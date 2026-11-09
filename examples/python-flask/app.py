"""Plaxswap crypto payments: a small Flask shop with checkout, webhook and return page.

Run:  pip install -r requirements.txt && flask --app app run --port 3000
Orders are stored in SQLite (shop.db) so "mark paid" runs in a real transaction.
"""
import hashlib
import hmac
import html
import json
import os
import re
import sqlite3
import time

import requests
from flask import Flask, abort, redirect, request

API_BASE = os.environ.get("PLAXSWAP_API_BASE", "https://plaxswap.com").rstrip("/")
API_KEY = os.environ.get("PLAXSWAP_API_KEY", "")  # pxs_test_... or pxs_live_...
WEBHOOK_SECRET = os.environ.get("PLAXSWAP_WEBHOOK_SECRET", "")  # whsec_...
SITE_URL = os.environ.get("SITE_URL", "http://localhost:3000").rstrip("/")
RECEIVE = os.environ.get("PLAXSWAP_RECEIVE", "")  # optional, such as usdt-tron
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "shop.db"))

if not re.match(r"^pxs_(test|live)_", API_KEY):
    raise SystemExit("Set PLAXSWAP_API_KEY to your pxs_test_ or pxs_live_ key")
if not WEBHOOK_SECRET.startswith("whsec_"):
    raise SystemExit("Set PLAXSWAP_WEBHOOK_SECRET to your whsec_ secret")
# A live key must never fulfil orders from test events, and the other way round.
LIVE = API_KEY.startswith("pxs_live_")
# Idempotency keys are per merchant account: put the site in them so two shops never collide.
SITE_KEY = SITE_URL.split("://", 1)[-1].split("/", 1)[0]

app = Flask(__name__)


# ---------- Storage ----------

def db():
    conn = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, amount TEXT NOT NULL, currency TEXT NOT NULL,
        status TEXT NOT NULL, payment_id TEXT UNIQUE, fulfil_count INTEGER NOT NULL DEFAULT 0, note TEXT NOT NULL DEFAULT '')""")
    conn.execute("CREATE TABLE IF NOT EXISTS webhook_events (id TEXT PRIMARY KEY, received_at INTEGER NOT NULL)")
    return conn


# ---------- Plaxswap API ----------

class PlaxswapError(Exception):
    pass


def plaxswap(method, path, body=None, idempotency_key=None):
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    r = requests.request(method, API_BASE + path, json=body, headers=headers, timeout=15)
    try:
        data = r.json()
    except ValueError:
        data = {}
    if not r.ok:
        raise PlaxswapError((data.get("error") or {}).get("message") or f"Plaxswap API error {r.status_code}")
    return data


# ---------- Webhook signature ----------

def verify_signature(raw_body: bytes, header: str, secret: str, tolerance: int = 300) -> bool:
    t, v1 = None, []
    for part in (header or "").split(","):
        key, _, value = part.strip().partition("=")
        if key == "t" and re.fullmatch(r"\d{10}", value):
            t = value
        elif key == "v1" and re.fullmatch(r"[0-9a-f]{64}", value):
            v1.append(value)
    if t is None or not v1 or abs(time.time() - int(t)) > tolerance:
        return False
    expected = hmac.new(secret.encode(), t.encode() + b"." + raw_body, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, sig) for sig in v1)


def same_amount(a, b):
    """'25.50' and '25.5' are the same amount."""
    def norm(s):
        whole, _, frac = str(s).strip().partition(".")
        return (whole.lstrip("0") or "0") + "." + frac.rstrip("0")
    return norm(a) == norm(b)


# ---------- Order updates ----------

def apply_payment(conn, order, payment):
    """Compare the payment read from the API with the order, then update it in one transaction."""
    if payment.get("id") != order["payment_id"]:
        return "wrong payment"
    if payment.get("livemode") is not LIVE:
        return "wrong mode"
    if str(payment.get("orderId")) != str(order["id"]):
        return "wrong order"
    if payment.get("currency") != order["currency"] or not same_amount(payment.get("amount", ""), order["amount"]):
        return "wrong amount"

    status = payment.get("status")
    conn.execute("BEGIN IMMEDIATE")  # one writer at a time: two webhooks can't both fulfil
    try:
        current = conn.execute("SELECT status FROM orders WHERE id = ?", (order["id"],)).fetchone()["status"]
        if current == "paid":
            conn.execute("COMMIT")
            return "already paid"
        if status == "paid" and payment.get("late"):
            conn.execute("UPDATE orders SET status = 'needs_review' WHERE id = ?", (order["id"],))
        elif status == "paid":
            note = "Overpaid: review the extra" if payment.get("overpaid") else ""
            conn.execute("UPDATE orders SET status = 'paid', fulfil_count = fulfil_count + 1, note = ? WHERE id = ?", (note, order["id"]))
            print(f"Fulfilled order {order['id']} (payment {payment['id']})", flush=True)
        elif status in ("partially_paid", "expired", "failed", "cancelled", "confirming"):
            conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order["id"]))
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return "ok"


# ---------- Routes ----------

@app.get("/")
def index():
    return """<!doctype html><title>Demo shop</title><h1>Demo shop</h1>
<form method="post" action="/checkout"><label>Price in USD <input name="amount" value="25.50"></label>
<button>Pay with crypto</button></form>"""


@app.post("/checkout")
def checkout():
    amount = (request.form.get("amount") or "").strip()
    if not re.fullmatch(r"\d+(\.\d{1,2})?", amount):
        return "Enter a price such as 25.50", 400
    conn = db()
    order_id = conn.execute("INSERT INTO orders (amount, currency, status) VALUES (?, 'USD', 'awaiting_payment')", (amount,)).lastrowid
    body = {
        "amount": amount,
        "currency": "USD",
        "orderId": str(order_id),
        "description": f"Order {order_id}",
        "returnUrl": f"{SITE_URL}/orders/{order_id}",
        "cancelUrl": f"{SITE_URL}/",
    }
    if RECEIVE:
        body["receive"] = RECEIVE
    try:
        # One Idempotency-Key per order: a retry or double click returns the same payment.
        payment = plaxswap("POST", "/api/v1/payments", body, idempotency_key=f"{SITE_KEY}-order-{order_id}")
    except (PlaxswapError, requests.RequestException) as e:
        app.logger.error("Create payment failed: %s", e)
        return "Could not start the payment. Please try again.", 502
    # Match webhooks on this id, never on a value from the browser.
    conn.execute("UPDATE orders SET payment_id = ? WHERE id = ?", (payment["id"], order_id))
    return redirect(payment["checkoutUrl"], code=303)


@app.post("/plaxswap-webhook")
def webhook():
    raw = request.get_data(cache=False)
    if len(raw) > 262144 or not verify_signature(raw, request.headers.get("x-px-signature", ""), WEBHOOK_SECRET):
        abort(400)
    try:
        event = json.loads(raw)
    except ValueError:
        abort(400)
    if event.get("event") == "ping":
        return "", 200
    if event.get("livemode") is not LIVE:
        return "", 200  # test events never touch live orders

    conn = db()
    if conn.execute("SELECT 1 FROM webhook_events WHERE id = ?", (event.get("id"),)).fetchone():
        return "", 200  # a repeat delivery
    order = conn.execute("SELECT * FROM orders WHERE payment_id = ?", ((event.get("data") or {}).get("id"),)).fetchone()
    if order is None:
        return "", 200

    try:
        # Don't act on the webhook body alone: read the payment from the API.
        payment = plaxswap("GET", f"/api/v1/payments/{order['payment_id']}")
    except (PlaxswapError, requests.RequestException) as e:
        app.logger.error("Webhook check failed: %s", e)
        return "", 500  # Plaxswap retries later

    result = apply_payment(conn, order, payment)
    if result not in ("ok", "already paid"):
        app.logger.warning("Order %s: %s", order["id"], result)
    conn.execute("INSERT OR IGNORE INTO webhook_events (id, received_at) VALUES (?, ?)", (event["id"], int(time.time())))
    return "", 200


TEXTS = {
    "awaiting_payment": "Waiting for your payment.",
    "pending": "Waiting for your payment.",
    "confirming": "Payment received, confirming on the network.",
    "paid": "Paid. Thank you.",
    "needs_review": "Payment received late. We will check it and email you.",
    "partially_paid": "Part of the amount arrived. Please send the rest from the payment page.",
    "expired": "This payment expired.",
    "failed": "The payment did not go through.",
    "cancelled": "This payment was cancelled.",
}


@app.get("/orders/<int:order_id>")
def order_page(order_id):
    conn = db()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if order is None:
        abort(404)
    # The customer coming back proves nothing. Ask the API.
    if order["payment_id"] and order["status"] not in ("paid", "needs_review"):
        try:
            apply_payment(conn, order, plaxswap("GET", f"/api/v1/payments/{order['payment_id']}"))
            order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        except (PlaxswapError, requests.RequestException):
            pass
    e = html.escape
    return (f"<!doctype html><title>Order {order['id']}</title><h1>Order {order['id']}</h1>"
            f"<p>{e(TEXTS.get(order['status'], order['status']))}</p>"
            f"<p>Status: <code>{e(order['status'])}</code>. Fulfilled {order['fulfil_count']} time(s). {e(order['note'])}</p>")
