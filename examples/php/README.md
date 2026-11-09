# PHP example

Plain PHP 7.4 or newer with the cURL extension. No framework.

| File | What it does |
|---|---|
| `index.php` | A demo product form. |
| `checkout.php` | Saves an order, creates a Plaxswap payment with an Idempotency-Key, stores `payment.id`, and redirects to `checkoutUrl`. |
| `webhook.php` | Checks `x-px-signature` on the raw body, skips repeated events, reads the payment back from the API, compares it with the order and marks it paid once. |
| `order.php` | The return page. It reads the payment from the API instead of trusting the browser. |
| `lib.php` | Settings, API calls, the signature check and a small locked file store. |

## Run it

```bash
export PLAXSWAP_API_KEY=pxs_test_...        # from Developers > API keys
export PLAXSWAP_WEBHOOK_SECRET=whsec_...    # from Developers > Webhooks
export SITE_URL=https://your-public-address # where Plaxswap can reach this server
php -S 0.0.0.0:3000 -t .
```

Set your callback URL in the merchant dashboard to `SITE_URL/webhook.php`, then open `SITE_URL/`.

On a normal host, set the same environment variables in your hosting panel or web server, and keep the `data` folder out of the public web root (or block it in your server config). Orders are stored in `data/orders.json` with a file lock so the example stays short. In production, use your database and do the "mark paid" step in one transaction.
