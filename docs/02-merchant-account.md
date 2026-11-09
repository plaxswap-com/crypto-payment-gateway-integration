# 2. Merchant account and keys

Plugins and the API both need a Plaxswap merchant account. This page covers opening it, the three secrets you get, and where your money goes.

## Open the account

1. Go to [plaxswap.com/merchants](https://plaxswap.com/merchants) and choose **Open merchant account**.
2. Sign in with Google or Telegram.
3. Fill in your business profile.
4. Turn on an authenticator app. Sensitive actions, such as withdrawals and new keys, ask for its code or a passkey.

Plaxswap can ask for business details, and can pause withdrawals until they are approved.

## Your keys and secret

| Secret | Starts with | What it does | Where it goes |
|---|---|---|---|
| Test API key | `pxs_test_` | Creates test payments. No real coins move. | Your server, while you build |
| Live API key | `pxs_live_` | Creates real payments | Your server, when you go live |
| Webhook signing secret | `whsec_` | Proves a webhook came from Plaxswap | Your server, next to the key |

In the merchant dashboard, open **Developers**:

- Under **API keys**, make a new key. Pick **Test payments** or **Live payments**, and name it after the site that uses it.
- Under **Webhooks**, enter your callback URL (the address of your webhook handler) in **Your shop's callback URL** and choose **Save**. Then choose **Make a new secret** and copy the signing secret.
- Choose **Send test** and check that the delivery shows as Delivered.

Creating keys and secrets asks for your authenticator code.

Each secret is shown once. Save it on your server straight away, in an environment variable or a secrets store, never in a web page, app or public repository.

A swap partner key (`pxk_...`) is a different product and does not work for payments.

You can have more than one key. Switch one off from the dashboard, or with `PATCH /api/v1/merchant/keys/{id}`, if it leaks. Each key can make 300 requests a minute.

## Test and live are separate worlds

- A test key only sees test payments, and a live key only live ones.
- Webhooks for test payments carry `"livemode": false` and the header `x-px-livemode: false`.
- Your code should refuse to fulfil a real order from a test payment. The [examples](../examples) do this.

## Where the money goes

Confirmed payments are added to your **Plaxswap merchant balance**, in the coin and network you receive. Plaxswap holds them until you withdraw to your own wallet.

| Action | Cost |
|---|---|
| Customer pays | 1.5% platform fee, paid by the customer and shown at checkout |
| You withdraw | 0.3% plus the network fee, both shown before you approve |
| You swap inside your balance | 0.3% same network, 0.5% same coin on another network, 0.7% another coin, plus the network fee |

Withdrawal rules worth knowing early:

- Withdrawals go only to addresses in your address book. A new address can be used 24 hours after you add it.
- A first withdrawal of $500 or more to an address is reviewed by the Plaxswap team.
- Sends pause for 24 hours after a security change or a sign-in from a new device.
- Every withdrawal needs your authenticator code or a passkey.

Older accounts made before the merchant balance (direct-wallet accounts) are paid straight to an address set on each payment. Every new account uses the merchant balance.

Next: [Payment workflow](03-payment-workflow.md)
