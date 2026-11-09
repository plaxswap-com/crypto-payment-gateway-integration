# WHMCS

The Plaxswap WHMCS module lets your clients pay invoices in Bitcoin, Ether, USDT, USDC, Solana, Litecoin and other coins. The invoice is marked paid automatically once Plaxswap confirms the payment.

The module is waiting for approval on the WHMCS Marketplace. Until then, download it from [plaxswap.com/downloads/plaxswap-whmcs-gateway-1.0.0.zip](https://plaxswap.com/downloads/plaxswap-whmcs-gateway-1.0.0.zip), or ask [support](https://plaxswap.com/support).

## Requirements

- WHMCS 8.x.
- PHP 7.4 or newer with cURL.
- A public HTTPS address for your WHMCS install.
- A Plaxswap [merchant account](../02-merchant-account.md).

## Install

1. Upload the `modules` folder from the zip into your WHMCS root folder (the one with `configuration.php`). It adds:
   - `modules/gateways/plaxswap.php`
   - `modules/gateways/plaxswap/`
   - `modules/gateways/callback/plaxswap.php`
2. In WHMCS, open **Configuration**, then **System Settings**, **Payment Gateways** (Apps & Integrations), **All Payment Gateways**, and activate **Plaxswap - Bitcoin & Crypto Payments Gateway**.

## Connect your Plaxswap account

3. Sign in to the [merchant dashboard](https://plaxswap.com/merchants/dashboard), finish your business profile and set up your authenticator.
4. Open **Developers**, then **API keys**, and make a test key (`pxs_test_...`).
5. Open **Developers**, then **Webhooks**, and set **Your shop's callback URL** to:

   ```
   https://YOUR-WHMCS-ADDRESS/modules/gateways/callback/plaxswap.php
   ```

   Use your real WHMCS address, the one in Setup, General Settings, Domain. Choose **Save**, then **Make a new secret**, and copy the signing secret (`whsec_...`).
6. In the Plaxswap gateway settings in WHMCS, paste the API key and the signing secret and save. Leave **Convert To For Processing** empty: Plaxswap prices invoices in more than 60 currencies.
7. Choose **Send test** under Webhooks in the Plaxswap dashboard. It should show as Delivered.

## Test, then go live

8. While a test key is saved, only a logged-in WHMCS admin can pay; clients see "being set up". Log in to the admin area, open a client's unpaid invoice in the client area (Login as Client), choose **Pay with Bitcoin & Crypto** and complete the test payment. The invoice turns Paid, and Billing, Gateway Log shows a Success entry.
9. Create a live key in the same Plaxswap account, paste it in place of the test key, save, and make one small real payment to check.

## How a payment works

- The client chooses the pay button on the invoice and goes to the Plaxswap checkout, where they pick a coin and network and send the exact amount shown.
- Plaxswap confirms the payment, credits your merchant balance and sends the signed webhook.
- The module asks the API for the payment, checks it belongs to this invoice (amount, currency, reference, test or live) and marks the invoice paid once.
- If the webhook is late, the invoice is also checked when the client returns to it.
- Partial payments, payments under review and expired payments leave the invoice unpaid.
- Choosing the pay button again within the hour reuses the same payment, so a client is never asked to pay twice for one invoice.

## Privacy

Per payment, the module sends the invoice amount, currency, invoice number and return links. The client's email is sent only if you turn on **Share client email**. It stores the invoice number, Plaxswap payment id, amount, currency, status and a random check value in its own table, `mod_plaxswap_payments`.
