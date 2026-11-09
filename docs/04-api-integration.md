# 4. API integration

The payment gateway API is JSON over HTTPS at `https://plaxswap.com`. Call it from your server only.

- Coin amounts are decimal strings in coin units, such as `"99.5"`, never floats.
- Times are ISO 8601 in UTC.
- A coin on one network has an id such as `usdt-tron`, `usdc-base` or `btc`.

## Authentication

Send your secret key in the `Authorization` header:

```
Authorization: Bearer pxs_test_YOUR_KEY
```

The `x-api-key` header also works. Every answer carries an `x-request-id`; quote it when you write to support.

## Create a payment

`POST /api/v1/payments`

```bash
curl -s -X POST https://plaxswap.com/api/v1/payments \
  -H "Authorization: Bearer $PLAXSWAP_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order-1042" \
  -d '{
    "amount": "100",
    "currency": "USD",
    "receive": "usdt-tron",
    "orderId": "1042",
    "description": "2 x T-shirt",
    "returnUrl": "https://shop.example/orders/1042/thanks",
    "cancelUrl": "https://shop.example/cart"
  }'
```

| Field | Required | What it is |
|---|---|---|
| `amount` | yes | The price, as text: `"100"`, `"25.50"`. |
| `currency` | yes | A fiat code (`USD`, `EUR`, `INR` and others), converted when the payment is made, or a coin (`USDT`, `BTC`). USD prices count one to one for USDT, USDC and DAI. |
| `receive` | no | The coin you receive, such as `usdt-tron`. Default: the one saved on your account. |
| `orderId` | no | Your order number, shown to the payer and searchable with `?orderId=`. |
| `description` | no | Shown to the payer. |
| `returnUrl` | no | HTTPS address the payer goes to after paying. |
| `cancelUrl` | no | HTTPS address of the checkout's back link. |
| `expiresInMinutes` | no | 15 to 1440. Default 60. |
| `customerPaysFee` | no | `true`: the payer pays the platform fee on top. Accounts with a merchant balance always use `true`. |
| `metadata` | no | Up to 20 keys of your own, with text values. Sent back in every webhook. |
| `receiveAddress`, `receiveMemo` | no | Older direct-wallet accounts only. |

The answer, `201 Created`, is the payment:

```json
{
  "id": "pay_7m2k9q4x8c1v5b3n",
  "object": "payment",
  "livemode": false,
  "status": "pending",
  "amount": "100",
  "currency": "USD",
  "receive": { "id": "usdt-tron", "assetId": "USDT", "networkId": "tron", "label": "USDT · Tron (TRC-20)", "decimals": 6, "memoRequired": false },
  "receiveAmount": "100",
  "expectedAmount": "100",
  "receivedAmount": "0",
  "fee": { "bps": 150, "paidBy": "customer", "amount": "1.5" },
  "orderId": "1042",
  "checkoutUrl": "https://plaxswap.com/checkout/pay_7m2k9q4x8c1v5b3n",
  "expiresAt": "2026-10-20T11:00:00.000Z",
  "transactions": []
}
```

Store `id` on your order, then redirect the customer to `checkoutUrl`.

### Retries are safe with Idempotency-Key

Send an `Idempotency-Key` header on every create. The same key with the same body returns the same payment (`200` instead of `201`). The same key with a different body is refused with `409 idempotency_conflict`. A key per order means a double click or a timeout retry never asks the customer to pay twice.

Keys are shared by everything that uses your merchant account. If two sites use the same account, or your order numbers restart, put the site in the key, such as `shop.example-order-1042`, so two different orders never share one. The examples do this.

## Read a payment

`GET /api/v1/payments/{id}` returns the payment as it stands now. Use it:

- in your webhook handler, before you fulfil the order;
- on your return page, before you show "paid";
- in a scheduled job that checks orders still waiting, in case a webhook was missed.

`GET /api/v1/payments` lists your payments. Add `?orderId=1042` to find the ones for an order.

## Cancel a payment

`POST /api/v1/payments/{id}/cancel` cancels a payment nothing was paid to. If coins already arrived, or the payment is closed, the answer is `409 not_cancellable`.

## Coins you can receive

`GET /api/v1/gateway/coins` lists the coins you can receive and what payers can pay each one with. The payer can always pay with your own coin. Other coins work where Uniswap swaps them on the same network, or where SwapKit carries them between networks. The checkout only shows what can pay that payment at that moment, so you don't need to keep your own list.

## Errors

Every error is `{ "error": { "code", "message", "details"? } }` with a matching HTTP status. `details.field` names the field when there is one.

| Code | HTTP | Meaning |
|---|---|---|
| `invalid_api_key` | 401 | The key is missing, mistyped, or not a merchant key. |
| `key_disabled` | 401 | The key was switched off. |
| `merchant_disabled` | 403 | Your account is switched off. Write to support. |
| `invalid_amount` | 400 | `amount` is not a plain positive number. |
| `invalid_currency` | 400 | `currency` is not a fiat code or a coin Plaxswap knows. |
| `invalid_receive_coin` | 400 | `receive` is not a coin the gateway pays out in. `details.allowed` lists them. |
| `amount_out_of_range` | 400 | Below about 1 US dollar, or above the coin's limit. |
| `invalid_url` | 400 | `returnUrl` or `cancelUrl` is not an HTTPS address. |
| `invalid_expiry` | 400 | `expiresInMinutes` is outside 15 to 1440. |
| `invalid_metadata` | 400 | More than 20 keys, a bad key name, or a value over 500 characters. |
| `idempotency_conflict` | 409 | The Idempotency-Key was used before with a different body. |
| `not_found` | 404 | No such payment for this key. Test keys see only test payments. |
| `not_cancellable` | 409 | Coins arrived, or the payment is closed. |
| `rate_limited` | 429 | Too many requests with one key in a minute (limit 300). |
| `service_paused` | 503 | New payments are paused for a moment. Try again later. |
| `rate_unavailable` | 503 | No current price to convert your currency. Try again in a minute. |

On `429` and `503`, wait and retry with the same Idempotency-Key.

## Endpoints you will use

| Method | Path | What it does |
|---|---|---|
| POST | `/api/v1/payments` | Create a payment |
| GET | `/api/v1/payments/{id}` | A payment as it stands now |
| GET | `/api/v1/payments` | List your payments |
| POST | `/api/v1/payments/{id}/cancel` | Cancel a payment nothing was paid to |
| POST | `/api/v1/payments/{id}/simulate` | Test mode: act out an outcome |
| GET | `/api/v1/gateway/coins` | Coins you can receive |
| GET | `/api/v1/merchant` | Your merchant account |
| PATCH | `/api/v1/merchant` | Change account settings, such as the webhook URL |
| POST | `/api/v1/merchant/webhooks/test` | Send a signed `ping` webhook |
| POST | `/api/v1/merchant/webhook-secret` | Make a new webhook signing secret |

The full list, with every field of every request and answer, is in the [OpenAPI document](https://plaxswap.com/api/v1/openapi.json) and the [API documentation](https://plaxswap.com/developers/payments).

## Working code

- [Node.js and Express](../examples/node-express)
- [PHP](../examples/php)
- [Python and Flask](../examples/python-flask)
- [curl scripts](../examples/curl)

Next: [Webhooks](05-webhooks.md)
