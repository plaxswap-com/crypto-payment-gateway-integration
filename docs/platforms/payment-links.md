# Payment links (no website needed)

A payment link asks for an exact amount of one coin, paid to your own address. It's free, needs no account and no code, and works for an invoice, a fixed price, or a one-off sale.

## Create a link

1. Open the [payment links page](https://plaxswap.com/pay).
2. Choose the coin and network you want to receive, the exact amount, your address, a title the payer will see, and how long the link stays open: 1 hour, 1 day, 7 days, 30 days, or with no end date.
3. Under **Link settings**, choose how many payments it takes. Leave **Accept more than one payment** off for an invoice (the link closes after one payment), or tick it for a fixed price that many people pay.
4. Share the link or its QR code.

When you create the link you also get a private manage link. It's the only way to see the payments and to cancel the link, and it can't be shown again, so keep it safe.

## What the payer does

1. Opens the link and chooses the coin they pay with.
2. Gives a refund address on that coin's network.
3. Sees the exact amount to send, with the Plaxswap fee included, and what you receive. The price is fixed for a few minutes.
4. Sends it within the time shown.

Your manage link shows each payment and the total received, and updates by itself. Only payments marked **Done** have reached your address.

## Fees

You pay nothing and receive exactly the amount on the link. The payer pays the Plaxswap fee on top:

| Payment | Fee |
|---|---|
| Stablecoin to stablecoin on one network | 1% |
| Other coins on one network | 1.5% |
| Across networks | 2% |

They also pay the route's cost and their own network fee, and see the total before sending.

## If a payment doesn't go through

- The payer's coins go back to their refund address, less network fees and a handling fee.
- If less than the full amount arrives, you get what arrived and the link stays open for the rest.
- If more arrives, the extra goes back to the payer.

## Rules that still apply

- Payers can't pay from countries under sanctions or that Plaxswap treats as high risk. See [supported countries](https://plaxswap.com/help/supported-countries).
- Sanctions and wallet screening, the travel rule and each route's amount range still apply, and a payment can be held for a check.
- Each payment through a direct route must be worth between $10 and $50,000, including conversion costs.

A payment through a payment link isn't a gateway payment: it doesn't use a merchant account, API keys or webhooks. For order-linked payments with webhooks, use the [API](../04-api-integration.md) or a [plugin](../01-choose-your-setup.md).

More detail: [How payment links work](https://plaxswap.com/help/payment-links) and [How to send a crypto invoice](https://plaxswap.com/help/crypto-invoice).
