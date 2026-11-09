# curl scripts

Quick checks from a terminal. Set your test key first:

```bash
export PLAXSWAP_API_KEY=pxs_test_...
```

| Script | What it does |
|---|---|
| `bash create-payment.sh 100 USD 1042` | Creates a payment for order 1042 and prints it. Open its `checkoutUrl`. |
| `bash get-payment.sh pay_...` | Prints the payment as it stands now. |
| `bash simulate.sh pay_... paid` | Test mode only: acts out an outcome and sends the webhook. |
| `bash list-coins.sh` | Lists the coins you can receive. |

Run `create-payment.sh` twice with the same order number: the second call returns the same payment, because the order number is used as the Idempotency-Key.
