All Checkout UI Extension targets with descriptions and common use cases.

## Block Render Targets (Dynamic Placement)

These targets allow merchants to place the extension anywhere in the checkout editor.

| Target | Location | Use Case |
|--------|----------|----------|
| `purchase.checkout.block.render` | Merchant-configured block position | General-purpose: banners, upsells, custom fields |
| `purchase.thank-you.block.render` | Thank you page (merchant-positioned) | Post-purchase surveys, referral prompts |
| `customer-account.order-status.block.render` | Order status page | Tracking info, return initiation |

## Static Render Targets (Fixed Position)

These render at a specific, fixed location in the checkout flow.

### Information Step
| Target | Location |
|--------|----------|
| `purchase.checkout.header.render-after` | After the checkout header |
| `purchase.checkout.contact.render-before` | Before email/phone fields |
| `purchase.checkout.contact.render-after` | After email/phone fields |

### Shipping Step
| Target | Location |
|--------|----------|
| `purchase.checkout.delivery-address.render-before` | Before the shipping address form |
| `purchase.checkout.delivery-address.render-after` | After the shipping address form |
| `purchase.checkout.shipping-option-list.render-before` | Before shipping method options |
| `purchase.checkout.shipping-option-list.render-after` | After shipping method options |
| `purchase.checkout.shipping-option-item.render-after` | After each individual shipping option |
| `purchase.checkout.pickup-point-list.render-before` | Before pickup point options |
| `purchase.checkout.pickup-point-list.render-after` | After pickup point options |
| `purchase.checkout.pickup-location-list.render-before` | Before local pickup locations |
| `purchase.checkout.pickup-location-list.render-after` | After local pickup locations |

### Payment Step
| Target | Location |
|--------|----------|
| `purchase.checkout.payment-method-list.render-before` | Before payment methods |
| `purchase.checkout.payment-method-list.render-after` | After payment methods |

### Review & Completion
| Target | Location |
|--------|----------|
| `purchase.checkout.reductions.render-before` | Before discount code field |
| `purchase.checkout.reductions.render-after` | After discount code field |
| `purchase.checkout.cart-line-list.render-after` | After the order summary line items |
| `purchase.checkout.cart-line-item.render-after` | After each individual cart line item |
| `purchase.checkout.footer.render-after` | After the checkout footer |
| `purchase.checkout.actions.render-before` | Before the "Pay now" / "Complete order" button |

### Thank You Page
| Target | Location |
|--------|----------|
| `purchase.thank-you.header.render-after` | After thank you page header |
| `purchase.thank-you.footer.render-after` | After thank you page footer |
| `purchase.thank-you.cart-line-list.render-after` | After order summary on thank you |
| `purchase.thank-you.cart-line-item.render-after` | After each line item on thank you |
| `purchase.thank-you.customer-information.render-after` | After customer info on thank you |

## Choosing the Right Target

**For custom input fields** (delivery notes, gift messages):
- `purchase.checkout.delivery-address.render-after` or `purchase.checkout.block.render`

**For upsells/cross-sells**:
- `purchase.checkout.cart-line-list.render-after` or `purchase.checkout.actions.render-before`

**For trust badges/guarantees**:
- `purchase.checkout.payment-method-list.render-after` or `purchase.checkout.footer.render-after`

**For delivery date pickers**:
- `purchase.checkout.shipping-option-list.render-after`

**For post-purchase engagement**:
- `purchase.thank-you.block.render`
