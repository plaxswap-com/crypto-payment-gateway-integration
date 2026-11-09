#!/usr/bin/env bash
# Coins you can receive, and what payers can pay each one with.
set -euo pipefail
API_BASE="${PLAXSWAP_API_BASE:-https://plaxswap.com}"
curl -sS "$API_BASE/api/v1/gateway/coins"
echo
