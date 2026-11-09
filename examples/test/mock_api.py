"""A tiny local stand-in for the Plaxswap payment API, for testing the examples without a network.

It is NOT Plaxswap. It copies only what the examples use: create a payment (with Idempotency-Key),
read a payment, and act out an outcome that sends a webhook signed the same way as the real one:
x-px-signature: t=<unix seconds>,v1=<hex HMAC-SHA256 of "t.body" keyed with the whole whsec_ secret>.

Run: python3 mock_api.py   (listens on 127.0.0.1:8099)
Test-only extras: POST /mock/config {"webhookUrl", "secret"} and POST /mock/resend-last.
"""
import hashlib
import hmac
import json
import os
import secrets
import string
import time
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("MOCK_PORT", "8099"))
STATE = {"payments": {}, "idem": {}, "webhookUrl": None, "secret": None, "last": None}
ALPHABET = string.ascii_lowercase + string.digits


def new_id(prefix):
    return prefix + "".join(secrets.choice(ALPHABET) for _ in range(16))


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def send_webhook(event_name, payment):
    if not STATE["webhookUrl"] or not STATE["secret"]:
        return None
    body = json.dumps({"id": new_id("evt_"), "event": event_name, "livemode": payment["livemode"],
                       "createdAt": now_iso(), "data": payment}).encode()
    STATE["last"] = body
    return deliver(body)


def deliver(body, secret=None, timestamp=None):
    t = str(timestamp or int(time.time()))
    sig = hmac.new((secret or STATE["secret"]).encode(), t.encode() + b"." + body, hashlib.sha256).hexdigest()
    req = urllib.request.Request(STATE["webhookUrl"], data=body, method="POST", headers={
        "Content-Type": "application/json", "x-px-signature": f"t={t},v1={sig}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, obj):
        data = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("x-request-id", new_id("req_"))
        self.end_headers()
        self.wfile.write(data)

    def error(self, status, code, message):
        self.reply(status, {"error": {"code": code, "message": message}})

    def key_mode(self):
        auth = self.headers.get("Authorization", "")
        key = auth[7:] if auth.startswith("Bearer ") else self.headers.get("x-api-key", "")
        if key.startswith("pxs_live_"):
            return True
        if key.startswith("pxs_test_"):
            return False
        return None

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        return raw, (json.loads(raw) if raw else {})

    def do_GET(self):
        live = self.key_mode()
        if self.path.startswith("/api/v1/payments/"):
            if live is None:
                return self.error(401, "invalid_api_key", "The key is missing or not a merchant key.")
            p = STATE["payments"].get(self.path.rsplit("/", 1)[1])
            if not p or p["livemode"] != live:
                return self.error(404, "not_found", "No such payment for this key.")
            return self.reply(200, p)
        self.error(404, "not_found", "Not found")

    def do_POST(self):
        raw, data = self.body()
        if self.path == "/mock/config":
            STATE["webhookUrl"], STATE["secret"] = data.get("webhookUrl"), data.get("secret")
            return self.reply(200, {"ok": True})
        if self.path == "/mock/resend-last":
            return self.reply(200, {"status": deliver(STATE["last"])})
        if self.path == "/mock/send-raw":
            # Sends the last body with a chosen secret or timestamp, to test refusals.
            return self.reply(200, {"status": deliver(STATE["last"], data.get("secret"), data.get("timestamp"))})

        live = self.key_mode()
        if live is None:
            return self.error(401, "invalid_api_key", "The key is missing or not a merchant key.")
        if self.path == "/api/v1/payments":
            idem = self.headers.get("Idempotency-Key")
            if idem and idem in STATE["idem"]:
                prev_raw, pid = STATE["idem"][idem]
                if prev_raw != raw:
                    return self.error(409, "idempotency_conflict", "The Idempotency-Key was used before with a different body.")
                return self.reply(200, STATE["payments"][pid])
            amount = str(data.get("amount", ""))
            try:
                if float(amount) <= 0:
                    raise ValueError
            except ValueError:
                return self.error(400, "invalid_amount", "amount is not a plain positive number.")
            pid = new_id("pay_")
            p = {"id": pid, "object": "payment", "livemode": live, "status": "pending", "amount": amount,
                 "currency": data.get("currency"), "receive": {"id": data.get("receive") or "usdt-tron"},
                 "receiveAmount": amount, "expectedAmount": amount, "receivedAmount": "0",
                 "fee": {"bps": 150, "paidBy": "customer", "amount": f"{float(amount) * 0.015:.2f}"},
                 "orderId": data.get("orderId"), "checkoutUrl": f"http://127.0.0.1:{PORT}/checkout/{pid}",
                 "expiresAt": now_iso(), "transactions": [], "late": False, "overpaid": False, "underReview": False,
                 "metadata": data.get("metadata") or {}}
            STATE["payments"][pid] = p
            if idem:
                STATE["idem"][idem] = (raw, pid)
            return self.reply(201, p)
        if self.path.startswith("/api/v1/payments/") and self.path.endswith("/simulate"):
            pid = self.path.split("/")[4]
            p = STATE["payments"].get(pid)
            if not p or p["livemode"] != live:
                return self.error(404, "not_found", "No such payment for this key.")
            if live:
                return self.error(400, "test_only", "Simulate works with test keys only.")
            outcome = data.get("outcome")
            status_map = {"paid": "paid", "partially_paid": "partially_paid", "overpaid": "paid",
                          "late": "paid", "expired": "expired", "failed": "failed"}
            if outcome not in status_map:
                return self.error(400, "invalid_outcome", "Unknown outcome.")
            p["status"] = status_map[outcome]
            p["overpaid"] = outcome == "overpaid"
            p["late"] = outcome == "late"
            p["receivedAmount"] = p["amount"] if p["status"] == "paid" else "0"
            self.reply(200, p)
            send_webhook("payment." + p["status"], p)
            return None
        self.error(404, "not_found", "Not found")


if __name__ == "__main__":
    print(f"Mock Plaxswap API on http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
