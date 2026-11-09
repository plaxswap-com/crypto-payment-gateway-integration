# Python and Flask example

Python 3.9 or newer, Flask and requests. Orders are kept in SQLite (`shop.db`), and the "mark paid" step runs in a transaction so two webhooks at once can't fulfil an order twice.

| Route | What it does |
|---|---|
| `POST /checkout` | Saves an order, creates a Plaxswap payment with an Idempotency-Key, stores `payment.id`, and redirects to `checkoutUrl`. |
| `POST /plaxswap-webhook` | Checks `x-px-signature` on the raw body, skips repeated events, reads the payment back from the API, compares it with the order and marks it paid once. |
| `GET /orders/<id>` | The return page. It reads the payment from the API instead of trusting the browser. |

## Run it

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export PLAXSWAP_API_KEY=pxs_test_...        # from Developers > API keys
export PLAXSWAP_WEBHOOK_SECRET=whsec_...    # from Developers > Webhooks
export SITE_URL=https://your-public-address # where Plaxswap can reach this server
flask --app app run --host 0.0.0.0 --port 3000
```

Set your callback URL in the merchant dashboard to `SITE_URL/plaxswap-webhook`, then open `SITE_URL/`.

For production, run it behind a real WSGI server such as gunicorn, over HTTPS.
