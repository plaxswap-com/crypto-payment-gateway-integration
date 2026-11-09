# 1. Choose your setup

There are four ways to take crypto with Plaxswap. They all end with the payment settled and the coins counted, but they differ in how much you build.

## Payment link

You set an exact amount in one coin, add a title, and share the link or its QR code. The person paying picks the coin they pay with on the payment page.

- No account, no website and no code.
- Good for invoices, a fixed price, or a one-off sale.
- The coins go to your own address. The payer pays the Plaxswap fee on top, so you receive the amount on the link.

Guide: [Payment links](platforms/payment-links.md)

## Plugin, module or add-on

If your site runs on supported software, install the ready-made integration. It creates the payment, sends the customer to checkout, checks the webhook and updates the order for you.

| Software | Integration | Where to get it |
|---|---|---|
| WooCommerce (WordPress) | Plaxswap Crypto Payments for WooCommerce | [WordPress.org](https://wordpress.org/plugins/plaxswap-crypto-payments/) |
| WHMCS | Plaxswap - Bitcoin & Crypto Payments Gateway | [Download](https://plaxswap.com/downloads/plaxswap-whmcs-gateway-1.0.0.zip) (WHMCS Marketplace listing waiting for approval) |
| XenForo 2.3+ | Plaxswap Crypto Payment Gateway | [xenforo.com](https://xenforo.com/community/resources/plaxswap-crypto-payment-gateway-accept-bitcoin-usdt-more.10932/) |

Guides: [WooCommerce](platforms/woocommerce.md), [WHMCS](platforms/whmcs.md), [XenForo](platforms/xenforo.md)

## Hosted checkout and API

For your own website, app or any other platform. Your server creates a payment through the REST API, sends the customer to the hosted checkout, and acts on a signed webhook. The checkout handles coin choice, networks, addresses, QR codes and confirmations, so you never touch a wallet.

Guide: [API integration](04-api-integration.md), then [Webhooks](05-webhooks.md)

## Which one should I pick?

| Question | If yes |
|---|---|
| Do you only send a few bills a month? | Payment link |
| Is your shop on WooCommerce, WHMCS or XenForo? | The plugin for it |
| Do you need the payment tied to your own order system, or to deliver something automatically? | Hosted checkout and API |
| Do you want the money in a merchant balance with withdrawals, payment history and a dashboard? | Plugin, or hosted checkout and API |

Payment links pay straight to your address and don't need a merchant account. Plugins and the API need a [merchant account](02-merchant-account.md), and payments are added to your merchant balance until you withdraw.

## Before you start

- Check that your business is allowed. The [merchant terms](https://plaxswap.com/legal/merchant-terms) bar gambling, adult content and financial services unless you're licensed for them where you operate.
- Checkout is closed in countries under sanctions or that Plaxswap treats as high risk. The list is on [supported countries](https://plaxswap.com/help/supported-countries).
- Whether you can take crypto, and how it's taxed, depends on your country. Ask an accountant or lawyer if you aren't sure.

Next: [Merchant account and keys](02-merchant-account.md)
