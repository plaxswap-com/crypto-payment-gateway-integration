#!/usr/bin/env bash
# Test mode only: act out an outcome and trigger the matching webhook.
# Usage: bash simulate.sh pay_7m2k9q4x8c1v5b3n paid
# Outcomes: paid, partially_paid, overpaid, late, expired, failed
set -euo pipefail
PAYMENT_ID="${1:?payment id}"
OUTCOME="${2:?outcome: paid, partially_paid, overpaid, late, expired or failed}"
API_BASE="${PLAXSWAP_API_BASE:-https://plaxswap.com}"
case "${PLAXSWAP_API_KEY:-}" in pxs_test_*) ;; *) echo "Use a pxs_test_ key: simulate works in test mode only" >&2; exit 1;; esac
curl -sS -X POST "$API_BASE/api/v1/payments/$PAYMENT_ID/simulate" \
  -H "Authorization: Bearer $PLAXSWAP_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"outcome\":\"$OUTCOME\"}"
echo
