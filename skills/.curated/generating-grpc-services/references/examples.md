# gRPC Service Generation Examples

## Protocol Buffer Definition

```protobuf
// proto/user_service.proto
syntax = "proto3";

package user.v1;

import "google/protobuf/timestamp.proto";
import "google/protobuf/field_mask.proto";

service UserService {
  rpc CreateUser(CreateUserRequest) returns (User);
  rpc GetUser(GetUserRequest) returns (User);
  rpc ListUsers(ListUsersRequest) returns (stream User);  // Server streaming
  rpc UpdateUser(UpdateUserRequest) returns (User);
  rpc DeleteUser(DeleteUserRequest) returns (DeleteUserResponse);
}

message User {
  string id = 1;
  string first_name = 2;
  string last_name = 3;
  string email = 4;
  UserStatus status = 5;
  google.protobuf.Timestamp created_at = 6;
}

message CreateUserRequest {
  string first_name = 1;
  string last_name = 2;
  string email = 3;
}

message GetUserRequest {
  string id = 1;
}

message ListUsersRequest {
  int32 page_size = 1;
  string page_token = 2;
}

message UpdateUserRequest {
  string id = 1;
  User user = 2;
  google.protobuf.FieldMask update_mask = 3;
}

message DeleteUserRequest {
  string id = 1;
}

message DeleteUserResponse {}

enum UserStatus {
  USER_STATUS_UNSPECIFIED = 0;
  USER_STATUS_ACTIVE = 1;
  USER_STATUS_INACTIVE = 2;
  USER_STATUS_SUSPENDED = 3;
}
```

## Generate Stubs

```bash
# Install tools
npm install @grpc/grpc-js @grpc/proto-loader

# Generate with buf
buf generate proto/

# Or with protoc directly
protoc --js_out=import_style=commonjs:generated \
       --grpc_out=generated \
       --plugin=protoc-gen-grpc=$(which grpc_node_plugin) \
       proto/user_service.proto

# Python
python -m grpc_tools.protoc -I proto \
  --python_out=generated --grpc_python_out=generated \
  proto/user_service.proto
```

## Node.js Server Implementation

```javascript
// src/services/user-service.js
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');

const packageDef = protoLoader.loadSync('proto/user_service.proto', {
  keepCase: true, longs: String, enums: String, defaults: true,
});
const proto = grpc.loadPackageDefinition(packageDef).user.v1;

const userService = {
  async CreateUser(call, callback) {
    const { first_name, last_name, email } = call.request;
    try {
      const user = await db.users.create({ first_name, last_name, email });
      callback(null, toProtoUser(user));
    } catch (err) {
      callback({
        code: grpc.status.INVALID_ARGUMENT,
        message: err.message,
      });
    }
  },

  async GetUser(call, callback) {
    const user = await db.users.findById(call.request.id);
    if (!user) {
      return callback({ code: grpc.status.NOT_FOUND, message: `User ${call.request.id} not found` });
    }
    callback(null, toProtoUser(user));
  },

  ListUsers(call) {  // Server streaming
    const pageSize = call.request.page_size || 20;
    const stream = db.users.streamAll({ batchSize: pageSize });
    stream.on('data', (user) => call.write(toProtoUser(user)));
    stream.on('end', () => call.end());
    stream.on('error', (err) => call.destroy(err));
  },

  async UpdateUser(call, callback) {
    const { id, user, update_mask } = call.request;
    const fields = update_mask?.paths || Object.keys(user);
    const updates = {};
    for (const field of fields) {
      if (user[field] !== undefined) updates[field] = user[field];
    }
    const updated = await db.users.update(id, updates);
    callback(null, toProtoUser(updated));
  },

  async DeleteUser(call, callback) {
    await db.users.destroy(call.request.id);
    callback(null, {});
  },
};

const server = new grpc.Server();
server.addService(proto.UserService.service, userService);
server.bindAsync('0.0.0.0:50051', grpc.ServerCredentials.createInsecure(), () => {
  console.log('gRPC server on :50051');
});
```

## Interceptors (Auth + Logging)

```javascript
// src/interceptors/auth.js
function authInterceptor(call, callback, next) {
  const metadata = call.metadata;
  const token = metadata.get('authorization')[0];

  if (!token) {
    return callback({ code: grpc.status.UNAUTHENTICATED, message: 'Missing authorization' });
  }

  try {
    const user = jwt.verify(token.replace('Bearer ', ''), process.env.JWT_SECRET);
    call.user = user;
    next(call, callback);
  } catch {
    callback({ code: grpc.status.UNAUTHENTICATED, message: 'Invalid token' });
  }
}

// src/interceptors/logging.js
function loggingInterceptor(call, callback, next) {
  const start = Date.now();
  const method = call.getPath();

  const originalCallback = callback;
  callback = (err, response) => {
    logger.info({
      method, durationMs: Date.now() - start,
      status: err ? err.code : 'OK',
      userId: call.user?.id,
    });
    originalCallback(err, response);
  };

  next(call, callback);
}
```

## Health Check Service

```javascript
const health = require('grpc-health-check');
const healthImpl = new health.Implementation({
  'user.v1.UserService': 'SERVING',
});
server.addService(health.service, healthImpl);
```

## gRPC Client (Python)

```python
import grpc
from generated import user_service_pb2, user_service_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = user_service_pb2_grpc.UserServiceStub(channel)

# Create user
user = stub.CreateUser(user_service_pb2.CreateUserRequest(
    first_name="Alice", last_name="Smith", email="alice@example.com"
))
print(f"Created: {user.id}")

# Get user
user = stub.GetUser(user_service_pb2.GetUserRequest(id=user.id))
print(f"Got: {user.first_name} {user.last_name}")

# Stream all users
for user in stub.ListUsers(user_service_pb2.ListUsersRequest(page_size=10)):
    print(f"  {user.id}: {user.email}")
```

## Testing with grpcurl

```bash
# List services
grpcurl -plaintext localhost:50051 list

# Describe service
grpcurl -plaintext localhost:50051 describe user.v1.UserService

# Create user
grpcurl -plaintext -d '{"first_name":"Alice","last_name":"Smith","email":"alice@example.com"}' \
  localhost:50051 user.v1.UserService/CreateUser

# Get user
grpcurl -plaintext -d '{"id":"usr_abc123"}' \
  localhost:50051 user.v1.UserService/GetUser

# Stream users
grpcurl -plaintext -d '{"page_size":5}' \
  localhost:50051 user.v1.UserService/ListUsers

# Health check
grpcurl -plaintext localhost:50051 grpc.health.v1.Health/Check
```

## Integration Tests

```javascript
describe('UserService', () => {
  let client;
  before(() => { client = new proto.UserService('localhost:50051', grpc.credentials.createInsecure()); });

  it('creates and retrieves user', (done) => {
    client.CreateUser({ first_name: 'Test', last_name: 'User', email: 'test@example.com' }, (err, user) => {
      expect(err).toBeNull();
      expect(user.id).toBeDefined();
      client.GetUser({ id: user.id }, (err, found) => {
        expect(found.email).toBe('test@example.com');
        done();
      });
    });
  });

  it('returns NOT_FOUND for missing user', (done) => {
    client.GetUser({ id: 'nonexistent' }, (err) => {
      expect(err.code).toBe(grpc.status.NOT_FOUND);
      done();
    });
  });
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
