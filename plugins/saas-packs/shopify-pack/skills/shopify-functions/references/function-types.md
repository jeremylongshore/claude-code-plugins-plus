All Shopify Function types with their targeting, use cases, and API extensions.

## Function Types

| Type | TOML `type` | Target | Use Case |
|------|------------|--------|----------|
| Product Discounts | `product_discounts` | `purchase.product-discount.run` | Percentage/fixed discounts on line items |
| Order Discounts | `order_discounts` | `purchase.order-discount.run` | Discounts on the entire order (e.g., spend $100 get $10 off) |
| Shipping Discounts | `delivery_discounts` | `purchase.delivery-discount.run` | Free or discounted shipping based on conditions |
| Payment Customization | `payment_customization` | `purchase.payment-customization.run` | Hide/reorder/rename payment methods at checkout |
| Delivery Customization | `delivery_customization` | `purchase.delivery-customization.run` | Hide/reorder/rename delivery options at checkout |
| Cart Transform | `cart_transform` | `purchase.cart-transform.run` | Merge lines, expand bundles, modify cart before checkout |
| Fulfillment Constraints | `fulfillment_constraints` | `purchase.fulfillment-constraint.run` | Restrict which locations can fulfill which items |
| Order Routing | `order_routing_location_rule` | `purchase.order-routing-location-rule.run` | Custom logic for location-based order routing |
| Cart & Checkout Validation | `cart_checkout_validation` | `purchase.validation.run` | Block checkout based on custom rules (e.g., max 3 items) |

## Discount Function Subtypes

### Product Discount
```toml
type = "product_discounts"
[[targeting]]
target = "purchase.product-discount.run"
```
- Applies to individual cart lines
- Returns `targets` array with `productVariant` IDs
- Value: `percentage` or `fixedAmount`

### Order Discount
```toml
type = "order_discounts"
[[targeting]]
target = "purchase.order-discount.run"
```
- Applies to the whole order
- Does NOT use line-level targets
- Value: `percentage` or `fixedAmount` on order subtotal

### Shipping Discount
```toml
type = "delivery_discounts"
[[targeting]]
target = "purchase.delivery-discount.run"
```
- Targets delivery groups
- Can make specific shipping options free or discounted

## Non-Discount Functions

### Payment Customization
```toml
type = "payment_customization"
[[targeting]]
target = "purchase.payment-customization.run"
```
Returns `operations` array:
```typescript
{
  operations: [
    { hide: { paymentMethodId: "gid://shopify/PaymentMethod/1" } },
    { rename: { paymentMethodId: "gid://shopify/PaymentMethod/2", name: "Pay Later" } },
    { move: { paymentMethodId: "gid://shopify/PaymentMethod/3", index: 0 } },
  ]
}
```

### Delivery Customization
```toml
type = "delivery_customization"
[[targeting]]
target = "purchase.delivery-customization.run"
```
Same `operations` shape as payment: `hide`, `rename`, `move` on delivery options.

### Cart Transform
```toml
type = "cart_transform"
[[targeting]]
target = "purchase.cart-transform.run"
```
Operations: `merge` (combine lines), `expand` (split bundles into components), `update` (modify line properties).
