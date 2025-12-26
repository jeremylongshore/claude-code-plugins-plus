---
name: generate-grpc-service
description: >
  Generate production-ready gRPC services with Protocol Buffers
shortcut: grpc
---
# Generate gRPC Service

Automatically generate high-performance gRPC services with Protocol Buffer definitions, streaming support, load balancing, and comprehensive service implementations for multiple programming languages.

## When to Use This Command

Use `/generate-grpc-service` when you need to:
- Build high-performance microservices with binary protocol
- Implement real-time bidirectional streaming communication
- Create strongly-typed service contracts across languages
- Build internal services requiring minimal latency
- Support multiple programming languages with single definition
- Implement efficient mobile/IoT communication protocols

DON'T use this when:
- Building browser-based web applications (limited browser support)
- Simple REST APIs suffice (gRPC adds complexity)
- Working with teams unfamiliar with Protocol Buffers
- Debugging tools are limited in your environment

## Design Decisions

This command implements **gRPC with Protocol Buffers v3** as the primary approach because:
- Binary protocol offers 20-30% better performance than JSON
- Built-in code generation for 10+ languages
- Native support for streaming in all RPC patterns
- Strong typing prevents runtime errors
- Backward compatibility through field numbering
- Built-in service discovery and load balancing

**Alternative considered: Apache Thrift**
- Similar performance characteristics
- Less ecosystem support
- Fewer language bindings
- Recommended for Facebook ecosystem

**Alternative considered: GraphQL with subscriptions**
- Better for public APIs
- More flexible queries
- Higher overhead
- Recommended for client-facing APIs

## Prerequisites

Before running this command:
1. Protocol Buffer compiler (protoc) installed
2. Language-specific gRPC tools installed
3. Understanding of Protocol Buffer syntax
4. Service architecture defined
5. Authentication strategy determined

## Implementation Process

### Step 1: Define Service Contract
Create comprehensive .proto files with service definitions and message types.

### Step 2: Generate Language Bindings
Compile Protocol Buffers to target language code with gRPC plugins.

### Step 3: Implement Service Logic
Build server-side implementations for all RPC methods.

### Step 4: Add Interceptors
Implement cross-cutting concerns like auth, logging, and error handling.

### Step 5: Configure Production Settings
Set up TLS, connection pooling, and load balancing.

## Output Format

The command generates:
- `proto/service.proto` - Protocol Buffer definitions
- `server/` - Server implementation with all RPC methods
- `client/` - Client library with connection management
- `interceptors/` - Authentication, logging, metrics interceptors
- `config/` - TLS certificates and configuration
- `docs/api.md` - Service documentation

## Code Examples

### Example 1: E-commerce Service with All RPC Patterns

```protobuf
// proto/ecommerce.proto
syntax = "proto3";

package ecommerce.v1;

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";

// Service definition with all RPC patterns
service ProductService {
  // Unary RPC
  rpc GetProduct(GetProductRequest) returns (Product);

  // Server streaming
  rpc ListProducts(ListProductsRequest) returns (stream Product);

  // Client streaming
  rpc ImportProducts(stream Product) returns (ImportSummary);

  // Bidirectional streaming
  rpc WatchInventory(stream InventoryUpdate) returns (stream InventoryChange);

  // Batch operations
  rpc BatchGetProducts(BatchGetProductsRequest) returns (BatchGetProductsResponse);
}

// Message definitions
message Product {
  string id = 1;
  string name = 2;
  string description = 3;
  double price = 4;
  int32 inventory = 5;
  repeated string categories = 6;
  map<string, string> metadata = 7;
  google.protobuf.Timestamp created_at = 8;
  google.protobuf.Timestamp updated_at = 9;

  enum Status {
    STATUS_UNSPECIFIED = 0;
    STATUS_ACTIVE = 1;
    STATUS_DISCONTINUED = 2;
    STATUS_OUT_OF_STOCK = 3;
  }
  Status status = 10;
}

message GetProductRequest {
  string product_id = 1;
  repeated string fields = 2; // Field mask for partial responses
}

message ListProductsRequest {
  string category = 1;
  int32 page_size = 2;
  string page_token = 3;
  string order_by = 4;

  message Filter {
    double min_price = 1;
    double max_price = 2;
    repeated string tags = 3;
  }
  Filter filter = 5;
}

message ImportSummary {
  int32 total_received = 1;
  int32 successful = 2;
  int32 failed = 3;
  repeated ImportError errors = 4;
}

message ImportError {
  int32 index = 1;
  string product_id = 2;
  string error = 3;
}

message InventoryUpdate {
  string product_id = 1;
  int32 quantity_change = 2;
  string warehouse_id = 3;
}

message InventoryChange {
  string product_id = 1;
  int32 old_quantity = 2;
  int32 new_quantity = 3;
  google.protobuf.Timestamp timestamp = 4;
  string triggered_by = 5;
}

message BatchGetProductsRequest {
  repeated string product_ids = 1;
  repeated string fields = 2;
}

message BatchGetProductsResponse {
  repeated Product products = 1;
  repeated string not_found = 2;
}
```

```go
// server/main.go - Go server implementation
package main

import (
    "context"
    "crypto/tls"
    "fmt"
    "io"
    "log"
    "net"
    "sync"
    "time"

    pb "github.com/company/ecommerce/proto"
    "github.com/golang/protobuf/ptypes/empty"
    "google.golang.org/grpc"
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/credentials"
    "google.golang.org/grpc/keepalive"
    "google.golang.org/grpc/metadata"
    "google.golang.org/grpc/status"
    "google.golang.org/protobuf/types/known/timestamppb"
)

type productServer struct {
    pb.UnimplementedProductServiceServer
    mu       sync.RWMutex
    products map[string]*pb.Product
    watchers map[string]chan *pb.InventoryChange
}

// Unary RPC implementation
func (s *productServer) GetProduct(
    ctx context.Context,
    req *pb.GetProductRequest,
) (*pb.Product, error) {
    // Extract metadata for tracing
    if md, ok := metadata.FromIncomingContext(ctx); ok {
        if traceID := md.Get("trace-id"); len(traceID) > 0 {
            log.Printf("GetProduct request - trace: %s", traceID[0])
        }
    }

    s.mu.RLock()
    product, exists := s.products[req.ProductId]
    s.mu.RUnlock()

    if !exists {
        return nil, status.Errorf(
            codes.NotFound,
            "product %s not found",
            req.ProductId,
        )
    }

    // Apply field mask if specified
    if len(req.Fields) > 0 {
        return applyFieldMask(product, req.Fields), nil
    }

    return product, nil
}

// Server streaming implementation
func (s *productServer) ListProducts(
    req *pb.ListProductsRequest,
    stream pb.ProductService_ListProductsServer,
) error {
    s.mu.RLock()
    defer s.mu.RUnlock()

    count := 0
    for _, product := range s.products {
        // Apply filters
        if !matchesFilter(product, req) {
            continue
        }

        // Send product to stream
        if err := stream.Send(product); err != nil {
            return status.Errorf(
                codes.Internal,
                "failed to send product: %v",
                err,
            )
        }

        count++
        if req.PageSize > 0 && count >= int(req.PageSize) {
            break
        }

        // Simulate real-time processing
        time.Sleep(10 * time.Millisecond)
    }

    return nil
}

// Client streaming implementation
func (s *productServer) ImportProducts(
    stream pb.ProductService_ImportProductsServer,
) error {
    var summary pb.ImportSummary
    var errors []*pb.ImportError
    index := 0

    for {
        product, err := stream.Recv()
        if err == io.EOF {
            // Client finished sending
            summary.Errors = errors
            return stream.SendAndClose(&summary)
        }
        if err != nil {
            return status.Errorf(
                codes.Internal,
                "failed to receive product: %v",
                err,
            )
        }

        summary.TotalReceived++

        // Validate and store product
        if err := validateProduct(product); err != nil {
            summary.Failed++
            errors = append(errors, &pb.ImportError{
                Index:     int32(index),
                ProductId: product.Id,
                Error:     err.Error(),
            })
        } else {
            s.mu.Lock()
            s.products[product.Id] = product
            s.mu.Unlock()
            summary.Successful++
        }

        index++
    }
}

// Bidirectional streaming implementation
func (s *productServer) WatchInventory(
    stream pb.ProductService_WatchInventoryServer,
) error {
    // Create change channel for this client
    changeChan := make(chan *pb.InventoryChange, 100)
    clientID := generateClientID()

    s.mu.Lock()
    s.watchers[clientID] = changeChan
    s.mu.Unlock()

    defer func() {
        s.mu.Lock()
        delete(s.watchers, clientID)
        s.mu.Unlock()
        close(changeChan)
    }()

    // Handle bidirectional communication
    errChan := make(chan error, 2)

    // Goroutine to receive updates from client
    go func() {
        for {
            update, err := stream.Recv()
            if err == io.EOF {
                errChan <- nil
                return
            }
            if err != nil {
                errChan <- err
                return
            }

            // Process inventory update
            if err := s.processInventoryUpdate(update); err != nil {
                log.Printf("Failed to process update: %v", err)
                continue
            }

            // Notify all watchers
            change := &pb.InventoryChange{
                ProductId:   update.ProductId,
                NewQuantity: s.getInventory(update.ProductId),
                Timestamp:   timestamppb.Now(),
                TriggeredBy: clientID,
            }

            s.broadcastChange(change)
        }
    }()

    // Goroutine to send changes to client
    go func() {
        for change := range changeChan {
            if err := stream.Send(change); err != nil {
                errChan <- err
                return
            }
        }
    }()

    // Wait for error or completion
    return <-errChan
}

// Interceptor for authentication
func authInterceptor(
    ctx context.Context,
    req interface{},
    info *grpc.UnaryServerInfo,
    handler grpc.UnaryHandler,
) (interface{}, error) {
    // Extract token from metadata
    md, ok := metadata.FromIncomingContext(ctx)
    if !ok {
        return nil, status.Error(codes.Unauthenticated, "missing metadata")
    }

    tokens := md.Get("authorization")
    if len(tokens) == 0 {
        return nil, status.Error(codes.Unauthenticated, "missing token")
    }

    // Validate token (implement your auth logic)
    if !isValidToken(tokens[0]) {
        return nil, status.Error(codes.Unauthenticated, "invalid token")
    }

    // Continue to handler
    return handler(ctx, req)
}

// Main server setup
func main() {
    // Load TLS credentials
    cert, err := tls.LoadX509KeyPair("server.crt", "server.key")
    if err != nil {
        log.Fatalf("Failed to load certificates: %v", err)
    }

    config := &tls.Config{
        Certificates: []tls.Certificate{cert},
        ClientAuth:   tls.RequireAndVerifyClientCert,
    }

    creds := credentials.NewTLS(config)

    // Configure server options
    opts := []grpc.ServerOption{
        grpc.Creds(creds),
        grpc.UnaryInterceptor(authInterceptor),
        grpc.KeepaliveParams(keepalive.ServerParameters{
            MaxConnectionIdle: 5 * time.Minute,
            Time:             2 * time.Minute,
            Timeout:          20 * time.Second,
        }),
        grpc.KeepaliveEnforcementPolicy(keepalive.EnforcementPolicy{
            MinTime:             5 * time.Second,
            PermitWithoutStream: true,
        }),
        grpc.MaxConcurrentStreams(1000),
    }

    // Create gRPC server
    server := grpc.NewServer(opts...)

    // Register service
    pb.RegisterProductServiceServer(server, &productServer{
        products: make(map[string]*pb.Product),
        watchers: make(map[string]chan *pb.InventoryChange),
    })

    // Start listening
    lis, err := net.Listen("tcp", ":50051")
    if err != nil {
        log.Fatalf("Failed to listen: %v", err)
    }

    log.Println("gRPC server starting on :50051")
    if err := server.Serve(lis); err != nil {
        log.Fatalf("Failed to serve: %v", err)
    }
}
```

### Example 2: Python Client with Retry and Load Balancing

```python
# client/product_client.py
import grpc
import asyncio
import logging
from typing import List, Optional, AsyncIterator
from concurrent import futures
from grpc import aio
import backoff

from proto import ecommerce_pb2 as pb
from proto import ecommerce_pb2_grpc as pb_grpc

logger = logging.getLogger(__name__)

class ProductClient:
    """Enhanced gRPC client with retry, load balancing, and connection pooling."""

    def __init__(
        self,
        servers: List[str],
        api_key: Optional[str] = None,
        use_tls: bool = True,
        pool_size: int = 10
    ):
        self.servers = servers
        self.api_key = api_key
        self.use_tls = use_tls
        self.pool_size = pool_size
        self.channels = []
        self.stubs = []
        self._round_robin_counter = 0
        self._setup_channels()

    def _setup_channels(self):
        """Set up connection pool with load balancing."""
        for server in self.servers:
            for _ in range(self.pool_size // len(self.servers)):
                if self.use_tls:
                    # Load client certificates
                    with open('client.crt', 'rb') as f:
                        client_cert = f.read()
                    with open('client.key', 'rb') as f:
                        client_key = f.read()
                    with open('ca.crt', 'rb') as f:
                        ca_cert = f.read()

                    credentials = grpc.ssl_channel_credentials(
                        root_certificates=ca_cert,
                        private_key=client_key,
                        certificate_chain=client_cert
                    )
                    channel = aio.secure_channel(
                        server,
                        credentials,
                        options=[
                            ('grpc.keepalive_time_ms', 120000),
                            ('grpc.keepalive_timeout_ms', 20000),
                            ('grpc.keepalive_permit_without_calls', True),
                            ('grpc.http2.max_pings_without_data', 0),
                        ]
                    )
                else:
                    channel = aio.insecure_channel(
                        server,
                        options=[
                            ('grpc.keepalive_time_ms', 120000),
                            ('grpc.keepalive_timeout_ms', 20000),
                        ]
                    )

                self.channels.append(channel)
                self.stubs.append(pb_grpc.ProductServiceStub(channel))

    def _get_stub(self) -> pb_grpc.ProductServiceStub:
        """Get next stub using round-robin load balancing."""
        stub = self.stubs[self._round_robin_counter]
        self._round_robin_counter = (self._round_robin_counter + 1) % len(self.stubs)
        return stub

    def _get_metadata(self) -> List[tuple]:
        """Generate request metadata."""
        metadata = []
        if self.api_key:
            metadata.append(('authorization', f'Bearer {self.api_key}'))
        metadata.append(('trace-id', self._generate_trace_id()))
        return metadata

    @backoff.on_exception(
        backoff.expo,
        grpc.RpcError,
        max_tries=3,
        giveup=lambda e: e.code() != grpc.StatusCode.UNAVAILABLE
    )
    async def get_product(
        self,
        product_id: str,
        fields: Optional[List[str]] = None
    ) -> pb.Product:
        """Get single product with retry logic."""
        request = pb.GetProductRequest(
            product_id=product_id,
            fields=fields or []
        )

        try:
            response = await self._get_stub().GetProduct(
                request,
                metadata=self._get_metadata(),
                timeout=5.0
            )
            return response
        except grpc.RpcError as e:
            logger.error(f"Failed to get product {product_id}: {e.details()}")
            raise

    async def list_products(
        self,
        category: Optional[str] = None,
        page_size: int = 100,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> AsyncIterator[pb.Product]:
        """Stream products with server-side streaming."""
        request = pb.ListProductsRequest(
            category=category or "",
            page_size=page_size
        )

        if min_price is not None or max_price is not None:
            request.filter.CopyFrom(pb.ListProductsRequest.Filter(
                min_price=min_price or 0,
                max_price=max_price or float('inf')
            ))

        try:
            stream = self._get_stub().ListProducts(
                request,
                metadata=self._get_metadata(),
                timeout=30.0
            )

            async for product in stream:
                yield product
        except grpc.RpcError as e:
            logger.error(f"Failed to list products: {e.details()}")
            raise

    async def import_products(
        self,
        products: List[pb.Product]
    ) -> pb.ImportSummary:
        """Import products using client-side streaming."""
        async def generate_products():
            for product in products:
                yield product
                await asyncio.sleep(0.01)  # Rate limiting

        try:
            response = await self._get_stub().ImportProducts(
                generate_products(),
                metadata=self._get_metadata(),
                timeout=60.0
            )

            if response.failed > 0:
                logger.warning(
                    f"Import completed with {response.failed} failures: "
                    f"{[e.error for e in response.errors]}"
                )

            return response
        except grpc.RpcError as e:
            logger.error(f"Failed to import products: {e.details()}")
            raise

    async def watch_inventory(
        self,
        updates: AsyncIterator[pb.InventoryUpdate]
    ) -> AsyncIterator[pb.InventoryChange]:
        """Bidirectional streaming for inventory monitoring."""
        try:
            stream = self._get_stub().WatchInventory(
                metadata=self._get_metadata()
            )

            # Start sending updates
            send_task = asyncio.create_task(self._send_updates(stream, updates))

            # Receive changes
            try:
                async for change in stream:
                    yield change
            finally:
                send_task.cancel()

        except grpc.RpcError as e:
            logger.error(f"Failed in inventory watch: {e.details()}")
            raise

    async def _send_updates(
        self,
        stream,
        updates: AsyncIterator[pb.InventoryUpdate]
    ):
        """Send inventory updates to server."""
        try:
            async for update in updates:
                await stream.write(update)
            await stream.done_writing()
        except asyncio.CancelledError:
            pass

    async def close(self):
        """Close all channels gracefully."""
        close_tasks = [channel.close() for channel in self.channels]
        await asyncio.gather(*close_tasks)

    @staticmethod
    def _generate_trace_id() -> str:
        """Generate unique trace ID for request tracking."""
        import uuid
        return str(uuid.uuid4())

# Usage example
async def main():
    # Initialize client with load balancing
    client = ProductClient(
        servers=[
            'product-service-1:50051',
            'product-service-2:50051',
            'product-service-3:50051'
        ],
        api_key='your-api-key',
        use_tls=True
    )

    try:
        # Unary call
        product = await client.get_product('prod-123')
        print(f"Product: {product.name} - ${product.price}")

        # Server streaming
        async for product in client.list_products(
            category='electronics',
            min_price=100,
            max_price=1000
        ):
            print(f"Listed: {product.name}")

        # Client streaming
        products_to_import = [
            pb.Product(id=f'new-{i}', name=f'Product {i}', price=99.99)
            for i in range(100)
        ]
        summary = await client.import_products(products_to_import)
        print(f"Imported {summary.successful} products")

        # Bidirectional streaming
        async def generate_updates():
            for i in range(10):
                yield pb.InventoryUpdate(
                    product_id=f'prod-{i}',
                    quantity_change=5,
                    warehouse_id='warehouse-1'
                )
                await asyncio.sleep(1)

        async for change in client.watch_inventory(generate_updates()):
            print(f"Inventory change: {change.product_id} -> {change.new_quantity}")

    finally:
        await client.close()

if __name__ == '__main__':
    asyncio.run(main())
```

### Example 3: Node.js Implementation with Health Checking

```javascript
// server/index.js
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');

// Load proto file
const PROTO_PATH = path.join(__dirname, '../proto/ecommerce.proto');
const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true
});

const protoDescriptor = grpc.loadPackageDefinition(packageDefinition);
const ecommerce = protoDescriptor.ecommerce.v1;

// Health check implementation
const health = require('grpc-health-check');
const healthImpl = new health.Implementation({
    '': 'SERVING',
    'ecommerce.v1.ProductService': 'SERVING'
});

// Service implementation
class ProductService {
    constructor() {
        this.products = new Map();
        this.watchers = new Map();
    }

    async getProduct(call, callback) {
        const { product_id } = call.request;
        const product = this.products.get(product_id);

        if (!product) {
            callback({
                code: grpc.status.NOT_FOUND,
                message: `Product ${product_id} not found`
            });
            return;
        }

        callback(null, product);
    }

    async listProducts(call) {
        const { category, page_size } = call.request;
        let count = 0;

        for (const [id, product] of this.products) {
            if (category && product.categories.indexOf(category) === -1) {
                continue;
            }

            call.write(product);
            count++;

            if (page_size > 0 && count >= page_size) {
                break;
            }

            // Simulate processing delay
            await new Promise(resolve => setTimeout(resolve, 10));
        }

        call.end();
    }

    // Add remaining methods...
}

// Server setup
function main() {
    const server = new grpc.Server({
        'grpc.max_concurrent_streams': 1000,
        'grpc.max_receive_message_length': 1024 * 1024 * 16
    });

    // Add services
    server.addService(
        ecommerce.ProductService.service,
        new ProductService()
    );

    // Add health check
    server.addService(health.service, healthImpl);

    // Start server
    server.bindAsync(
        '0.0.0.0:50051',
        grpc.ServerCredentials.createInsecure(),
        (err, port) => {
            if (err) {
                console.error('Failed to bind:', err);
                return;
            }
            console.log(`gRPC server running on port ${port}`);
            server.start();
        }
    );
}

main();
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Failed to compile proto" | Invalid Protocol Buffer syntax | Validate with `protoc --lint` |
| "Connection refused" | Server not running or wrong port | Check server status and port |
| "Deadline exceeded" | Request timeout | Increase timeout or optimize operation |
| "Resource exhausted" | Rate limiting or quota exceeded | Implement backoff and retry |
| "Unavailable" | Server temporarily down | Implement circuit breaker pattern |

## Configuration Options

**Server Options**
- `MaxConcurrentStreams`: Limit concurrent streams per connection
- `MaxReceiveMessageSize`: Maximum message size (default 4MB)
- `KeepaliveParams`: Connection health monitoring
- `ConnectionTimeout`: Maximum idle time before closing

**Client Options**
- `LoadBalancingPolicy`: round_robin, pick_first, grpclb
- `WaitForReady`: Block until server available
- `Retry`: Automatic retry configuration
- `Interceptors`: Add cross-cutting concerns

## Best Practices

DO:
- Use field numbers consistently for backward compatibility
- Implement proper error codes and messages
- Add request deadlines for all RPCs
- Use streaming for large datasets
- Implement health checking endpoints
- Version your services properly

DON'T:
- Change field numbers in proto files
- Use gRPC for browser clients without proxy
- Ignore proper error handling
- Send large messages without streaming
- Skip TLS in production
- Use synchronous calls for long operations

## Performance Considerations

- Binary protocol reduces bandwidth by 20-30% vs JSON
- HTTP/2 multiplexing eliminates head-of-line blocking
- Connection pooling reduces handshake overhead
- Streaming prevents memory exhaustion with large datasets
- Protocol Buffers provide 3-10x faster serialization than JSON

## Security Considerations

- Always use TLS in production with mutual authentication
- Implement token-based authentication via metadata
- Use interceptors for consistent auth across services
- Validate all input according to proto definitions
- Implement rate limiting per client
- Use service accounts for service-to-service auth

## Related Commands

- `/rest-api-generator` - Generate REST APIs
- `/graphql-server-builder` - Build GraphQL servers
- `/api-gateway-builder` - Create API gateways
- `/webhook-handler-creator` - Handle webhooks
- `/websocket-server-builder` - WebSocket servers

## Version History

- v1.0.0 (2024-10): Initial implementation with Go, Python, Node.js support
- Planned v1.1.0: Add Rust and Java implementations with advanced load balancing