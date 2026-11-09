<?php
// Shared code for the PHP example: settings, API calls, the webhook signature check and a tiny order store.
declare(strict_types=1);

define('PLAXSWAP_API_BASE', rtrim(getenv('PLAXSWAP_API_BASE') ?: 'https://plaxswap.com', '/'));
define('PLAXSWAP_API_KEY', getenv('PLAXSWAP_API_KEY') ?: '');            // pxs_test_... or pxs_live_...
define('PLAXSWAP_WEBHOOK_SECRET', getenv('PLAXSWAP_WEBHOOK_SECRET') ?: ''); // whsec_...
define('SITE_URL', rtrim(getenv('SITE_URL') ?: 'http://localhost:3000', '/'));
define('PLAXSWAP_RECEIVE', getenv('PLAXSWAP_RECEIVE') ?: '');             // optional, such as usdt-tron
define('STORE_FILE', getenv('STORE_FILE') ?: __DIR__ . '/data/orders.json');

if (!preg_match('/^pxs_(test|live)_/', PLAXSWAP_API_KEY) || strpos(PLAXSWAP_WEBHOOK_SECRET, 'whsec_') !== 0) {
    http_response_code(500);
    exit("Set PLAXSWAP_API_KEY and PLAXSWAP_WEBHOOK_SECRET\n");
}
// A live key must never fulfil orders from test events, and the other way round.
define('PLAXSWAP_LIVE', strpos(PLAXSWAP_API_KEY, 'pxs_live_') === 0);
// Idempotency keys are per merchant account: put the site in them so two shops never collide.
define('SITE_KEY', (string) parse_url(SITE_URL, PHP_URL_HOST) . (parse_url(SITE_URL, PHP_URL_PORT) ? ':' . parse_url(SITE_URL, PHP_URL_PORT) : ''));

/** Calls the Plaxswap API. Throws on errors. */
function plaxswap_api(string $method, string $path, ?array $body = null, ?string $idempotencyKey = null): array
{
    $headers = ['Authorization: Bearer ' . PLAXSWAP_API_KEY, 'Accept: application/json'];
    if ($body !== null) { $headers[] = 'Content-Type: application/json'; }
    if ($idempotencyKey !== null) { $headers[] = 'Idempotency-Key: ' . $idempotencyKey; }
    $ch = curl_init(PLAXSWAP_API_BASE . $path);
    curl_setopt_array($ch, [
        CURLOPT_CUSTOMREQUEST => $method,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 15,
        CURLOPT_POSTFIELDS => $body !== null ? json_encode($body) : null,
    ]);
    $raw = curl_exec($ch);
    $status = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    if (PHP_VERSION_ID < 80000) { curl_close($ch); } // not needed from PHP 8, deprecated in 8.5
    $data = is_string($raw) ? json_decode($raw, true) : null;
    if ($status < 200 || $status >= 300 || !is_array($data)) {
        $message = $data['error']['message'] ?? ('Plaxswap API error ' . $status);
        throw new RuntimeException($message);
    }
    return $data;
}

/** True when the x-px-signature header matches the raw body. */
function plaxswap_verify_signature(string $rawBody, string $header, string $secret, int $tolerance = 300): bool
{
    $t = null;
    $v1 = [];
    foreach (explode(',', $header) as $part) {
        $pair = explode('=', trim($part), 2);
        if (count($pair) !== 2) { continue; }
        if ($pair[0] === 't' && preg_match('/^\d{10}$/', $pair[1])) { $t = $pair[1]; }
        if ($pair[0] === 'v1' && preg_match('/^[0-9a-f]{64}$/', $pair[1])) { $v1[] = $pair[1]; }
    }
    if ($t === null || !$v1 || abs(time() - (int) $t) > $tolerance) { return false; }
    $expected = hash_hmac('sha256', $t . '.' . $rawBody, $secret);
    foreach ($v1 as $sig) {
        if (hash_equals($expected, $sig)) { return true; }
    }
    return false;
}

/** "25.50" and "25.5" are the same amount. */
function same_amount(string $a, string $b): bool
{
    $norm = static function (string $s): string {
        $parts = explode('.', trim($s), 2);
        $int = ltrim($parts[0], '0');
        $frac = rtrim($parts[1] ?? '', '0');
        return ($int === '' ? '0' : $int) . '.' . $frac;
    };
    return $norm($a) === $norm($b);
}

/**
 * Runs $fn with the whole store locked, so two webhooks at once can't both mark an order paid.
 * This file store is for the example only: use your database and a transaction in production.
 */
function with_store(callable $fn)
{
    if (!is_dir(dirname(STORE_FILE))) { mkdir(dirname(STORE_FILE), 0700, true); }
    $fh = fopen(STORE_FILE, 'c+');
    flock($fh, LOCK_EX);
    $raw = stream_get_contents($fh);
    $store = $raw ? json_decode($raw, true) : null;
    if (!is_array($store)) { $store = ['orders' => [], 'events' => []]; }
    $result = $fn($store);
    ftruncate($fh, 0);
    rewind($fh);
    fwrite($fh, json_encode($store, JSON_PRETTY_PRINT));
    fflush($fh);
    flock($fh, LOCK_UN);
    fclose($fh);
    return $result;
}

/** Compares the payment read from the API with the order, then updates the order. */
function apply_payment(array &$order, array $payment): string
{
    if (($payment['id'] ?? '') !== $order['paymentId']) { return 'wrong payment'; }
    if (($payment['livemode'] ?? null) !== PLAXSWAP_LIVE) { return 'wrong mode'; }
    if ((string) ($payment['orderId'] ?? '') !== $order['id']) { return 'wrong order'; }
    if (($payment['currency'] ?? '') !== $order['currency'] || !same_amount((string) ($payment['amount'] ?? ''), $order['amount'])) {
        return 'wrong amount';
    }
    if ($order['status'] === 'paid') { return 'already paid'; }

    $status = $payment['status'] ?? '';
    if ($status === 'paid' && !empty($payment['late'])) {
        $order['status'] = 'needs_review'; // coins came after expiry: check before you ship
    } elseif ($status === 'paid') {
        $order['status'] = 'paid';
        $order['fulfilCount']++;
        $order['note'] = !empty($payment['overpaid']) ? 'Overpaid: review the extra' : '';
        error_log('Fulfilled order ' . $order['id'] . ' (payment ' . $payment['id'] . ')');
    } elseif (in_array($status, ['partially_paid', 'expired', 'failed', 'cancelled', 'confirming'], true)) {
        $order['status'] = $status;
    }
    return 'ok';
}
