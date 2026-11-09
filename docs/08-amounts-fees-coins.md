# 8. Amounts, fees and coins

## The amount fields on a payment

| Field | Meaning |
|---|---|
| `amount`, `currency` | The price you asked for, as you sent it. |
| `receiveAmount` | The price in the coin you receive, fixed when the payment is made. |
| `expectedAmount` | What you should receive: `receiveAmount`, less the 1.5% platform fee when you pay it (`fee.paidBy` is `merchant`). |
| `receivedAmount` | What has reached your balance so far. |
| `fee` | The platform fee: `bps` (100 = 1%), who pays it, and its amount in your coin. |

## What happens when the amount isn't exact

- When the payer's coin is converted, they're asked for a little more than the price (a 0.5% cushion), so a small price move while their coins confirm still covers you. Whatever is left over reaches you.
- A short payment is passed on and marked `partially_paid`. While the payment is open, the payer can send the rest.
- An extra payment is passed on with `overpaid: true`.
- Coins that arrive after the payment expired, up to 24 hours later, are passed on with `late: true`.
- Refunds of payments that reached you are yours to make. A crypto payment can't be reversed.

## Fees

| Who | What | How much |
|---|---|---|
| Customer | Platform fee, shown at checkout | 1.5% of the payment |
| Customer | Network fees and conversion costs (Uniswap or SwapKit) | Inside the amount they send |
| You | Withdrawal to your own wallet | 0.3% plus the network fee |
| You | Swap inside your merchant balance | 0.3% same network, 0.5% same coin on another network, 0.7% another coin, plus the network fee |

Example: a $100 order. Your customer sends about $101.50 in the coin they chose, plus their network fee. About $100 in that coin reaches your merchant balance. Current figures are always on the [fees page](https://plaxswap.com/fees).

Payment links work differently: you pay nothing and receive the exact amount on the link, and the payer pays 1%, 1.5% or 2% on top depending on the coins and networks. See [Payment links](platforms/payment-links.md).

## Currencies

- Price in a fiat currency such as `USD`, `EUR`, `GBP` or `INR`, and it's converted when the payment is made.
- Or price in a coin, such as `USDT` or `BTC`.
- USD prices count one to one for USDT, USDC and DAI.
- If no current price is available, the API answers `503 rate_unavailable`. Try again in a minute.

## Coins

You choose one coin and network to receive, on your merchant page or per payment with `receive`. Your customer can pay with that coin, or with another coin that can be converted into it:

- on the same network through Uniswap;
- between networks through SwapKit (mainly BTC, ETH, and USDT or USDC on Ethereum and Arbitrum, and into Tron USDT).

The list changes, so read it live instead of hard-coding it:

```bash
curl -s https://plaxswap.com/api/v1/gateway/coins
```

The checkout shows only the coins that can pay that payment at that moment.

### Network matters

USDT on Tron, USDT on Ethereum and USDT on BNB Chain are different. Coins sent on the wrong network usually can't be recovered. The checkout shows the network next to every address, so tell customers to follow it exactly.

## Limits

- A payment must be worth more than about 1 US dollar. Each coin has its own upper limit, and the checkout shows it.
- Each API key can make 300 requests a minute.

Next: [Security](09-security.md)
