B2B-specific checkout configuration: draft orders, payment terms, and purchase order numbers.

## Draft Orders for B2B

Draft orders are the primary way to create B2B orders programmatically. They support purchase order numbers, payment terms, and company association:

```typescript
const DRAFT_ORDER_CREATE = `
  mutation draftOrderCreate($input: DraftOrderInput!) {
    draftOrderCreate(input: $input) {
      draftOrder {
        id
        name
        status
        invoiceUrl
        purchaseOrder
        totalPriceSet {
          shopMoney { amount currencyCode }
        }
        subtotalPriceSet {
          shopMoney { amount currencyCode }
        }
        totalTaxSet {
          shopMoney { amount currencyCode }
        }
        lineItems(first: 50) {
          edges {
            node {
              title
              quantity
              originalUnitPriceSet {
                shopMoney { amount currencyCode }
              }
            }
          }
        }
      }
      userErrors { field message }
    }
  }
`;

await client.request(DRAFT_ORDER_CREATE, {
  variables: {
    input: {
      purchaseOrder: "PO-2026-0042",
      note: "Q1 restock order",
      tags: ["wholesale", "tier-1"],
      lineItems: [
        {
          variantId: "gid://shopify/ProductVariant/111",
          quantity: 100,
        },
        {
          variantId: "gid://shopify/ProductVariant/222",
          quantity: 50,
        },
      ],
      purchasingEntity: {
        purchasingCompany: {
          companyId: "gid://shopify/Company/456",
          companyContactId: "gid://shopify/CompanyContact/789",
          companyLocationId: "gid://shopify/CompanyLocation/012",
        },
      },
      shippingAddress: {
        address1: "500 Industrial Blvd",
        address2: "Dock 3",
        city: "Dallas",
        provinceCode: "TX",
        countryCode: "US",
        zip: "75201",
      },
      paymentTerms: {
        paymentTermsTemplateId: "gid://shopify/PaymentTermsTemplate/1",
      },
    },
  },
});
```

## Payment Terms

Shopify provides built-in payment terms templates for B2B:

| Template | Description |
|----------|-------------|
| Due on receipt | Payment required immediately |
| Net 15 | Payment due 15 days after fulfillment |
| Net 30 | Payment due 30 days after fulfillment |
| Net 45 | Payment due 45 days after fulfillment |
| Net 60 | Payment due 60 days after fulfillment |
| Net 90 | Payment due 90 days after fulfillment |

Query available payment terms templates:

```typescript
const PAYMENT_TERMS_TEMPLATES = `
  query paymentTermsTemplates {
    paymentTermsTemplates {
      id
      name
      paymentTermsType
      dueInDays
      description
    }
  }
`;

const response = await client.request(PAYMENT_TERMS_TEMPLATES);
// Returns all available templates with their GIDs
```

## Sending Invoice to B2B Customer

After creating a draft order, send the invoice so the B2B contact can complete payment:

```typescript
const SEND_INVOICE = `
  mutation draftOrderInvoiceSend(
    $id: ID!,
    $email: DraftOrderInvoiceInput
  ) {
    draftOrderInvoiceSend(id: $id, email: $email) {
      draftOrder {
        id
        status
        invoiceSentAt
      }
      userErrors { field message }
    }
  }
`;

await client.request(SEND_INVOICE, {
  variables: {
    id: "gid://shopify/DraftOrder/123",
    email: {
      to: ["purchasing@acme-dist.com"],
      subject: "Invoice for PO-2026-0042",
      customMessage: "Your wholesale order is ready for payment.",
    },
  },
});
```

## Complete a Draft Order

Convert a draft order to a real order (mark as paid or apply payment terms):

```typescript
const DRAFT_ORDER_COMPLETE = `
  mutation draftOrderComplete($id: ID!, $paymentPending: Boolean) {
    draftOrderComplete(id: $id, paymentPending: $paymentPending) {
      draftOrder {
        id
        status
        order {
          id
          name
          displayFinancialStatus
        }
      }
      userErrors { field message }
    }
  }
`;

// paymentPending: true = mark as payment pending (Net 30 etc.)
// paymentPending: false = mark as paid
await client.request(DRAFT_ORDER_COMPLETE, {
  variables: {
    id: "gid://shopify/DraftOrder/123",
    paymentPending: true, // B2B orders typically use deferred payment
  },
});
```

## Vaulted Payment Methods

B2B customers can save payment methods for repeat orders:

```typescript
const CUSTOMER_PAYMENT_METHODS = `
  query customerPaymentMethods($customerId: ID!) {
    customer(id: $customerId) {
      id
      paymentMethods(first: 10) {
        edges {
          node {
            id
            instrument {
              ... on CustomerCreditCard {
                brand
                lastDigits
                expiryMonth
                expiryYear
              }
            }
            revokedAt
          }
        }
      }
    }
  }
`;

// Send a payment method request to the B2B customer
const SEND_PAYMENT_REQUEST = `
  mutation customerPaymentMethodSendUpdateEmail($customerId: ID!) {
    customerPaymentMethodSendUpdateEmail(customerId: $customerId) {
      customer { id }
      userErrors { field message }
    }
  }
`;
```

## B2B Order Workflow Summary

```
1. companyCreate → Create B2B company with contact and location
2. catalogCreate → Link product catalog to company location
3. priceListCreate → Set wholesale pricing for catalog
4. draftOrderCreate → Create order with PO number and payment terms
5. draftOrderInvoiceSend → Email invoice to B2B contact
6. Customer pays via invoice link (or you mark as paid)
7. draftOrderComplete → Converts to real order
8. Fulfill order through normal fulfillment flow
```
