<?php
// Demo shop page. Run: php -S localhost:3000 -t .
?><!doctype html>
<title>Demo shop</title>
<h1>Demo shop</h1>
<form method="post" action="/checkout.php">
  <label>Price in USD <input name="amount" value="25.50"></label>
  <button>Pay with crypto</button>
</form>
