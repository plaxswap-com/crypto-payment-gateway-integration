# WooCommerce

Plaxswap Crypto Payments for WooCommerce is a free plugin on [WordPress.org](https://wordpress.org/plugins/plaxswap-crypto-payments/). Your customer pays on the hosted checkout, and WooCommerce marks the order paid once the plugin has verified the payment. Source: [plaxswap-com/plaxswap-crypto-payments](https://github.com/plaxswap-com/plaxswap-crypto-payments).

## Requirements

- WordPress 6.8 and WooCommerce 9.0 or newer.
- PHP 7.4 or newer with OpenSSL.
- HTTPS on the live store, outbound HTTPS to plaxswap.com, and a public address for webhooks.
- Working WordPress scheduled tasks (WP-Cron or a real cron).
- A Plaxswap [merchant account](../02-merchant-account.md).

Works with the Checkout Block and the classic checkout, and supports High-Performance Order Storage.

## Install and connect

1. Open a merchant account, finish the business setup and turn on your authenticator.
2. In WordPress, open **Plugins**, then **Add New Plugin**. Search for "Plaxswap Crypto Payments", install it and activate it. WooCommerce must be active.
3. Open **WooCommerce**, then **Settings**, **Payments** and **Plaxswap**.
4. In your merchant dashboard, open **Developers**, then **API keys**, and create a test key. It starts with `pxs_test_`. Paste it into **Merchant API key**.
5. Copy the callback URL the plugin shows. In the dashboard, open **Developers**, then **Webhooks**, paste that exact address into **Your shop's callback URL** and choose **Save**. Choose **Make a new secret** and copy it (`whsec_...`) into **Webhook signing secret**.
6. Tick **Show at checkout**, leave **Test mode** on, and choose **Save changes**. Saving checks your key and account. Nothing changes if they don't match.
7. Choose **Send test** under Webhooks in the dashboard and check that it shows **Delivered**.

## Test

While signed in as a store admin or shop manager, place a test order. Other visitors don't see the option in test mode. On the test checkout, act out a paid payment, then an expired one, and check what the order does.

## Go live

Create a live key (`pxs_live_...`), paste it in, turn off **Test mode** and save.

## What happens to an order

The plugin never trusts a customer returning to your store, or a notification on its own. A signed webhook makes it ask the API about the payment, and it checks the payment id, mode, amount, currency and order reference before it changes the order.

| Payment | Order status |
|---|---|
| Waiting for the customer | On hold |
| Seen on the network, confirming | On hold, with a note |
| Part of the amount arrived | On hold. The customer can pay the rest from the payment page. |
| Paid and verified | Paid, normally Processing |
| Expired or failed | Failed |
| Cancelled before payment | Cancelled |
| Paid late, or after the order closed | No automatic change. A note asks you to review it. |

A payment counts as paid if the customer sent at least 99.5% of the amount. If a webhook is missed, the plugin checks unpaid orders about every five minutes for up to 30 days. You can also choose **Refresh Plaxswap payment** in the order actions.

## Limits

- One-off orders only. Subscriptions and automatic renewals aren't supported.
- Refunds aren't automatic. Marking an order Refunded doesn't send any coins.
- Your balance is credited in the coin the customer paid with. Swap inside your merchant account afterwards if you want one coin.
- A store on `localhost` can't receive webhooks.

## Troubleshooting

| What you see | What to check |
|---|---|
| Plaxswap isn't at checkout | Enable it and save valid keys. In test mode, sign in as a store admin or shop manager. In live mode, the store needs HTTPS. |
| The API key is rejected | A `pxs_test_` key needs Test mode on, and a `pxs_live_` key needs it off. |
| Settings won't save | Check outbound HTTPS from your server, finish your merchant setup, and use the signing secret from the same account. |
| A payment stays on hold | Check Webhooks in the dashboard, then choose Refresh Plaxswap payment on the order. |
| Webhooks don't arrive | The callback URL must be public HTTPS. Maintenance mode, a login wall or a firewall can block it. |

The full guide with screenshots is at [plaxswap.com/integrations/woocommerce](https://plaxswap.com/integrations/woocommerce).
