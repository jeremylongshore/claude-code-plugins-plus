# GDPR Webhook Handlers

Mandatory handlers required for Shopify App Store submission: customer data request, customer redact, and shop redact.

```typescript
// Mandatory GDPR handlers — your app will be REJECTED without these

// 1. Customer Data Request — merchant forwards customer's data request
app.post("/webhooks/gdpr/data-request", rawBodyParser, async (req, res) => {
  if (!verifyShopifyWebhook(req.body, req.headers["x-shopify-hmac-sha256"]!, SECRET)) {
    return res.status(401).send("Unauthorized");
  }

  const payload = JSON.parse(req.body.toString());
  // payload shape:
  // {
  //   "shop_id": 12345,
  //   "shop_domain": "store.myshopify.com",
  //   "orders_requested": [123, 456],
  //   "customer": { "id": 789, "email": "customer@example.com", "phone": "+1234567890" },
  //   "data_request": { "id": 101112 }
  // }

  // Collect all data you have for this customer
  const customerData = await collectCustomerData(payload.customer.id);
  await sendDataToMerchant(payload.shop_domain, customerData);

  res.status(200).send("OK");
});

// 2. Customer Redact — delete customer's personal data
app.post("/webhooks/gdpr/customers-redact", rawBodyParser, async (req, res) => {
  if (!verifyShopifyWebhook(req.body, req.headers["x-shopify-hmac-sha256"]!, SECRET)) {
    return res.status(401).send("Unauthorized");
  }

  const payload = JSON.parse(req.body.toString());
  // payload shape:
  // {
  //   "shop_id": 12345,
  //   "shop_domain": "store.myshopify.com",
  //   "customer": { "id": 789, "email": "customer@example.com", "phone": "+1234567890" },
  //   "orders_to_redact": [123, 456]
  // }

  await deleteCustomerData(payload.customer.id);
  await deleteOrderData(payload.orders_to_redact);

  res.status(200).send("OK");
});

// 3. Shop Redact — 48 hours after app uninstall, delete ALL shop data
app.post("/webhooks/gdpr/shop-redact", rawBodyParser, async (req, res) => {
  if (!verifyShopifyWebhook(req.body, req.headers["x-shopify-hmac-sha256"]!, SECRET)) {
    return res.status(401).send("Unauthorized");
  }

  const payload = JSON.parse(req.body.toString());
  // { "shop_id": 12345, "shop_domain": "store.myshopify.com" }

  await deleteAllShopData(payload.shop_id);

  res.status(200).send("OK");
});
```
