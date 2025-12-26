---
name: validate-schemas
description: Validate API schemas
shortcut: sche
---
# Validate API Schemas

Implement comprehensive schema validation using modern validation libraries like JSON Schema, Joi, Yup, or Zod to ensure type safety, data integrity, and contract compliance across your API.

## When to Use This Command

Use `/validate-schemas` when you need to:
- Enforce strict data types and formats in API requests and responses
- Create reusable validation schemas across multiple endpoints
- Generate TypeScript types from validation schemas
- Implement complex conditional validation logic
- Provide detailed validation error messages to clients
- Ensure data consistency before database operations

DON'T use this when:
- Working with unstructured or highly dynamic data (use runtime checks instead)
- Building quick prototypes without formal contracts (premature optimization)
- Validation logic is trivial (simple type checks may suffice)

## Design Decisions

This command implements **Zod** as the primary approach because:
- TypeScript-first with automatic type inference
- Composable schemas with chaining syntax
- Zero runtime dependencies
- Excellent error messages out of the box
- Schema transformation and parsing capabilities
- Works seamlessly with modern frameworks

**Alternative considered: Joi**
- More mature with extensive ecosystem
- Better for JavaScript-only projects
- More verbose API
- Recommended for legacy Node.js applications

**Alternative considered: JSON Schema**
- Language-agnostic standard
- Better for cross-platform validation
- More complex to write and maintain
- Recommended when sharing schemas across different languages

## Prerequisites

Before running this command:
1. Choose validation library based on your tech stack
2. Define validation requirements for each endpoint
3. Plan error response format
4. Consider performance impact for complex schemas
5. Determine validation strategy (fail-fast vs. collect-all-errors)

## Implementation Process

### Step 1: Define Base Schemas
Create reusable schema primitives for common data types and patterns.

### Step 2: Compose Endpoint Schemas
Build complex schemas by composing base schemas with business rules.

### Step 3: Integrate with Middleware
Set up validation middleware to automatically validate requests and responses.

### Step 4: Generate Types
Generate TypeScript types from schemas for compile-time safety.

### Step 5: Implement Error Handling
Create consistent error formatting and reporting mechanisms.

## Output Format

The command generates:
- `schemas/` - Schema definitions organized by domain
- `validators/` - Compiled validation functions
- `types/` - Generated TypeScript types from schemas
- `middleware/validation.ts` - Request/response validation middleware
- `tests/schema.test.ts` - Schema validation test suites
- `docs/validation-rules.md` - Documentation of all validation rules

## Code Examples

### Example 1: Zod Schema Validation (TypeScript)

```typescript
// schemas/user.schema.ts
import { z } from 'zod';

// Base schemas for reuse
const emailSchema = z.string().email().toLowerCase();
const passwordSchema = z.string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain uppercase letter')
  .regex(/[a-z]/, 'Password must contain lowercase letter')
  .regex(/[0-9]/, 'Password must contain number')
  .regex(/[^A-Za-z0-9]/, 'Password must contain special character');

const phoneSchema = z.string().regex(
  /^\+?[1-9]\d{1,14}$/,
  'Invalid phone number format (E.164)'
);

const addressSchema = z.object({
  street: z.string().min(1).max(100),
  city: z.string().min(1).max(50),
  state: z.string().length(2).toUpperCase(),
  zipCode: z.string().regex(/^\d{5}(-\d{4})?$/),
  country: z.string().length(2).toUpperCase().default('US')
});

// User schemas
export const createUserSchema = z.object({
  body: z.object({
    email: emailSchema,
    password: passwordSchema,
    firstName: z.string().min(1).max(50),
    lastName: z.string().min(1).max(50),
    dateOfBirth: z.string().datetime().refine(
      (date) => {
        const age = new Date().getFullYear() - new Date(date).getFullYear();
        return age >= 18;
      },
      { message: 'Must be at least 18 years old' }
    ),
    phone: phoneSchema.optional(),
    address: addressSchema.optional(),
    preferences: z.object({
      newsletter: z.boolean().default(false),
      notifications: z.enum(['email', 'sms', 'push', 'none']).default('email'),
      theme: z.enum(['light', 'dark', 'auto']).default('auto')
    }).default({}),
    metadata: z.record(z.string(), z.any()).optional()
  })
});

export const updateUserSchema = z.object({
  params: z.object({
    id: z.string().uuid()
  }),
  body: createUserSchema.shape.body.partial().extend({
    // Can't update email without verification
    email: z.never().optional()
  })
});

export const getUserSchema = z.object({
  params: z.object({
    id: z.string().uuid()
  })
});

export const listUsersSchema = z.object({
  query: z.object({
    page: z.coerce.number().int().positive().default(1),
    limit: z.coerce.number().int().min(1).max(100).default(20),
    sort: z.enum(['createdAt', 'email', 'name']).default('createdAt'),
    order: z.enum(['asc', 'desc']).default('desc'),
    filter: z.object({
      email: z.string().optional(),
      status: z.enum(['active', 'inactive', 'suspended']).optional(),
      createdAfter: z.string().datetime().optional(),
      createdBefore: z.string().datetime().optional()
    }).optional()
  })
});

// Type inference
export type CreateUserInput = z.infer<typeof createUserSchema>;
export type UpdateUserInput = z.infer<typeof updateUserSchema>;
export type GetUserInput = z.infer<typeof getUserSchema>;
export type ListUsersInput = z.infer<typeof listUsersSchema>;

// Validation middleware
import { Request, Response, NextFunction } from 'express';

export function validate(schema: z.ZodSchema) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const validated = await schema.parseAsync({
        body: req.body,
        query: req.query,
        params: req.params
      });

      // Replace request properties with validated/transformed data
      req.body = validated.body || req.body;
      req.query = validated.query || req.query;
      req.params = validated.params || req.params;

      next();
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({
          error: 'Validation failed',
          details: error.errors.map(err => ({
            path: err.path.join('.'),
            message: err.message,
            code: err.code
          }))
        });
      }
      next(error);
    }
  };
}

// Usage in routes
import express from 'express';

const router = express.Router();

router.post('/users',
  validate(createUserSchema),
  async (req, res) => {
    // req.body is now typed and validated
    const user = await createUser(req.body);
    res.json(user);
  }
);

router.put('/users/:id',
  validate(updateUserSchema),
  async (req, res) => {
    const user = await updateUser(req.params.id, req.body);
    res.json(user);
  }
);
```

### Example 2: Joi Schema Validation (JavaScript)

```javascript
// schemas/product.schema.js
const Joi = require('joi');

// Custom validators
const customValidators = {
  sku: Joi.string().pattern(/^[A-Z]{3}-\d{6}$/),
  price: Joi.number().precision(2).positive().max(999999.99),
  url: Joi.string().uri({ scheme: ['http', 'https'] })
};

// Product schemas
const productSchema = {
  create: Joi.object({
    sku: customValidators.sku.required(),
    name: Joi.string().min(3).max(200).required(),
    description: Joi.string().max(2000).required(),
    price: customValidators.price.required(),
    compareAtPrice: customValidators.price
      .greater(Joi.ref('price'))
      .optional(),
    category: Joi.string().valid(
      'electronics',
      'clothing',
      'food',
      'books',
      'other'
    ).required(),
    tags: Joi.array()
      .items(Joi.string().min(2).max(20))
      .max(10)
      .unique(),
    inventory: Joi.object({
      quantity: Joi.number().integer().min(0).required(),
      trackInventory: Joi.boolean().default(true),
      allowBackorder: Joi.boolean().default(false),
      lowStockThreshold: Joi.number().integer().min(0).default(10)
    }).required(),
    images: Joi.array()
      .items(Joi.object({
        url: customValidators.url.required(),
        alt: Joi.string().max(200),
        isPrimary: Joi.boolean().default(false)
      }))
      .min(1)
      .max(10)
      .unique('url')
      .required(),
    shipping: Joi.object({
      weight: Joi.number().positive().required(),
      dimensions: Joi.object({
        length: Joi.number().positive().required(),
        width: Joi.number().positive().required(),
        height: Joi.number().positive().required()
      }).required(),
      requiresShipping: Joi.boolean().default(true),
      shippingClass: Joi.string().valid('standard', 'fragile', 'oversized')
    }).when('category', {
      is: 'electronics',
      then: Joi.required(),
      otherwise: Joi.optional()
    }),
    variants: Joi.array()
      .items(Joi.object({
        name: Joi.string().required(),
        options: Joi.array()
          .items(Joi.string())
          .min(1)
          .required()
      }))
      .optional(),
    metadata: Joi.object().pattern(
      Joi.string(),
      Joi.alternatives().try(
        Joi.string(),
        Joi.number(),
        Joi.boolean()
      )
    ).optional()
  }).custom((value, helpers) => {
    // Custom validation: ensure at least one primary image
    const primaryImages = value.images.filter(img => img.isPrimary);
    if (primaryImages.length !== 1) {
      return helpers.error('any.invalid', {
        message: 'Exactly one image must be marked as primary'
      });
    }
    return value;
  }),

  update: Joi.object({
    name: Joi.string().min(3).max(200),
    description: Joi.string().max(2000),
    price: customValidators.price,
    // ... partial schema
  }).min(1), // At least one field required

  list: Joi.object({
    page: Joi.number().integer().positive().default(1),
    limit: Joi.number().integer().min(1).max(100).default(20),
    category: Joi.string(),
    minPrice: Joi.number().positive(),
    maxPrice: Joi.number().positive().greater(Joi.ref('minPrice')),
    search: Joi.string().max(100),
    inStock: Joi.boolean()
  })
};

// Validation middleware
function validateRequest(schemaName) {
  return async (req, res, next) => {
    const schema = productSchema[schemaName];
    if (!schema) {
      return next(new Error(`Schema ${schemaName} not found`));
    }

    const dataToValidate = {
      ...req.body,
      ...req.query,
      ...req.params
    };

    try {
      const validated = await schema.validateAsync(dataToValidate, {
        abortEarly: false, // Return all errors
        stripUnknown: true, // Remove unknown keys
        convert: true // Type coercion
      });

      // Merge validated data back
      Object.keys(validated).forEach(key => {
        if (req.body.hasOwnProperty(key)) req.body[key] = validated[key];
        if (req.query.hasOwnProperty(key)) req.query[key] = validated[key];
        if (req.params.hasOwnProperty(key)) req.params[key] = validated[key];
      });

      next();
    } catch (error) {
      if (error.isJoi) {
        return res.status(400).json({
          error: 'Validation failed',
          details: error.details.map(detail => ({
            field: detail.path.join('.'),
            message: detail.message,
            type: detail.type
          }))
        });
      }
      next(error);
    }
  };
}

module.exports = {
  productSchema,
  validateRequest
};
```

### Example 3: Pydantic Schema Validation (Python)

```python
# schemas/order_schema.py
from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import re

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    BANK_TRANSFER = "bank_transfer"

class Address(BaseModel):
    street: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., regex="^[A-Z]{2}$")
    zip_code: str = Field(..., regex=r"^\d{5}(-\d{4})?$")
    country: str = Field(default="US", regex="^[A-Z]{2}$")

    @validator('state', 'country')
    def uppercase_codes(cls, v):
        return v.upper()

class OrderItem(BaseModel):
    product_id: str = Field(..., regex="^[A-Z]{3}-\d{6}$")
    quantity: int = Field(..., gt=0, le=100)
    unit_price: Decimal = Field(..., decimal_places=2, ge=0)
    discount: Optional[Decimal] = Field(None, decimal_places=2, ge=0, le=1)

    @validator('discount')
    def validate_discount(cls, v, values):
        if v and v >= 1:
            raise ValueError('Discount must be less than 100%')
        return v

    @property
    def subtotal(self) -> Decimal:
        discount_amount = self.discount or Decimal('0')
        return self.quantity * self.unit_price * (1 - discount_amount)

class CreateOrderSchema(BaseModel):
    customer_email: str = Field(..., regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    items: List[OrderItem] = Field(..., min_items=1, max_items=50)
    shipping_address: Address
    billing_address: Optional[Address] = None
    payment_method: PaymentMethod
    notes: Optional[str] = Field(None, max_length=500)
    coupon_code: Optional[str] = Field(None, regex="^[A-Z0-9]{4,12}$")

    @validator('customer_email')
    def validate_email(cls, v):
        # Additional email validation
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", v.lower()):
            raise ValueError('Invalid email format')
        return v.lower()

    @validator('billing_address', always=True)
    def set_billing_address(cls, v, values):
        # Use shipping address if billing not provided
        return v or values.get('shipping_address')

    @root_validator
    def validate_order(cls, values):
        items = values.get('items', [])

        # Check for duplicate products
        product_ids = [item.product_id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError('Duplicate products in order')

        # Calculate total
        total = sum(item.subtotal for item in items)
        if total <= 0:
            raise ValueError('Order total must be positive')

        # Validate coupon if provided
        coupon = values.get('coupon_code')
        if coupon and not cls.validate_coupon(coupon):
            raise ValueError('Invalid coupon code')

        return values

    @staticmethod
    def validate_coupon(code: str) -> bool:
        # Implement coupon validation logic
        valid_coupons = ['SAVE10', 'FREESHIP', 'WELCOME20']
        return code in valid_coupons

class UpdateOrderSchema(BaseModel):
    status: Optional[OrderStatus] = None
    shipping_address: Optional[Address] = None
    notes: Optional[str] = Field(None, max_length=500)
    tracking_number: Optional[str] = Field(None, regex=r"^[A-Z0-9]{10,30}$")

    class Config:
        use_enum_values = True

# FastAPI integration
from fastapi import FastAPI, HTTPException, Depends
from fastapi.encoders import jsonable_encoder

app = FastAPI()

@app.post("/orders", response_model=Dict[str, Any])
async def create_order(order: CreateOrderSchema):
    # Validation happens automatically
    order_dict = jsonable_encoder(order)
    # Process order
    return {"id": "ORD-123456", **order_dict}

@app.patch("/orders/{order_id}")
async def update_order(
    order_id: str,
    updates: UpdateOrderSchema
):
    # Only provided fields will be updated
    update_dict = updates.dict(exclude_unset=True)
    # Update order
    return {"id": order_id, **update_dict}

# Custom validation endpoint
@app.post("/validate/order")
async def validate_order(order: CreateOrderSchema):
    # Just validate without processing
    return {"valid": True, "data": order.dict()}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid type" | Wrong data type provided | Check schema definition and input data |
| "Required field missing" | Mandatory field not provided | Ensure all required fields are present |
| "Validation failed" | Business rule violation | Review custom validators and constraints |
| "Schema not found" | Referenced schema doesn't exist | Verify schema imports and definitions |
| "Circular dependency" | Schema references itself | Refactor to break circular references |

## Configuration Options

**Validation Strategies**
- `fail-fast`: Stop at first error (faster)
- `collect-all`: Gather all errors (better UX)
- `partial`: Allow partial validation for updates

**Type Coercion**
- `strict`: No type conversion
- `loose`: Attempt type conversion
- `smart`: Context-aware conversion

## Best Practices

DO:
- Create reusable base schemas for common patterns
- Use descriptive error messages for custom validators
- Generate TypeScript types from schemas
- Version schemas with your API
- Document all validation rules
- Test edge cases and boundary conditions

DON'T:
- Duplicate validation logic across layers
- Use overly complex nested schemas
- Ignore performance impact of complex validations
- Mix validation with business logic
- Trust client-side validation alone

## Performance Considerations

- Compile schemas once at startup
- Cache validated results for identical inputs
- Use async validation for external checks
- Limit regex complexity to prevent ReDoS attacks
- Consider schema complexity for large payloads

## Security Considerations

- Sanitize error messages to prevent information leakage
- Implement rate limiting on validation endpoints
- Use strict type checking to prevent injection attacks
- Validate file uploads separately with size limits
- Never expose internal schema structure to clients

## Related Commands

- `/api-response-validator` - Validate API responses
- `/api-contract-generator` - Generate schemas from code
- `/api-testing-framework` - Test with schema validation
- `/api-documentation-generator` - Document schemas

## Version History

- v1.0.0 (2024-10): Initial implementation with Zod, Joi, and Pydantic support
- Planned v1.1.0: Add support for Yup and JSON Schema generation