# 10. Troubleshooting

| What you see | What to check |
|---|---|
| `401 invalid_api_key` | Copy the whole key. Use a `pxs_test_` or `pxs_live_` merchant key, not a swap partner key (`pxk_`) or a Google or Telegram login id. |
| `401 key_disabled` | The key was switched off. Switch it on in the dashboard or use another key. |
| `400 invalid_receive_coin` | The coin isn't one the gateway pays out in. `details.allowed` lists the ones that are. |
| `400 amount_out_of_range` | The payment is under about 1 US dollar or above that coin's limit. |
| `400 invalid_url` | `returnUrl` and `cancelUrl` must start with `https://`. |
| `409 idempotency_conflict` | You reused an Idempotency-Key with a different body. Use one key per order, put your site in it if several sites share the account, and don't change the order's price after creating the payment. |
| `404 not_found` on a payment you just made | A test key can't see live payments, and the other way round. |
| `429 rate_limited` | More than 300 requests a minute on one key. Wait, then retry. |
| `503 service_paused` or `rate_unavailable` | Try again in a minute with the same Idempotency-Key. |
| Webhooks never arrive | The callback URL must be public HTTPS. Check for a login wall, maintenance mode, firewall or bot challenge on that path. Choose **Send test** under Developers, Webhooks and look at the delivery result. |
| Signature never matches | Use the raw body bytes, not re-encoded JSON. Use the whole secret, `whsec_` included, from the same merchant account as the key. Check your server clock. |
| The same order was shipped twice | Record event ids and fulfil inside a transaction or lock. See [Webhooks](05-webhooks.md). |
| The customer came back but the order is unpaid | Coming back doesn't prove payment. Wait for the webhook, or read the payment from the API. |
| Payment stuck on `confirming` | Coins are being confirmed or converted. Open the payment's checkout page to see its confirmations. Don't ship until `paid`. |
| Payment `partially_paid` | The customer sent too little. They can send the rest while it's open. Otherwise review it by hand. |
| Coins arrived after the order expired | They are passed on with `late: true` for up to 24 hours. Review before you fulfil. |
| Customer sent coins on the wrong network | Coins sent on the wrong network usually can't be recovered. Contact support with the transaction id. |

## Getting help

Write to [support](https://plaxswap.com/support) with:

- the payment id (`pay_...`) and your order number;
- the `x-request-id` from the API answer, if there was an error;
- your plugin and platform version, if you use a plugin.

Never send an API key, signing secret, recovery phrase or authenticator code.

Back to the [start](../README.md)
