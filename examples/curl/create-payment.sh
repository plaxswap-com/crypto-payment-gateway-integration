#!/usr/bin/env bash
# Create a payment. Usage: bash create-payment.sh 100 USD 1042 [receive-coin]
# Needs PLAXSWAP_API_KEY in the environment (pxs_test_... while testing).
set -euo pipefail
AMOUNT="${1:?amount, such as 100}"
CURRENCY="${2:?currency, such as USD}"
ORDER_ID="${3:?your order number}"
RECEIVE="${4:-}"
API_BASE="${PLAXSWAP_API_BASE:-https://plaxswap.com}"
BODY="{\"amount\":\"$AMOUNT\",\"currency\":\"$CURRENCY\",\"orderId\":\"$ORDER_ID\""
[ -n "$RECEIVE" ] && BODY="$BODY,\"receive\":\"$RECEIVE\""
BODY="$BODY}"
curl -sS -X POST "$API_BASE/api/v1/payments" \
  -H "Authorization: Bearer ${PLAXSWAP_API_KEY:?set PLAXSWAP_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order-$ORDER_ID" \
  -d "$BODY"
echo
