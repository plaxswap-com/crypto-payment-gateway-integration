# Node.js and Express example

A small shop with three routes:

| Route | What it does |
|---|---|
| `POST /checkout` | Saves an order, creates a Plaxswap payment with an Idempotency-Key, stores `payment.id`, and redirects to `checkoutUrl`. |
| `POST /plaxswap-webhook` | Checks `x-px-signature` on the raw body, skips repeated events, reads the payment back from the API, compares it with the order and marks it paid once. |
| `GET /orders/:id` | The return page. It reads the payment from the API instead of trusting the browser. |

## Run it

Needs Node.js 18 or newer.

```bash
npm install
export PLAXSWAP_API_KEY=pxs_test_...        # from Developers > API keys
export PLAXSWAP_WEBHOOK_SECRET=whsec_...    # from Developers > Webhooks
export SITE_URL=https://your-public-address # where Plaxswap can reach this server
npm start
```

Set your callback URL in the merchant dashboard to `SITE_URL/plaxswap-webhook`, then open `SITE_URL/` and pay with a test checkout.

Orders are kept in memory so the example stays short. In production, store orders and handled event ids in your database, and do the "mark paid" step in one transaction.

Read [Webhooks](../../docs/05-webhooks.md) for why each check is there.
