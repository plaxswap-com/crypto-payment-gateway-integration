# XenForo

The Plaxswap Crypto Payment Gateway add-on connects to XenForo 2.3+ as a payment profile, so it works wherever your forum already takes payments, such as account upgrades. Get it from [xenforo.com](https://xenforo.com/community/resources/plaxswap-crypto-payment-gateway-accept-bitcoin-usdt-more.10932/).

This is different from the Plaxswap Crypto Swaps add-on, which adds a swap page to a forum.

## Install

1. Back up your forum files and database.
2. In the Admin CP, open **Add-ons** and choose **Install/upgrade from archive**. Upload the release ZIP. To upgrade, upgrade the existing add-on; don't uninstall it first.

## Connect your Plaxswap account

3. Sign in to the [merchant dashboard](https://plaxswap.com/merchants/dashboard) with Google or Telegram. Complete your business profile and set up your authenticator.
4. Open **Developers**, then **API keys**, and choose **New key**. Select **Test**, name it XenForo and choose **Create test key**. It starts with `pxs_test_` and is shown only once.
5. Open **Developers**, then **Webhooks**, choose **Make a new secret** and copy it (`whsec_...`). A new secret replaces the old one for all your integrations.
6. In the Admin CP, open **Setup**, then **Payment profiles**, **Add payment profile**, and choose **Plaxswap Crypto Payment Gateway**. Paste the API key and the signing secret, then save.
7. Reopen the saved profile. It shows the exact webhook URL for this forum and profile, which looks like:

   ```
   https://forum.example/payment_callback.php?_xfProvider=plaxswap_gateway&profile_id=1
   ```

   In the merchant dashboard, open **Developers**, then **Webhooks**, choose **Add URL**, paste it into **Your shop's callback URL** and choose **Save**.
8. Choose **Send test** under Webhooks and check that it shows Delivered.

## Test, then go live

9. Select the payment profile for a purchase, such as an account upgrade. Complete a test checkout as a forum administrator with the test key. Normal members can't make test purchases that grant real access.
10. In the Admin CP, open **Plaxswap payment gateway**, then **Payments & tracking**, and check that the invoice is paid and the purchase activated once.
11. Create a live key in the same merchant account, replace the test key in the payment profile, and check one small real payment.

## How a payment works

- The member chooses Pay and goes to the Plaxswap checkout, picks a coin and network, and sees the exact amount and every fee before sending.
- Plaxswap credits your merchant balance. The forum checks the signature, asks the API to verify the payment, and activates the purchase.
- A member returning to the forum never activates a purchase by itself. Partial payments and payments under review wait.

## If something doesn't connect

| Problem | What to check |
|---|---|
| Invalid API key | Use a `pxs_test_` or `pxs_live_` key, not a login client id or a `pxk_` swap partner key. |
| Signing secret rejected | Use the `whsec_` secret from the same merchant account's Webhooks page. |
| No callback URL shown | Save the payment profile, then reopen it. |
| Test notification fails | Check the full HTTPS callback URL and `profile_id`. A forum login prompt or bot challenge must not block this address. |
