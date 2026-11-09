# Examples

| Folder | Language | Run with |
|---|---|---|
| [node-express](node-express) | Node.js 18+ and Express | `npm install && npm start` |
| [php](php) | PHP 7.4+ with cURL | `php -S 0.0.0.0:3000 -t .` |
| [python-flask](python-flask) | Python 3.9+ and Flask | `flask --app app run --port 3000` |
| [curl](curl) | Shell and curl | `bash create-payment.sh 100 USD 1042` |

All three servers do the same three things, the same way:

1. Checkout saves an order, creates a payment with an `Idempotency-Key`, stores `payment.id`, and redirects to `checkoutUrl`.
2. The webhook handler checks `x-px-signature` on the raw body, skips repeated events, reads the payment back from the API, compares id, mode, amount, currency and order number, and marks the order paid once.
3. The return page reads the payment from the API instead of trusting the browser.

Each one reads the same environment variables:

| Variable | Required | What it is |
|---|---|---|
| `PLAXSWAP_API_KEY` | yes | `pxs_test_...` while testing, `pxs_live_...` in production |
| `PLAXSWAP_WEBHOOK_SECRET` | yes | `whsec_...` from Developers, Webhooks |
| `SITE_URL` | yes | The public address of your server, used for `returnUrl` and `cancelUrl` |
| `PLAXSWAP_RECEIVE` | no | The coin you receive, such as `usdt-tron`. Default: the one on your merchant account |
| `PLAXSWAP_API_BASE` | no | Default `https://plaxswap.com`. Change it only for the local test below |

## Test the examples without a network

[test/mock_api.py](test/mock_api.py) is a small local stand-in for the Plaxswap API. It is not Plaxswap: it only copies the calls the examples use, and it signs webhooks exactly as the real API does. [test/run_e2e.sh](test/run_e2e.sh) starts it, runs each example against it, and checks 12 things per example:

- checkout redirects to the checkout page;
- the return page shows "waiting" before payment;
- a `payment.paid` webhook on its own fulfils the order, exactly once;
- a repeated webhook changes nothing;
- a wrong signature and a 10-minute-old timestamp are refused with 400;
- partly paid, late, expired and overpaid payments each do the right thing.

From the repository root:

```bash
pip install flask requests
bash examples/test/run_e2e.sh            # all three
bash examples/test/run_e2e.sh php        # or one of: node php python
```

It needs ports 3101 to 3103 and 8099 free. When it passes, test once more against the real API with your test key before you go live: see [Testing](../docs/06-testing.md).
