# 7. Go-live checklist

Tick every line before you put a live key on your server.

## Account

- [ ] Business profile complete and authenticator on.
- [ ] The coin and network you receive is set on your merchant page, or named in `receive`.
- [ ] Your business is allowed under the [merchant terms](https://plaxswap.com/legal/merchant-terms).
- [ ] You know which countries can't pay: [supported countries](https://plaxswap.com/help/supported-countries).

## Your server

- [ ] The API key and signing secret live only on the server, in environment variables or a secrets store.
- [ ] Every create call sends an `Idempotency-Key` per order, unique across all sites on the account (for example `shop.example-order-1042`).
- [ ] `payment.id` is stored on each order.
- [ ] The site is served over HTTPS, and `returnUrl` and `cancelUrl` are HTTPS.

## Webhook handler

- [ ] Checks `x-px-signature` on the raw body, with a 5-minute window.
- [ ] Skips event ids it has already seen.
- [ ] Finds the order by the stored `payment.id`.
- [ ] Reads the payment back with `GET /api/v1/payments/{id}` before fulfilling.
- [ ] Compares status, mode, amount, currency and order number.
- [ ] Fulfils once, inside a transaction or lock.
- [ ] Answers `2xx` within 8 seconds.
- [ ] Refuses to fulfil a live order from a test event.
- [ ] Reachable from the internet: no login wall, maintenance page or bot challenge on that path.

## Return page and fallbacks

- [ ] The return page reads the payment from your server, never from the URL alone.
- [ ] A scheduled job re-checks orders still waiting, in case a webhook was missed.

## Tested in test mode

- [ ] `paid`, `partially_paid`, `overpaid`, `late`, `expired` and `failed` each do the right thing.
- [ ] A repeated webhook does nothing the second time.
- [ ] A bad signature is refused.
- [ ] **Send test** under Webhooks shows Delivered.

## Switch to live

1. Create a live key in the same merchant account (`pxs_live_...`).
2. Replace the test key on your server. Keep the same signing secret, from the same account.
3. Make one small real payment and follow it to your merchant balance.
4. Tell your customers how you handle refunds. A crypto payment can't be pulled back, so any refund is yours to send.

Next: [Amounts, fees and coins](08-amounts-fees-coins.md)
