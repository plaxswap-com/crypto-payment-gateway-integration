#!/usr/bin/env bash
# End-to-end test of the three examples against the local mock API (no network, no real keys).
# Needs: python3, node 18+ and npm, php 7.4+ with curl, and Flask + requests for Python.
# Usage, from the repository root:  bash examples/test/run_e2e.sh [node|php|python ...]
set -uo pipefail
cd "$(dirname "$0")/.."
EX="$(pwd)"
TMP="$(mktemp -d)"
MOCK=http://127.0.0.1:8099
KEY=pxs_test_mock_only_key
SECRET=whsec_mock_only_secret
PASS=0; FAIL=0
PIDS=()
cleanup() { for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null; done; rm -rf "$TMP"; }
trap cleanup EXIT

ok()   { PASS=$((PASS+1)); echo "  pass  $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  FAIL  $1"; }
check(){ if eval "$2"; then ok "$1"; else bad "$1"; fi; }
wait_up(){ for _ in $(seq 1 50); do curl -s -o /dev/null "$1" && return 0; sleep 0.2; done; return 1; }
mock() { curl -s -X POST "$MOCK$1" -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d "$2"; }
field(){ python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }

python3 test/mock_api.py >/dev/null 2>&1 & PIDS+=($!)
for port in 3101 3102 3103 8099; do
  if lsof -nP -iTCP:$port -sTCP:LISTEN >/dev/null 2>&1 && [ $port != 8099 ]; then echo "Port $port is busy. Stop whatever uses it and run again."; exit 1; fi
done
wait_up "$MOCK/" || { echo "mock API did not start"; exit 1; }

run_example() {
  local name=$1 base=$2 checkout=$3 hook=$4 order_url=$5 log=$6
  echo "== $name"
  wait_up "$base/" || { bad "$name server started"; return; }
  mock /mock/config "{\"webhookUrl\":\"$base$hook\",\"secret\":\"$SECRET\"}" >/dev/null

  new_payment() {  # prints the payment id after a checkout
    local loc; loc=$(curl -s -o /dev/null -w '%{redirect_url}' -d amount=25.50 "$base$checkout")
    echo "${loc##*/}"
  }
  order_page() {  # $1 payment id
    local oid; oid=$(curl -s "$MOCK/api/v1/payments/$1" -H "Authorization: Bearer $KEY" | field "['orderId']")
    curl -s "$(printf "$order_url" "$base" "$oid")"
  }

  local pid page
  pid=$(new_payment); check "checkout redirects to the checkout page" '[[ "$pid" == pay_* ]]'
  page=$(order_page "$pid"); check "return page before payment shows waiting" '[[ "$page" == *"Waiting for your payment"* ]]'
  mock "/api/v1/payments/$pid/simulate" '{"outcome":"paid"}' >/dev/null
  sleep 0.3
  check "webhook alone fulfils the order (before the return page)" '[[ $(grep -c "Fulfilled order" "$log") == 1 ]]'
  page=$(order_page "$pid")
  check "paid webhook marks the order paid" '[[ "$page" == *"<code>paid</code>"* ]]'
  check "order fulfilled exactly once" '[[ "$page" == *"Fulfilled 1 time"* ]]'
  local st; st=$(mock /mock/resend-last '{}' | field "['status']")
  page=$(order_page "$pid")
  check "repeated webhook answered 200 ($st) and not fulfilled again" '[[ "$st" == 200 && "$page" == *"Fulfilled 1 time"* && $(grep -c "Fulfilled order" "$log") == 1 ]]'
  st=$(mock /mock/send-raw '{"secret":"whsec_wrong_secret"}' | field "['status']")
  check "wrong signature refused with 400 (got $st)" '[[ "$st" == 400 ]]'
  st=$(mock /mock/send-raw "{\"timestamp\":$(( $(date +%s) - 600 ))}" | field "['status']")
  check "10-minute-old timestamp refused with 400 (got $st)" '[[ "$st" == 400 ]]'

  pid=$(new_payment); mock "/api/v1/payments/$pid/simulate" '{"outcome":"partially_paid"}' >/dev/null
  page=$(order_page "$pid"); check "partially paid stays unpaid" '[[ "$page" == *"<code>partially_paid</code>"* && "$page" == *"Fulfilled 0 time"* ]]'
  pid=$(new_payment); mock "/api/v1/payments/$pid/simulate" '{"outcome":"late"}' >/dev/null
  page=$(order_page "$pid"); check "late payment goes to review, not fulfilled" '[[ "$page" == *"<code>needs_review</code>"* && "$page" == *"Fulfilled 0 time"* ]]'
  pid=$(new_payment); mock "/api/v1/payments/$pid/simulate" '{"outcome":"expired"}' >/dev/null
  page=$(order_page "$pid"); check "expired payment is not fulfilled" '[[ "$page" == *"<code>expired</code>"* && "$page" == *"Fulfilled 0 time"* ]]'
  pid=$(new_payment); mock "/api/v1/payments/$pid/simulate" '{"outcome":"overpaid"}' >/dev/null
  page=$(order_page "$pid"); check "overpaid is paid and flagged" '[[ "$page" == *"<code>paid</code>"* && "$page" == *"Overpaid"* ]]'
}

ENV=(PLAXSWAP_API_BASE="$MOCK" PLAXSWAP_API_KEY="$KEY" PLAXSWAP_WEBHOOK_SECRET="$SECRET")
WANT="${*:-node php python}"

if [[ " $WANT " == *" node "* ]]; then
  (cd node-express && [ -d node_modules ] || npm install --silent >/dev/null 2>&1)
  (cd node-express && exec env "${ENV[@]}" SITE_URL=http://127.0.0.1:3101 PORT=3101 node server.js >"$TMP/node.log" 2>&1) & PIDS+=($!)
  run_example node http://127.0.0.1:3101 /checkout /plaxswap-webhook "%s/orders/%s" "$TMP/node.log"
fi
if [[ " $WANT " == *" php "* ]]; then
  (cd php && exec env "${ENV[@]}" SITE_URL=http://127.0.0.1:3102 STORE_FILE="$TMP/php-orders.json" php -S 127.0.0.1:3102 -t . >"$TMP/php.log" 2>&1) & PIDS+=($!)
  run_example php http://127.0.0.1:3102 /checkout.php /webhook.php "%s/order.php?id=%s" "$TMP/php.log"
fi
if [[ " $WANT " == *" python "* ]]; then
  (cd python-flask && exec env "${ENV[@]}" SITE_URL=http://127.0.0.1:3103 DB_PATH="$TMP/shop.db" python3 -m flask --app app run --port 3103 >"$TMP/python.log" 2>&1) & PIDS+=($!)
  run_example python http://127.0.0.1:3103 /checkout /plaxswap-webhook "%s/orders/%s" "$TMP/python.log"
fi

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
