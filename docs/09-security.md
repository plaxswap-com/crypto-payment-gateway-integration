# 9. Security

A payment integration moves money, so a few rules matter more than anything else on this list.

## Keys and secrets

- Keep the API key and the webhook signing secret on your server only. Never put them in a web page, a mobile app, client-side JavaScript, or a public repository.
- Load them from environment variables or a secrets store. The examples read `PLAXSWAP_API_KEY` and `PLAXSWAP_WEBHOOK_SECRET`.
- Give each site its own key, named after it, so you can switch one off without breaking the others.
- If a key leaks, switch it off in the dashboard straight away and create a new one.
- Never send a key, signing secret, wallet recovery phrase or authenticator code to anyone, support included. Plaxswap will never ask for them.

## Trust nothing from the browser

- A customer arriving at your `returnUrl` doesn't prove they paid. Anyone can open that address.
- Never change an order because of a query string, form field or cookie the customer controls.
- The only proof is a signed webhook followed by your own `GET /api/v1/payments/{id}`.

## Webhook handler

- Check the signature on the raw body before you parse it.
- Refuse timestamps more than 5 minutes off.
- Skip event ids you've already handled.
- Match on the `payment.id` you stored, not on a number the customer could choose.
- Compare amount, currency, order number and mode before fulfilling.
- Fulfil inside a transaction or lock, so two deliveries at once can't ship twice.
- Don't log the signing secret, or full request headers, anywhere.

## Test and live

- Refuse to fulfil a real order from a test event (`livemode: false`).
- Use test keys only on test sites. Use live keys only on production.

## Your merchant account

- Turn on the authenticator app, and add a passkey if you can.
- Set an anti-phishing code, so you can recognise real Plaxswap emails.
- Keep the withdrawal address book short. New addresses wait 24 hours before use.
- Review signed-in devices from the dashboard from time to time.

## HTTPS

Serve your site and your webhook handler over HTTPS. `returnUrl` and `cancelUrl` must be HTTPS, and live payments on plugins need an HTTPS store.

Next: [Troubleshooting](10-troubleshooting.md)
