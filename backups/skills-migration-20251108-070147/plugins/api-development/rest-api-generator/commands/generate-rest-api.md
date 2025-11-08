---
description: Generate production-ready RESTful APIs with best practices
shortcut: gra
---

# Generate REST API

Automatically generate comprehensive RESTful API implementations from schema definitions with proper routing, validation, error handling, authentication, pagination, and OpenAPI documentation following industry best practices.

## When to Use This Command

Use `/generate-rest-api` when you need to:
- Build CRUD APIs quickly with consistent patterns
- Create microservices with RESTful interfaces
- Generate APIs from database schemas or models
- Implement standardized API patterns across projects
- Support multiple client applications (web, mobile, IoT)
- Build public APIs with comprehensive documentation

DON'T use this when:
- Building real-time applications (consider WebSocket/gRPC)
- Internal services need maximum performance (consider gRPC)
- Complex event-driven architectures (consider event streaming)
- GraphQL would better serve client needs

## Design Decisions

This command implements **OpenAPI-first design** as the primary approach because:
- Contract-first development ensures consistency
- Auto-generates server stubs and client SDKs
- Provides interactive API documentation
- Enables API mocking during development
- Supports multiple framework implementations
- Industry-standard specification format

**Alternative considered: Code-first with annotations**
- Faster initial development
- Tighter coupling to implementation
- Less portable across frameworks
- Recommended for rapid prototyping

**Alternative considered: GraphQL**
- More flexible client queries
- Reduced over/under-fetching
- Higher complexity
- Recommended for complex client needs

## Prerequisites

Before running this command:
1. Define your data models and relationships
2. Choose target framework (Express, FastAPI, NestJS, etc.)
3. Select database technology
4. Determine authentication requirements
5. Plan API versioning strategy

## Implementation Process

### Step 1: Define OpenAPI Specification
Create comprehensive API contracts with schemas, endpoints, and examples.

### Step 2: Generate Server Stubs
Build framework-specific implementations from OpenAPI specs.

### Step 3: Implement Business Logic
Add controllers, services, and data access layers.

### Step 4: Add Middleware
Configure authentication, validation, rate limiting, and CORS.

### Step 5: Generate Documentation
Create interactive docs, client SDKs, and Postman collections.

## Output Format

The command generates:
- `openapi.yaml` - Complete API specification
- `src/controllers/` - Request handlers with business logic
- `src/routes/` - RESTful endpoint definitions
- `src/models/` - Data models and schemas
- `src/middleware/` - Auth, validation, rate limiting
- `src/services/` - Business logic layer
- `tests/` - Integration and unit tests
- `docs/` - API documentation and examples

## Code Examples

### Example 1: E-commerce API with Express.js and TypeScript

```yaml
# openapi.yaml
openapi: 3.0.0
info:
  title: E-commerce API
  version: 1.0.0
  description: RESTful API for e-commerce platform

servers:
  - url: https://api.example.com/v1
    description: Production server
  - url: http://localhost:3000/v1
    description: Development server

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    Product:
      type: object
      required:
        - name
        - price
        - inventory
      properties:
        id:
          type: string
          format: uuid
          readOnly: true
        name:
          type: string
          minLength: 1
          maxLength: 200
        description:
          type: string
          maxLength: 2000
        price:
          type: number
          minimum: 0
          multipleOf: 0.01
        inventory:
          type: integer
          minimum: 0
        category:
          type: string
          enum: [electronics, clothing, food, books, other]
        images:
          type: array
          items:
            type: string
            format: uri
        metadata:
          type: object
          additionalProperties:
            type: string
        createdAt:
          type: string
          format: date-time
          readOnly: true
        updatedAt:
          type: string
          format: date-time
          readOnly: true

    Error:
      type: object
      required:
        - code
        - message
      properties:
        code:
          type: string
        message:
          type: string
        details:
          type: object

    PaginatedProducts:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/Product'
        pagination:
          type: object
          properties:
            total:
              type: integer
            page:
              type: integer
            perPage:
              type: integer
            totalPages:
              type: integer
        links:
          type: object
          properties:
            self:
              type: string
            next:
              type: string
            prev:
              type: string
            first:
              type: string
            last:
              type: string

paths:
  /products:
    get:
      summary: List products
      operationId: listProducts
      tags:
        - Products
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
            minimum: 1
        - name: perPage
          in: query
          schema:
            type: integer
            default: 20
            minimum: 1
            maximum: 100
        - name: category
          in: query
          schema:
            type: string
            enum: [electronics, clothing, food, books, other]
        - name: minPrice
          in: query
          schema:
            type: number
            minimum: 0
        - name: maxPrice
          in: query
          schema:
            type: number
            minimum: 0
        - name: search
          in: query
          schema:
            type: string
        - name: sort
          in: query
          schema:
            type: string
            enum: [name, price, createdAt]
        - name: order
          in: query
          schema:
            type: string
            enum: [asc, desc]
            default: asc
      responses:
        '200':
          description: Products retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedProducts'
        '400':
          description: Invalid request parameters
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

    post:
      summary: Create product
      operationId: createProduct
      tags:
        - Products
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Product'
      responses:
        '201':
          description: Product created successfully
          headers:
            Location:
              schema:
                type: string
                format: uri
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Product'
        '400':
          description: Invalid product data
        '401':
          description: Unauthorized
        '422':
          description: Validation error

  /products/{productId}:
    parameters:
      - name: productId
        in: path
        required: true
        schema:
          type: string
          format: uuid

    get:
      summary: Get product by ID
      operationId: getProduct
      tags:
        - Products
      responses:
        '200':
          description: Product retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Product'
        '404':
          description: Product not found

    put:
      summary: Update product
      operationId: updateProduct
      tags:
        - Products
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Product'
      responses:
        '200':
          description: Product updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Product'
        '400':
          description: Invalid product data
        '401':
          description: Unauthorized
        '404':
          description: Product not found

    patch:
      summary: Partial update product
      operationId: patchProduct
      tags:
        - Products
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              minProperties: 1
      responses:
        '200':
          description: Product updated successfully

    delete:
      summary: Delete product
      operationId: deleteProduct
      tags:
        - Products
      security:
        - bearerAuth: []
      responses:
        '204':
          description: Product deleted successfully
        '401':
          description: Unauthorized
        '404':
          description: Product not found
```

```typescript
// src/app.ts - Express application setup
import express, { Application } from 'express';
import helmet from 'helmet';
import cors from 'cors';
import compression from 'compression';
import morgan from 'morgan';
import swaggerUi from 'swagger-ui-express';
import { rateLimit } from 'express-rate-limit';
import { errorHandler } from './middleware/errorHandler';
import { notFoundHandler } from './middleware/notFoundHandler';
import { authMiddleware } from './middleware/auth';
import { validationMiddleware } from './middleware/validation';
import { productRouter } from './routes/products';
import { loadOpenAPISpec } from './utils/openapi';

export class App {
    public app: Application;

    constructor() {
        this.app = express();
        this.initializeMiddleware();
        this.initializeRoutes();
        this.initializeErrorHandling();
    }

    private initializeMiddleware(): void {
        // Security middleware
        this.app.use(helmet());
        this.app.use(cors({
            origin: process.env.ALLOWED_ORIGINS?.split(',') || '*',
            credentials: true
        }));

        // Rate limiting
        const limiter = rateLimit({
            windowMs: 15 * 60 * 1000, // 15 minutes
            max: 100, // limit each IP to 100 requests per windowMs
            standardHeaders: true,
            legacyHeaders: false,
            message: 'Too many requests from this IP'
        });
        this.app.use('/api/', limiter);

        // Body parsing
        this.app.use(express.json({ limit: '10mb' }));
        this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

        // Compression
        this.app.use(compression());

        // Logging
        this.app.use(morgan('combined'));

        // API Documentation
        const openAPISpec = loadOpenAPISpec();
        this.app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(openAPISpec));
    }

    private initializeRoutes(): void {
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({ status: 'healthy', timestamp: new Date().toISOString() });
        });

        // API routes
        this.app.use('/v1/products', productRouter);

        // Catch-all for API routes
        this.app.all('/v1/*', notFoundHandler);
    }

    private initializeErrorHandling(): void {
        this.app.use(errorHandler);
    }
}

// src/controllers/productController.ts
import { Request, Response, NextFunction } from 'express';
import { ProductService } from '../services/productService';
import { PaginationParams, FilterParams } from '../types';
import { ApiError } from '../utils/ApiError';

export class ProductController {
    constructor(private productService: ProductService) {}

    async listProducts(
        req: Request,
        res: Response,
        next: NextFunction
    ): Promise<void> {
        try {
            const pagination: PaginationParams = {
                page: parseInt(req.query.page as string) || 1,
                perPage: parseInt(req.query.perPage as string) || 20
            };

            const filters: FilterParams = {
                category: req.query.category as string,
                minPrice: parseFloat(req.query.minPrice as string),
                maxPrice: parseFloat(req.query.maxPrice as string),
                search: req.query.search as string,
                sort: req.query.sort as string || 'createdAt',
                order: req.query.order as 'asc' | 'desc' || 'desc'
            };

            const result = await this.productService.listProducts(
                pagination,
                filters
            );

            // Add HATEOAS links
            const baseUrl = `${req.protocol}://${req.get('host')}${req.baseUrl}`;
            const links = this.generatePaginationLinks(
                baseUrl,
                pagination,
                result.pagination.totalPages
            );

            res.json({
                ...result,
                links
            });
        } catch (error) {
            next(error);
        }
    }

    async getProduct(
        req: Request,
        res: Response,
        next: NextFunction
    ): Promise<void> {
        try {
            const { productId } = req.params;
            const product = await this.productService.getProduct(productId);

            if (!product) {
                throw new ApiError(404, 'Product not found');
            }

            // Add HATEOAS links
            const links = {
                self: `${req.protocol}://${req.get('host')}${req.originalUrl}`,
                update: {
                    href: `${req.protocol}://${req.get('host')}${req.originalUrl}`,
                    method: 'PUT'
                },
                delete: {
                    href: `${req.protocol}://${req.get('host')}${req.originalUrl}`,
                    method: 'DELETE'
                }
            };

            res.json({
                ...product,
                _links: links
            });
        } catch (error) {
            next(error);
        }
    }

    async createProduct(
        req: Request,
        res: Response,
        next: NextFunction
    ): Promise<void> {
        try {
            const product = await this.productService.createProduct(req.body);
            const location = `${req.protocol}://${req.get('host')}${req.baseUrl}/${product.id}`;

            res.status(201)
               .location(location)
               .json(product);
        } catch (error) {
            next(error);
        }
    }

    async updateProduct(
        req: Request,
        res: Response,
        next: NextFunction
    ): Promise<void> {
        try {
            const { productId } = req.params;
            const product = await this.productService.updateProduct(
                productId,
                req.body
            );

            if (!product) {
                throw new ApiError(404, 'Product not found');
            }

            res.json(product);
        } catch (error) {
            next(error);
        }
    }

    async patchProduct(
        req: Request,
        res: Response,
        next: NextFunction
    ): Promise<void> {
        try {
            const { productId } = req.params;
            const product = await this.productService.patchProduct(
                productId,
                req.body
            );

            if (!product) {
                throw new ApiError(404, 'Product not found');
            }

            res.json(product);
        } catch (error) {
            next(error);
        }
    }

    async deleteProduct(
        req: Request,
        res: Response,
        next: NextFunction
    ): Promise<void> {
        try {
            const { productId } = req.params;
            const deleted = await this.productService.deleteProduct(productId);

            if (!deleted) {
                throw new ApiError(404, 'Product not found');
            }

            res.status(204).send();
        } catch (error) {
            next(error);
        }
    }

    private generatePaginationLinks(
        baseUrl: string,
        pagination: PaginationParams,
        totalPages: number
    ): Record<string, string> {
        const links: Record<string, string> = {
            self: `${baseUrl}?page=${pagination.page}&perPage=${pagination.perPage}`
        };

        if (pagination.page > 1) {
            links.first = `${baseUrl}?page=1&perPage=${pagination.perPage}`;
            links.prev = `${baseUrl}?page=${pagination.page - 1}&perPage=${pagination.perPage}`;
        }

        if (pagination.page < totalPages) {
            links.next = `${baseUrl}?page=${pagination.page + 1}&perPage=${pagination.perPage}`;
            links.last = `${baseUrl}?page=${totalPages}&perPage=${pagination.perPage}`;
        }

        return links;
    }
}

// src/middleware/validation.ts
import { Request, Response, NextFunction } from 'express';
import Joi from 'joi';
import { ApiError } from '../utils/ApiError';

export function validate(schema: Joi.Schema) {
    return (req: Request, res: Response, next: NextFunction) => {
        const { error, value } = schema.validate(req.body, {
            abortEarly: false,
            stripUnknown: true
        });

        if (error) {
            const errors = error.details.map(detail => ({
                field: detail.path.join('.'),
                message: detail.message
            }));

            throw new ApiError(422, 'Validation error', errors);
        }

        req.body = value;
        next();
    };
}

// src/schemas/product.schema.ts
import Joi from 'joi';

export const productSchema = {
    create: Joi.object({
        name: Joi.string().min(1).max(200).required(),
        description: Joi.string().max(2000),
        price: Joi.number().min(0).multiple(0.01).required(),
        inventory: Joi.number().integer().min(0).required(),
        category: Joi.string().valid(
            'electronics',
            'clothing',
            'food',
            'books',
            'other'
        ),
        images: Joi.array().items(Joi.string().uri()),
        metadata: Joi.object().pattern(Joi.string(), Joi.string())
    }),

    update: Joi.object({
        name: Joi.string().min(1).max(200),
        description: Joi.string().max(2000),
        price: Joi.number().min(0).multiple(0.01),
        inventory: Joi.number().integer().min(0),
        category: Joi.string().valid(
            'electronics',
            'clothing',
            'food',
            'books',
            'other'
        ),
        images: Joi.array().items(Joi.string().uri()),
        metadata: Joi.object().pattern(Joi.string(), Joi.string())
    }).min(1),

    query: Joi.object({
        page: Joi.number().integer().min(1).default(1),
        perPage: Joi.number().integer().min(1).max(100).default(20),
        category: Joi.string().valid(
            'electronics',
            'clothing',
            'food',
            'books',
            'other'
        ),
        minPrice: Joi.number().min(0),
        maxPrice: Joi.number().min(0),
        search: Joi.string(),
        sort: Joi.string().valid('name', 'price', 'createdAt'),
        order: Joi.string().valid('asc', 'desc').default('asc')
    })
};
```

### Example 2: FastAPI Implementation with Python

```python
# main.py - FastAPI application
from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uvicorn

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="E-commerce API",
    version="1.0.0",
    description="RESTful API for e-commerce platform",
    docs_url="/api-docs",
    redoc_url="/redoc"
)

# Add rate limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*.example.com", "localhost"]
)

# Pydantic models
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    price: float = Field(..., gt=0, multiple_of=0.01)
    inventory: int = Field(..., ge=0)
    category: Optional[str] = Field(
        None,
        regex="^(electronics|clothing|food|books|other)$"
    )
    images: Optional[List[str]] = []
    metadata: Optional[dict] = {}

    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return round(v, 2)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[float] = Field(None, gt=0, multiple_of=0.01)
    inventory: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None
    images: Optional[List[str]] = None
    metadata: Optional[dict] = None

class Product(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PaginationParams(BaseModel):
    page: int = Query(1, ge=1, description="Page number")
    per_page: int = Query(20, ge=1, le=100, description="Items per page")

class FilterParams(BaseModel):
    category: Optional[str] = Query(None, regex="^(electronics|clothing|food|books|other)$")
    min_price: Optional[float] = Query(None, ge=0)
    max_price: Optional[float] = Query(None, ge=0)
    search: Optional[str] = Query(None, max_length=100)
    sort: str = Query("created_at", regex="^(name|price|created_at)$")
    order: str = Query("desc", regex="^(asc|desc)$")

class PaginatedResponse(BaseModel):
    data: List[Product]
    pagination: dict
    links: dict

# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get(
    "/v1/products",
    response_model=PaginatedResponse,
    summary="List products",
    tags=["Products"]
)
@limiter.limit("100/minute")
async def list_products(
    request: Request,
    pagination: PaginationParams = Depends(),
    filters: FilterParams = Depends()
):
    """
    List products with pagination and filtering.

    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 20, max: 100)
    - **category**: Filter by category
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **search**: Search in name and description
    - **sort**: Sort field (name, price, created_at)
    - **order**: Sort order (asc, desc)
    """
    # Implement service logic here
    products = await product_service.list_products(pagination, filters)

    # Generate HATEOAS links
    base_url = str(request.url).split('?')[0]
    links = generate_pagination_links(
        base_url,
        pagination.page,
        pagination.per_page,
        products['total_pages']
    )

    return PaginatedResponse(
        data=products['data'],
        pagination=products['pagination'],
        links=links
    )

@app.get(
    "/v1/products/{product_id}",
    response_model=Product,
    summary="Get product by ID",
    tags=["Products"]
)
async def get_product(product_id: str):
    """Get a single product by ID."""
    product = await product_service.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )
    return product

@app.post(
    "/v1/products",
    response_model=Product,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
    tags=["Products"]
)
@limiter.limit("10/minute")
async def create_product(
    request: Request,
    product: ProductCreate,
    user=Depends(get_current_user)
):
    """Create a new product (requires authentication)."""
    new_product = await product_service.create_product(product)

    # Set Location header
    response.headers["Location"] = f"{request.url}/{new_product.id}"

    return new_product

@app.put(
    "/v1/products/{product_id}",
    response_model=Product,
    summary="Update product",
    tags=["Products"]
)
async def update_product(
    product_id: str,
    product: ProductCreate,
    user=Depends(get_current_user)
):
    """Update an existing product (requires authentication)."""
    updated = await product_service.update_product(product_id, product)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )
    return updated

@app.patch(
    "/v1/products/{product_id}",
    response_model=Product,
    summary="Partial update product",
    tags=["Products"]
)
async def patch_product(
    product_id: str,
    product: ProductUpdate,
    user=Depends(get_current_user)
):
    """Partially update a product (requires authentication)."""
    # Filter out None values
    update_data = product.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    updated = await product_service.patch_product(product_id, update_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )
    return updated

@app.delete(
    "/v1/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
    tags=["Products"]
)
async def delete_product(
    product_id: str,
    user=Depends(get_current_user)
):
    """Delete a product (requires authentication)."""
    deleted = await product_service.delete_product(product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )
    return None

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={
            "code": "VALIDATION_ERROR",
            "message": str(exc)
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

### Example 3: Integration Tests

```javascript
// tests/products.test.js
const request = require('supertest');
const { app } = require('../src/app');
const { generateToken } = require('../src/utils/auth');

describe('Products API', () => {
    let authToken;
    let productId;

    beforeAll(async () => {
        // Generate auth token for protected routes
        authToken = await generateToken({ userId: 'test-user', role: 'admin' });
    });

    describe('GET /v1/products', () => {
        it('should return paginated products', async () => {
            const res = await request(app)
                .get('/v1/products')
                .query({ page: 1, perPage: 10 })
                .expect(200);

            expect(res.body).toHaveProperty('data');
            expect(res.body).toHaveProperty('pagination');
            expect(res.body).toHaveProperty('links');
            expect(res.body.data).toBeInstanceOf(Array);
            expect(res.body.data.length).toBeLessThanOrEqual(10);
        });

        it('should filter products by category', async () => {
            const res = await request(app)
                .get('/v1/products')
                .query({ category: 'electronics' })
                .expect(200);

            res.body.data.forEach(product => {
                expect(product.category).toBe('electronics');
            });
        });

        it('should handle invalid query parameters', async () => {
            const res = await request(app)
                .get('/v1/products')
                .query({ page: -1, perPage: 1000 })
                .expect(400);

            expect(res.body).toHaveProperty('code');
            expect(res.body).toHaveProperty('message');
        });
    });

    describe('POST /v1/products', () => {
        it('should create a new product', async () => {
            const newProduct = {
                name: 'Test Product',
                description: 'Test description',
                price: 99.99,
                inventory: 100,
                category: 'electronics'
            };

            const res = await request(app)
                .post('/v1/products')
                .set('Authorization', `Bearer ${authToken}`)
                .send(newProduct)
                .expect(201);

            expect(res.body).toHaveProperty('id');
            expect(res.body.name).toBe(newProduct.name);
            expect(res.headers).toHaveProperty('location');

            productId = res.body.id;
        });

        it('should validate required fields', async () => {
            const res = await request(app)
                .post('/v1/products')
                .set('Authorization', `Bearer ${authToken}`)
                .send({ name: 'Incomplete' })
                .expect(422);

            expect(res.body.code).toBe('VALIDATION_ERROR');
        });

        it('should require authentication', async () => {
            await request(app)
                .post('/v1/products')
                .send({ name: 'Test' })
                .expect(401);
        });
    });

    describe('GET /v1/products/:id', () => {
        it('should return a single product', async () => {
            const res = await request(app)
                .get(`/v1/products/${productId}`)
                .expect(200);

            expect(res.body.id).toBe(productId);
            expect(res.body).toHaveProperty('_links');
        });

        it('should return 404 for non-existent product', async () => {
            await request(app)
                .get('/v1/products/non-existent')
                .expect(404);
        });
    });

    describe('PATCH /v1/products/:id', () => {
        it('should partially update a product', async () => {
            const updates = { price: 89.99 };

            const res = await request(app)
                .patch(`/v1/products/${productId}`)
                .set('Authorization', `Bearer ${authToken}`)
                .send(updates)
                .expect(200);

            expect(res.body.price).toBe(89.99);
        });
    });

    describe('DELETE /v1/products/:id', () => {
        it('should delete a product', async () => {
            await request(app)
                .delete(`/v1/products/${productId}`)
                .set('Authorization', `Bearer ${authToken}`)
                .expect(204);

            // Verify deletion
            await request(app)
                .get(`/v1/products/${productId}`)
                .expect(404);
        });
    });
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid request body" | Malformed JSON or missing fields | Validate against schema |
| "Unauthorized" | Missing or invalid auth token | Include valid Bearer token |
| "Rate limit exceeded" | Too many requests | Implement backoff strategy |
| "Resource not found" | Invalid ID or deleted resource | Verify resource exists |
| "Validation error" | Data doesn't match schema | Check field requirements |

## Configuration Options

**Framework Options**
- `Express.js`: Node.js, middleware ecosystem
- `FastAPI`: Python, automatic OpenAPI docs
- `NestJS`: TypeScript, enterprise patterns
- `Django REST`: Python, batteries included
- `Spring Boot`: Java, enterprise features

**Database Options**
- `PostgreSQL`: Relational, ACID compliance
- `MongoDB`: Document store, flexible schema
- `MySQL`: Relational, wide support
- `DynamoDB`: Serverless, auto-scaling

## Best Practices

DO:
- Use proper HTTP status codes consistently
- Implement comprehensive input validation
- Version your APIs from the start
- Include pagination for list endpoints
- Return consistent error formats
- Add request/response logging

DON'T:
- Mix authentication schemes
- Return sensitive data in errors
- Use GET for state-changing operations
- Ignore rate limiting
- Skip input validation
- Forget CORS configuration

## Performance Considerations

- Implement database query optimization with indexes
- Use connection pooling for database connections
- Add caching layers (Redis, Memcached)
- Compress responses with gzip
- Implement pagination to limit response size
- Use CDN for static assets

## Security Considerations

- Always use HTTPS in production
- Implement proper authentication (JWT, OAuth2)
- Validate and sanitize all inputs
- Use parameterized queries to prevent SQL injection
- Implement rate limiting per user/IP
- Add API key rotation mechanisms
- Log security events for audit

## Related Commands

- `/api-documentation-generator` - Generate API docs
- `/api-gateway-builder` - Create API gateway
- `/graphql-server-builder` - Build GraphQL APIs
- `/grpc-service-generator` - Create gRPC services
- `/webhook-handler-creator` - Handle webhooks

## Version History

- v1.0.0 (2024-10): Initial implementation with Express, FastAPI, NestJS support
- Planned v1.1.0: Add Spring Boot and Django REST Framework templates