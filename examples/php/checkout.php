<?php
// Saves an order, creates a Plaxswap payment and sends the customer to the checkout.
declare(strict_types=1);
require __DIR__ . '/lib.php';

$amount = trim((string) ($_POST['amount'] ?? ''));
if (!preg_match('/^\d+(\.\d{1,2})?$/', $amount)) {
    http_response_code(400);
    exit('Enter a price such as 25.50');
}

$order = with_store(static function (array &$store) use ($amount) {
    $id = (string) (1000 + count($store['orders']) + 1);
    $store['orders'][$id] = ['id' => $id, 'amount' => $amount, 'currency' => 'USD', 'status' => 'awaiting_payment', 'paymentId' => null, 'fulfilCount' => 0, 'note' => ''];
    return $store['orders'][$id];
});

$body = [
    'amount' => $order['amount'],
    'currency' => $order['currency'],
    'orderId' => $order['id'],
    'description' => 'Order ' . $order['id'],
    'returnUrl' => SITE_URL . '/order.php?id=' . $order['id'],
    'cancelUrl' => SITE_URL . '/',
];
if (PLAXSWAP_RECEIVE !== '') { $body['receive'] = PLAXSWAP_RECEIVE; }

try {
    // One Idempotency-Key per order: a retry or double click returns the same payment.
    $payment = plaxswap_api('POST', '/api/v1/payments', $body, SITE_KEY . '-order-' . $order['id']);
} catch (RuntimeException $e) {
    error_log('Create payment failed: ' . $e->getMessage());
    http_response_code(502);
    exit('Could not start the payment. Please try again.');
}

// Match webhooks on this id, never on a value from the browser.
with_store(static function (array &$store) use ($order, $payment) {
    $store['orders'][$order['id']]['paymentId'] = $payment['id'];
});

header('Location: ' . $payment['checkoutUrl'], true, 303);
