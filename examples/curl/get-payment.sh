#!/usr/bin/env bash
# Read a payment as it stands now. Usage: bash get-payment.sh pay_7m2k9q4x8c1v5b3n
set -euo pipefail
PAYMENT_ID="${1:?payment id, such as pay_7m2k9q4x8c1v5b3n}"
API_BASE="${PLAXSWAP_API_BASE:-https://plaxswap.com}"
curl -sS "$API_BASE/api/v1/payments/$PAYMENT_ID" \
  -H "Authorization: Bearer ${PLAXSWAP_API_KEY:?set PLAXSWAP_API_KEY}"
echo
