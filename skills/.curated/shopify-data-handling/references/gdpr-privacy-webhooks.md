Complete implementation of the three mandatory GDPR webhooks required for Shopify App Store submission.

```typescript
// 1. customers/data_request — Customer requests their data
// Shopify sends this when a customer asks the merchant for their data
async function handleCustomerDataRequest(payload: {
  shop_domain: string;
  customer: { id: number; email: string; phone: string };
  orders_requested: number[];
  data_request: { id: number };
}): Promise<void> {
  // Collect all data you store about this customer
  const customerData = await db.customerRecords.findMany({
    where: {
      shopDomain: payload.shop_domain,
      shopifyCustomerId: String(payload.customer.id),
    },
  });

  const orderData = await db.orderRecords.findMany({
    where: {
      shopDomain: payload.shop_domain,
      shopifyOrderId: { in: payload.orders_requested.map(String) },
    },
  });

  // You have 30 days to respond
  // Email the data to the merchant (or make it available via your app)
  await sendDataExport({
    requestId: payload.data_request.id,
    shop: payload.shop_domain,
    customer: customerData,
    orders: orderData,
  });
}

// 2. customers/redact — Delete specific customer's data
async function handleCustomerRedact(payload: {
  shop_domain: string;
  customer: { id: number; email: string; phone: string };
  orders_to_redact: number[];
}): Promise<void> {
  // Delete ALL personal data for this customer
  await db.customerRecords.deleteMany({
    where: {
      shopDomain: payload.shop_domain,
      shopifyCustomerId: String(payload.customer.id),
    },
  });

  // Anonymize order records (keep for accounting, remove PII)
  for (const orderId of payload.orders_to_redact) {
    await db.orderRecords.update({
      where: { shopifyOrderId: String(orderId) },
      data: {
        customerEmail: null,
        customerName: null,
        shippingAddress: null,
        // Keep: orderId, total, line items, timestamps
      },
    });
  }

  // Log the deletion (keep audit record)
  await db.auditLog.create({
    data: {
      action: "CUSTOMER_DATA_REDACTED",
      shop: payload.shop_domain,
      customerId: String(payload.customer.id),
      timestamp: new Date(),
    },
  });
}

// 3. shop/redact — Delete ALL data for a shop (48h after uninstall)
async function handleShopRedact(payload: {
  shop_id: number;
  shop_domain: string;
}): Promise<void> {
  // Delete EVERYTHING related to this shop
  await db.customerRecords.deleteMany({
    where: { shopDomain: payload.shop_domain },
  });
  await db.orderRecords.deleteMany({
    where: { shopDomain: payload.shop_domain },
  });
  await db.sessions.deleteMany({
    where: { shop: payload.shop_domain },
  });
  await db.appSettings.deleteMany({
    where: { shopDomain: payload.shop_domain },
  });

  console.log(`All data deleted for ${payload.shop_domain}`);
}
```
