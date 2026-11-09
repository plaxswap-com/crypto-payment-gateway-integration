# 5. Webhooks

When a payment changes, Plaxswap sends a `POST` to your callback URL with the whole payment in `data`. This is how your site learns that a payment was paid, even if the customer closed the browser.

## Set your callback URL

In the merchant dashboard, open **Developers**, then **Webhooks**. Enter the public HTTPS address of your handler, for example `https://shop.example/plaxswap-webhook`, in **Your shop's callback URL** and choose **Save**. Choose **Make a new secret** and copy the signing secret (`whsec_...`); it is shown only once. You can also set the URL with `PATCH /api/v1/merchant`.

The address must be reachable from the internet. A site on `localhost`, behind a login wall, in maintenance mode, or behind a firewall or bot challenge that blocks this path won't receive webhooks.

## Events

| Event | When |
|---|---|
| `payment.confirming` | Coins arrived and are being confirmed, checked or converted. |
| `payment.paid` | The payer sent the amount asked and it settled. |
| `payment.partially_paid` | Less than asked settled. The payer can still send the rest while the payment is open. |
| `payment.expired` | Nothing arrived in time. Late coins (up to 24 hours) are followed by `payment.paid` or `payment.partially_paid` with `late: true`. |
| `payment.cancelled` | You cancelled the payment. |
| `payment.failed` | The payer's coins were sent back. |
| `payment.updated` | A flag or the amount changed without a status change. |
| `ping` | A test from `POST /api/v1/merchant/webhooks/test` or the dashboard. |

## Body

```json
{
  "id": "evt_3k9q2m7x8c1v5b4n",
  "event": "payment.paid",
  "livemode": true,
  "createdAt": "2026-10-20T10:22:05.000Z",
  "data": { "id": "pay_7m2k9q4x8c1v5b3n", "object": "payment", "status": "paid", "orderId": "1042", "receivedAmount": "99.84" }
}
```

`data` holds the full payment, the same object `GET /api/v1/payments/{id}` returns.

## The signature

Each webhook has an `x-px-signature` header:

```
x-px-signature: t=1792491725,v1=5f1c...e9a0
```

- `t` is the time it was signed, in Unix seconds.
- `v1` is the hex HMAC-SHA256 of the text `t + "." + raw body`, keyed with your whole signing secret, `whsec_` included.

To check it:

1. Read the raw request body as bytes. Don't parse and re-encode the JSON first, or the bytes change.
2. Split the header on commas into `t` and every `v1` value.
3. Refuse it if `t` is more than 5 minutes away from your server's clock.
4. Compute `HMAC-SHA256(secret, t + "." + body)` as lowercase hex.
5. Compare it with each `v1` using a constant-time comparison. Accept if one matches.
6. Only then parse the JSON.

### Node.js

```js
import crypto from "node:crypto";

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
```

### PHP

```php
function plaxswap_verify_signature(string $rawBody, string $header, string $secret, int $tolerance = 300): bool {
    $t = null; $v1 = [];
    foreach (explode(',', $header) as $part) {
        $pair = explode('=', trim($part), 2);
        if (count($pair) !== 2) continue;
        if ($pair[0] === 't' && preg_match('/^\d{10}$/', $pair[1])) $t = $pair[1];
        if ($pair[0] === 'v1' && preg_match('/^[0-9a-f]{64}$/', $pair[1])) $v1[] = $pair[1];
    }
    if ($t === null || !$v1 || abs(time() - (int) $t) > $tolerance) return false;
    $expected = hash_hmac('sha256', $t . '.' . $rawBody, $secret);
    foreach ($v1 as $sig) { if (hash_equals($expected, $sig)) return true; }
    return false;
}
```

### Python

```python
import hashlib, hmac, re, time

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
```

All three run in the examples, and [examples/test/run_e2e.sh](../examples/test/run_e2e.sh) checks them with the same signed webhooks. See [examples/README.md](../examples/README.md).

## What to do after the signature passes

1. Skip repeats. Save the event `id`. If you have seen it, answer `200` and stop.
2. Check the mode. If `livemode` is `false` and your site is live, never fulfil a real order from it.
3. Find the order by the payment id you stored, not by `orderId` alone.
4. Read the payment back with `GET /api/v1/payments/{id}`. Act on that answer, not only on the webhook body.
5. Compare `status`, `livemode`, `amount`, `currency` and `orderId` with your order.
6. Fulfil once. Do the "mark paid" step in one database transaction or with a lock.
7. Answer fast. Return any `2xx` within 8 seconds. Do slow work, like sending emails, after you answer or in a queue.

## Retries

If your handler doesn't answer `2xx` within 8 seconds, delivery is retried with growing gaps, 10 times over about a day. That is why the same event can arrive more than once, and why step 1 matters. Past deliveries are listed on the dashboard's Webhooks page, where you can send one again. `POST /api/v1/merchant/webhooks/{id}/resend` does the same.

## Test your handler

- Choose **Send test** under Webhooks, or call `POST /api/v1/merchant/webhooks/test`. It sends a `ping` event, signed like a real one.
- In test mode, act out each outcome with `POST /api/v1/payments/{id}/simulate`. See [Testing](06-testing.md).

## Changing the secret

**Make a new secret** in the dashboard, or `POST /api/v1/merchant/webhook-secret`, makes a new secret. Every site that uses the old one must be updated. To switch without missing events, let your handler accept both secrets for a short time, then remove the old one.

Next: [Testing](06-testing.md)
