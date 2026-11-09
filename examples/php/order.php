<?php
// The return page. The customer coming back proves nothing, so it asks the API.
declare(strict_types=1);
require __DIR__ . '/lib.php';

$id = (string) ($_GET['id'] ?? '');
$order = with_store(static fn (array &$store) => $store['orders'][$id] ?? null);
if ($order === null) { http_response_code(404); exit('No such order'); }

if ($order['paymentId'] !== null && !in_array($order['status'], ['paid', 'needs_review'], true)) {
    try {
        $payment = plaxswap_api('GET', '/api/v1/payments/' . rawurlencode($order['paymentId']));
        $order = with_store(static function (array &$store) use ($id, $payment) {
            apply_payment($store['orders'][$id], $payment);
            return $store['orders'][$id];
        });
    } catch (RuntimeException $e) {
        // show what we have
    }
}

$texts = [
    'awaiting_payment' => 'Waiting for your payment.',
    'pending' => 'Waiting for your payment.',
    'confirming' => 'Payment received, confirming on the network.',
    'paid' => 'Paid. Thank you.',
    'needs_review' => 'Payment received late. We will check it and email you.',
    'partially_paid' => 'Part of the amount arrived. Please send the rest from the payment page.',
    'expired' => 'This payment expired.',
    'failed' => 'The payment did not go through.',
    'cancelled' => 'This payment was cancelled.',
];
$h = static fn (string $s): string => htmlspecialchars($s, ENT_QUOTES);
?><!doctype html>
<title>Order <?= $h($order['id']) ?></title>
<h1>Order <?= $h($order['id']) ?></h1>
<p><?= $h($texts[$order['status']] ?? $order['status']) ?></p>
<p>Status: <code><?= $h($order['status']) ?></code>. Fulfilled <?= (int) $order['fulfilCount'] ?> time(s). <?= $h($order['note']) ?></p>
