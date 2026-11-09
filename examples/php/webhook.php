<?php
// Plaxswap webhook handler. Set your callback URL to SITE_URL/webhook.php in the merchant dashboard.
declare(strict_types=1);
require __DIR__ . '/lib.php';

$raw = file_get_contents('php://input') ?: '';
if (strlen($raw) > 262144 || !plaxswap_verify_signature($raw, $_SERVER['HTTP_X_PX_SIGNATURE'] ?? '', PLAXSWAP_WEBHOOK_SECRET)) {
    http_response_code(400);
    exit;
}

$event = json_decode($raw, true);
if (!is_array($event) || !isset($event['id'], $event['event'])) { http_response_code(400); exit; }
if ($event['event'] === 'ping') { http_response_code(200); exit; }
if (($event['livemode'] ?? null) !== PLAXSWAP_LIVE) { http_response_code(200); exit; } // test events never touch live orders

$paymentId = (string) ($event['data']['id'] ?? '');
$order = with_store(static function (array &$store) use ($event, $paymentId) {
    if (isset($store['events'][$event['id']])) { return null; } // a repeat delivery
    foreach ($store['orders'] as $o) {
        if ($o['paymentId'] !== null && $o['paymentId'] === $paymentId) { return $o; }
    }
    return null;
});
if ($order === null) { http_response_code(200); exit; }

try {
    // Don't act on the webhook body alone: read the payment from the API.
    $payment = plaxswap_api('GET', '/api/v1/payments/' . rawurlencode($order['paymentId']));
} catch (RuntimeException $e) {
    error_log('Webhook check failed: ' . $e->getMessage());
    http_response_code(500); // Plaxswap retries later
    exit;
}

with_store(static function (array &$store) use ($event, $order, $payment) {
    $result = apply_payment($store['orders'][$order['id']], $payment);
    if ($result !== 'ok' && $result !== 'already paid') { error_log('Order ' . $order['id'] . ': ' . $result); }
    $store['events'][$event['id']] = time();
});
http_response_code(200);
