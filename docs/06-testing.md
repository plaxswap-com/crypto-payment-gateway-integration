# 6. Testing

Payments made with a test key (`pxs_test_...`) never move real coins. Build and test your whole flow with one before you switch to a live key.

## What test mode does

- The checkout shows a test banner, a pretend address, and buttons that act out each outcome.
- Webhooks are sent exactly as for a live payment, with `"livemode": false` and the header `x-px-livemode: false`.
- A test key sees only test payments. A live key sees only live ones.
- One test payment takes one outcome. Make a new payment to try the next.

## Act out an outcome from your server

```bash
curl -s -X POST https://plaxswap.com/api/v1/payments/pay_7m2k9q4x8c1v5b3n/simulate \
  -H "Authorization: Bearer $PLAXSWAP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "outcome": "paid" }'
```

Outcomes: `paid`, `partially_paid`, `overpaid`, `late`, `expired`, `failed`.

The script [examples/curl/simulate.sh](../examples/curl/simulate.sh) does this for you.

## Test plan

Run each of these with a fresh test payment and check what your site does.

| Test | Expected result on your site |
|---|---|
| `paid` | Order marked paid once. Stock and emails run once. |
| The same `payment.paid` delivered twice (resend it from the dashboard) | Nothing happens the second time. |
| `partially_paid` | Order stays unpaid. Customer or staff is told. |
| `overpaid` | Order paid. The extra is flagged for review. |
| `expired` | Order not fulfilled, but not deleted. |
| `late` | Order flagged for review before you fulfil. |
| `failed` | Order marked failed. |
| Webhook with a wrong signature | Handler answers 400 and changes nothing. |
| Webhook with a timestamp over 5 minutes old | Handler answers 400. |
| Customer returns before the webhook | Return page reads the payment from the API and shows "waiting". |
| Double click on "Pay" | Same payment comes back (Idempotency-Key). |
| **Send test** under Webhooks | Shows as Delivered. |

## Test webhooks on your own computer

Plaxswap can't reach `localhost`. While you build, either:

- deploy to a test server with a public HTTPS address, or
- put a tunnel in front of your local server and use its HTTPS address as the callback URL. Remove it when you finish.

The [examples](../examples) also include a local test that signs webhooks with a test secret, so you can check your signature code without any network.

Next: [Go-live checklist](07-go-live-checklist.md)
