---
name: generate-sdk
description: Generate client SDKs from OpenAPI specs
shortcut: sdk
---
# Generate Client SDK

Automatically generate type-safe, production-ready client SDKs from OpenAPI/Swagger specifications for multiple programming languages with comprehensive features and documentation.

## When to Use This Command

Use `/generate-sdk` when you need to:
- Create official client libraries for your API
- Ensure type safety across different programming languages
- Maintain SDK consistency with API changes
- Reduce manual SDK maintenance overhead
- Provide developers with intuitive API clients
- Support multiple programming languages

DON'T use this when:
- Your API lacks proper OpenAPI documentation (create spec first)
- Building internal-only APIs with single consumer (direct integration may be simpler)
- API is still rapidly changing (wait for stability)

## Design Decisions

This command implements **OpenAPI Generator** as the primary approach because:
- Supports 50+ programming languages and frameworks
- Active community with regular updates
- Customizable templates for each language
- Generates both client and server code
- Comprehensive documentation generation
- Battle-tested in production environments

**Alternative considered: Swagger Codegen**
- Original OpenAPI code generator
- Less frequent updates
- Fewer customization options
- Recommended for legacy projects

**Alternative considered: Custom generators**
- Full control over generated code
- Better for specific requirements
- Higher maintenance burden
- Recommended only for unique needs

## Prerequisites

Before running this command:
1. Complete OpenAPI specification (v3.0 or v3.1)
2. Validate spec with OpenAPI validators
3. Define authentication schemes
4. Document all endpoints and models
5. Choose target languages and versions

## Implementation Process

### Step 1: Validate OpenAPI Specification
Ensure your OpenAPI spec is complete, valid, and includes all necessary details.

### Step 2: Configure Generator Options
Set language-specific options like package names, versions, and dependencies.

### Step 3: Generate SDK Code
Run the generator for each target language with customized templates.

### Step 4: Add Custom Enhancements
Implement additional features like retry logic, caching, or specialized authentication.

### Step 5: Package and Distribute
Create distribution packages for each language's package manager.

## Output Format

The command generates:
- `sdks/javascript/` - Node.js/Browser SDK with TypeScript definitions
- `sdks/python/` - Python SDK with type hints
- `sdks/java/` - Java SDK with Maven/Gradle support
- `sdks/go/` - Go SDK with modules
- `docs/sdk-usage.md` - Usage documentation for all SDKs
- `examples/` - Working examples for each language

## Code Examples

### Example 1: TypeScript SDK Generation and Usage

```yaml
# openapi.yaml
openapi: 3.0.0
info:
  title: E-commerce API
  version: 1.0.0
servers:
  - url: https://api.example.com/v1
paths:
  /products:
    get:
      operationId: listProducts
      parameters:
        - name: category
          in: query
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: Product list
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Product'
  /products/{productId}:
    get:
      operationId: getProduct
      parameters:
        - name: productId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Product details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Product'
components:
  schemas:
    Product:
      type: object
      required:
        - id
        - name
        - price
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        description:
          type: string
        price:
          type: number
          format: double
        category:
          type: string
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

```bash
# Generate TypeScript SDK
npx @openapitools/openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-axios \
  -o ./sdks/typescript \
  --additional-properties=\
npmName=@company/api-client,\
npmVersion=1.0.0,\
supportsES6=true,\
withInterfaces=true
```

```typescript
// sdks/typescript/src/index.ts (generated)
import { Configuration, ProductsApi } from '@company/api-client';

// Enhanced configuration with retry and interceptors
export class ApiClient {
  private config: Configuration;
  private productsApi: ProductsApi;
  private retryConfig = {
    retries: 3,
    retryDelay: 1000,
    retryCondition: (error: any) => {
      return error.response?.status >= 500;
    }
  };

  constructor(apiKey?: string, basePath?: string) {
    this.config = new Configuration({
      basePath: basePath || 'https://api.example.com/v1',
      accessToken: apiKey,
      baseOptions: {
        timeout: 10000,
        headers: {
          'User-Agent': '@company/api-client/1.0.0'
        }
      }
    });

    this.productsApi = new ProductsApi(this.config);
    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor for logging
    this.config.baseOptions.transformRequest = [
      (data, headers) => {
        console.log('API Request:', { data, headers });
        return data;
      }
    ];

    // Response interceptor for error handling
    this.config.baseOptions.validateStatus = (status) => {
      return status >= 200 && status < 300;
    };
  }

  async getProducts(options?: {
    category?: string;
    limit?: number;
  }): Promise<Product[]> {
    try {
      const response = await this.withRetry(() =>
        this.productsApi.listProducts(
          options?.category,
          options?.limit
        )
      );
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  async getProduct(productId: string): Promise<Product> {
    try {
      const response = await this.withRetry(() =>
        this.productsApi.getProduct(productId)
      );
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  private async withRetry<T>(
    fn: () => Promise<T>,
    retriesLeft = this.retryConfig.retries
  ): Promise<T> {
    try {
      return await fn();
    } catch (error) {
      if (retriesLeft > 0 && this.retryConfig.retryCondition(error)) {
        await this.delay(this.retryConfig.retryDelay);
        return this.withRetry(fn, retriesLeft - 1);
      }
      throw error;
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private handleError(error: any) {
    if (error.response) {
      console.error('API Error:', {
        status: error.response.status,
        data: error.response.data
      });
    } else if (error.request) {
      console.error('Network Error:', error.message);
    } else {
      console.error('Error:', error.message);
    }
  }
}

// Usage example
const client = new ApiClient('your-api-key');

// Get products with automatic retry and error handling
const products = await client.getProducts({
  category: 'electronics',
  limit: 50
});

// Get single product
const product = await client.getProduct('550e8400-e29b-41d4-a716-446655440000');
```

### Example 2: Python SDK Generation with Enhanced Features

```bash
# Generate Python SDK
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python \
  -o ./sdks/python \
  --additional-properties=\
packageName=company_api,\
packageVersion=1.0.0,\
projectName=company-api-client
```

```python
# sdks/python/company_api/enhanced_client.py
import time
import logging
from typing import Optional, Dict, Any, List
from functools import wraps
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from company_api import Configuration, ApiClient
from company_api.api import ProductsApi
from company_api.models import Product

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries=3, delay=1):
    """Decorator for retrying failed API calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {wait_time} seconds..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed")
            raise last_exception
        return wrapper
    return decorator

class EnhancedApiClient:
    """Enhanced API client with retry logic, caching, and connection pooling."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        # Configure base client
        config = Configuration()
        config.host = base_url or "https://api.example.com/v1"
        if api_key:
            config.api_key['Authorization'] = api_key
            config.api_key_prefix['Authorization'] = 'Bearer'

        # Set up session with connection pooling
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        self.api_client = ApiClient(configuration=config)
        self.api_client.rest_client.session = session
        self.products_api = ProductsApi(self.api_client)
        self.timeout = timeout
        self._cache: Dict[str, Any] = {}

    @retry_on_failure(max_retries=3, delay=1)
    def list_products(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = 20,
        use_cache: bool = True
    ) -> List[Product]:
        """List products with optional caching."""
        cache_key = f"products_{category}_{limit}"

        if use_cache and cache_key in self._cache:
            logger.info(f"Returning cached results for {cache_key}")
            return self._cache[cache_key]

        try:
            response = self.products_api.list_products(
                category=category,
                limit=limit,
                _request_timeout=self.timeout
            )

            if use_cache:
                self._cache[cache_key] = response
                logger.info(f"Cached results for {cache_key}")

            return response
        except Exception as e:
            logger.error(f"Failed to list products: {e}")
            raise

    @retry_on_failure(max_retries=3, delay=1)
    def get_product(
        self,
        product_id: str,
        use_cache: bool = True
    ) -> Product:
        """Get product details with optional caching."""
        cache_key = f"product_{product_id}"

        if use_cache and cache_key in self._cache:
            logger.info(f"Returning cached product {product_id}")
            return self._cache[cache_key]

        try:
            response = self.products_api.get_product(
                product_id=product_id,
                _request_timeout=self.timeout
            )

            if use_cache:
                self._cache[cache_key] = response
                logger.info(f"Cached product {product_id}")

            return response
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}")
            raise

    def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries matching pattern."""
        if pattern:
            keys_to_remove = [
                k for k in self._cache.keys()
                if pattern in k
            ]
            for key in keys_to_remove:
                del self._cache[key]
            logger.info(f"Cleared {len(keys_to_remove)} cache entries")
        else:
            self._cache.clear()
            logger.info("Cleared all cache entries")

# Usage example
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Initialize client
    client = EnhancedApiClient(
        api_key="your-api-key",
        timeout=30,
        max_retries=3
    )

    # List products with automatic retry and caching
    products = client.list_products(
        category="electronics",
        limit=50,
        use_cache=True
    )
    print(f"Found {len(products)} products")

    # Get specific product
    product = client.get_product("550e8400-e29b-41d4-a716-446655440000")
    print(f"Product: {product.name} - ${product.price}")
```

### Example 3: Multi-Language SDK Generation Script

```bash
#!/bin/bash
# generate-all-sdks.sh

SPEC_FILE="openapi.yaml"
OUTPUT_DIR="./sdks"
VERSION="1.0.0"

# Validate OpenAPI spec first
echo "Validating OpenAPI specification..."
npx @stoplight/spectral-cli lint $SPEC_FILE

if [ $? -ne 0 ]; then
    echo "OpenAPI spec validation failed"
    exit 1
fi

# Generate TypeScript SDK
echo "Generating TypeScript SDK..."
npx @openapitools/openapi-generator-cli generate \
  -i $SPEC_FILE \
  -g typescript-axios \
  -o $OUTPUT_DIR/typescript \
  --additional-properties=\
npmName=@company/api-client,\
npmVersion=$VERSION,\
supportsES6=true,\
withInterfaces=true

# Generate Python SDK
echo "Generating Python SDK..."
openapi-generator-cli generate \
  -i $SPEC_FILE \
  -g python \
  -o $OUTPUT_DIR/python \
  --additional-properties=\
packageName=company_api,\
packageVersion=$VERSION

# Generate Java SDK
echo "Generating Java SDK..."
openapi-generator-cli generate \
  -i $SPEC_FILE \
  -g java \
  -o $OUTPUT_DIR/java \
  --additional-properties=\
groupId=com.company,\
artifactId=api-client,\
artifactVersion=$VERSION,\
library=okhttp-gson

# Generate Go SDK
echo "Generating Go SDK..."
openapi-generator-cli generate \
  -i $SPEC_FILE \
  -g go \
  -o $OUTPUT_DIR/go \
  --additional-properties=\
packageName=company,\
packageVersion=$VERSION

# Generate documentation
echo "Generating SDK documentation..."
for lang in typescript python java go; do
  echo "## $lang SDK" >> $OUTPUT_DIR/README.md
  echo "See $OUTPUT_DIR/$lang for implementation" >> $OUTPUT_DIR/README.md
done

echo "SDK generation complete!"
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid OpenAPI spec" | Malformed specification | Validate with Spectral or similar tools |
| "Unsupported feature" | Generator limitation | Check generator documentation for support |
| "Template error" | Custom template issues | Review template syntax and variables |
| "Version conflict" | Dependency issues | Update generator and dependencies |
| "Generation failed" | Missing required fields | Ensure all required spec fields are present |

## Configuration Options

**Generator Options**
- `library`: HTTP client library to use
- `dateLibrary`: Date handling library
- `useSingleRequestParameter`: Bundle parameters
- `nullableFields`: Generate nullable types
- `enumUnknownDefaultCase`: Handle unknown enums

**Language-Specific Options**
- TypeScript: `npmRepository`, `withoutPrefixEnums`
- Python: `packageUrl`, `useNose`, `asyncio`
- Java: `serializationLibrary`, `useRuntimeException`
- Go: `isGoSubmodule`, `structPrefix`

## Best Practices

DO:
- Keep OpenAPI spec as single source of truth
- Version SDKs alongside API versions
- Include comprehensive examples
- Generate SDKs in CI/CD pipeline
- Add language-specific enhancements
- Publish to package registries

DON'T:
- Manually edit generated code (use templates)
- Skip OpenAPI validation before generation
- Ignore breaking changes in API
- Forget to update SDK documentation
- Mix generated and custom code

## Performance Considerations

- Use connection pooling for better performance
- Implement client-side caching where appropriate
- Add request/response compression support
- Consider pagination for large result sets
- Implement circuit breakers for resilience

## Related Commands

- `/api-documentation-generator` - Generate API docs
- `/api-contract-generator` - Create OpenAPI specs
- `/api-testing-framework` - Test SDKs
- `/api-versioning-manager` - Handle API versions

## Version History

- v1.0.0 (2024-10): Initial implementation with OpenAPI Generator support
- Planned v1.1.0: Add GraphQL and gRPC SDK generation