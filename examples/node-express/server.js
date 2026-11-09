// Plaxswap crypto payments: a small Express shop with checkout, webhook and return page.
// Run: npm install && node server.js   (Node.js 18 or newer)
// Orders live in memory here. Use your own database in production.

import crypto from "node:crypto";
import express from "express";

const API_BASE = (process.env.PLAXSWAP_API_BASE || "https://plaxswap.com").replace(/\/$/, "");
const API_KEY = process.env.PLAXSWAP_API_KEY || ""; // pxs_test_... or pxs_live_...
const WEBHOOK_SECRET = process.env.PLAXSWAP_WEBHOOK_SECRET || ""; // whsec_...
const SITE_URL = (process.env.SITE_URL || "http://localhost:3000").replace(/\/$/, "");
const RECEIVE = process.env.PLAXSWAP_RECEIVE || ""; // optional, such as usdt-tron
const PORT = Number(process.env.PORT || 3000);
// Idempotency keys are per merchant account: put the site in them so two shops never collide.
const SITE_KEY = new URL(SITE_URL).host;

if (!/^pxs_(test|live)_/.test(API_KEY)) throw new Error("Set PLAXSWAP_API_KEY to your pxs_test_ or pxs_live_ key");
if (!WEBHOOK_SECRET.startsWith("whsec_")) throw new Error("Set PLAXSWAP_WEBHOOK_SECRET to your whsec_ secret");
// A live key must never fulfil orders from test events, and the other way round.
const LIVE = API_KEY.startsWith("pxs_live_");

const orders = new Map(); // orderId -> order
const seenEvents = new Set(); // webhook event ids already handled

// ---------- Plaxswap API ----------

async function plaxswap(method, path, body, idempotencyKey) {
  const headers = { Authorization: `Bearer ${API_KEY}`, Accept: "application/json" };
  if (body) headers["Content-Type"] = "application/json";
  if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;
  const res = await fetch(API_BASE + path, { method, headers, body: body ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(15000) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data?.error?.message || `Plaxswap API error ${res.status}`);
    err.code = data?.error?.code;
    err.requestId = res.headers.get("x-request-id");
    throw err;
  }
  return data;
}

// ---------- Webhook signature ----------

function verifySignature(rawBody, header, secret, toleranceSeconds = 300) {
  let t = null;
  const v1 = [];
  for (const part of String(header || "").split(",")) {
    const [key, value] = part.trim().split("=", 2);
    if (key === "t" && /^\d{10}$/.test(value || "")) t = value;
    else if (key === "v1" && /^[0-9a-f]{64}$/.test(value || "")) v1.push(value);
  }
  if (!t || v1.length === 0) return false;
  if (Math.abs(Date.now() / 1000 - Number(t)) > toleranceSeconds) return false;
  const expected = crypto.createHmac("sha256", secret).update(`${t}.`).update(rawBody).digest("hex");
  return v1.some((sig) => crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected)));
}

// "25.50" and "25.5" are the same amount.
function sameAmount(a, b) {
  const norm = (s) => {
    const [i, f = ""] = String(s).trim().split(".");
    return `${i.replace(/^0+(?=\d)/, "")}.${f.replace(/0+$/, "")}`;
  };
  return norm(a) === norm(b);
}

// ---------- Order updates ----------

// Compare the payment read from the API with the order before changing anything.
function applyPayment(order, payment) {
  if (payment.id !== order.paymentId) return "wrong payment";
  if (payment.livemode !== LIVE) return "wrong mode";
  if (payment.orderId !== order.id) return "wrong order";
  if (payment.currency !== order.currency || !sameAmount(payment.amount, order.amount)) return "wrong amount";

  if (order.status === "paid") return "already paid";
  if (payment.status === "paid" && payment.late) {
    order.status = "needs_review"; // coins came after expiry: check before you ship
  } else if (payment.status === "paid") {
    // JavaScript runs this block without interruption, so it can only happen once.
    // With a database, do the same in one transaction: UPDATE ... WHERE status != 'paid'.
    order.status = "paid";
    order.fulfilCount += 1;
    order.note = payment.overpaid ? "Overpaid: review the extra" : "";
    console.log(`Fulfilled order ${order.id} (payment ${payment.id})`);
  } else if (["partially_paid", "expired", "failed", "cancelled", "confirming"].includes(payment.status)) {
    order.status = payment.status;
  }
  return "ok";
}

// ---------- Web app ----------

const app = express();

app.get("/", (req, res) => {
  res.type("html").send(`<!doctype html><title>Demo shop</title>
<h1>Demo shop</h1>
<form method="post" action="/checkout">
  <label>Price in USD <input name="amount" value="25.50"></label>
  <button>Pay with crypto</button>
</form>`);
});

app.post("/checkout", express.urlencoded({ extended: false }), async (req, res) => {
  const amount = String(req.body.amount || "").trim();
  if (!/^\d+(\.\d{1,2})?$/.test(amount)) return res.status(400).send("Enter a price such as 25.50");

  const order = { id: String(1000 + orders.size + 1), amount, currency: "USD", status: "awaiting_payment", paymentId: null, fulfilCount: 0, note: "" };
  orders.set(order.id, order);

  try {
    const payment = await plaxswap("POST", "/api/v1/payments", {
      amount: order.amount,
      currency: order.currency,
      ...(RECEIVE ? { receive: RECEIVE } : {}),
      orderId: order.id,
      description: `Order ${order.id}`,
      returnUrl: `${SITE_URL}/orders/${order.id}`,
      cancelUrl: `${SITE_URL}/`,
    }, `${SITE_KEY}-order-${order.id}`);
    order.paymentId = payment.id; // match webhooks on this, never on a value from the browser
    res.redirect(303, payment.checkoutUrl);
  } catch (err) {
    console.error("Create payment failed:", err.message, err.code || "", err.requestId || "");
    res.status(502).send("Could not start the payment. Please try again.");
  }
});

// The raw body is needed for the signature check, so no JSON parser here.
app.post("/plaxswap-webhook", express.raw({ type: "*/*", limit: "256kb" }), async (req, res) => {
  if (!verifySignature(req.body, req.get("x-px-signature"), WEBHOOK_SECRET)) return res.sendStatus(400);

  let event;
  try { event = JSON.parse(req.body.toString("utf8")); } catch { return res.sendStatus(400); }
  if (event.event === "ping") return res.sendStatus(200);
  if (seenEvents.has(event.id)) return res.sendStatus(200); // a repeat delivery
  if (event.livemode !== LIVE) return res.sendStatus(200); // test events never touch live orders

  const order = [...orders.values()].find((o) => o.paymentId === event.data?.id);
  if (!order) return res.sendStatus(200); // not one of ours, or already removed

  try {
    // Don't act on the webhook body alone: read the payment from the API.
    const payment = await plaxswap("GET", `/api/v1/payments/${encodeURIComponent(order.paymentId)}`);
    const result = applyPayment(order, payment);
    if (result !== "ok" && result !== "already paid") console.warn(`Order ${order.id}: ${result}`);
    seenEvents.add(event.id);
    res.sendStatus(200);
  } catch (err) {
    console.error("Webhook check failed:", err.message);
    res.sendStatus(500); // Plaxswap retries later
  }
});

app.get("/orders/:id", async (req, res) => {
  const order = orders.get(req.params.id);
  if (!order) return res.status(404).send("No such order");
  // The customer coming back proves nothing. Ask the API.
  if (order.paymentId && !["paid", "needs_review"].includes(order.status)) {
    try { applyPayment(order, await plaxswap("GET", `/api/v1/payments/${encodeURIComponent(order.paymentId)}`)); } catch { /* show what we have */ }
  }
  const text = {
    awaiting_payment: "Waiting for your payment.",
    pending: "Waiting for your payment.",
    confirming: "Payment received, confirming on the network.",
    paid: "Paid. Thank you.",
    needs_review: "Payment received late. We will check it and email you.",
    partially_paid: "Part of the amount arrived. Please send the rest from the payment page.",
    expired: "This payment expired.",
    failed: "The payment did not go through.",
    cancelled: "This payment was cancelled.",
  }[order.status] || order.status;
  res.type("html").send(`<!doctype html><title>Order ${order.id}</title>
<h1>Order ${order.id}</h1><p>${text}</p>
<p>Status: <code>${order.status}</code>. Fulfilled ${order.fulfilCount} time(s). ${order.note}</p>`);
});

app.listen(PORT, () => console.log(`Demo shop on ${SITE_URL} (port ${PORT}), ${LIVE ? "LIVE" : "test"} mode, API ${API_BASE}`));
