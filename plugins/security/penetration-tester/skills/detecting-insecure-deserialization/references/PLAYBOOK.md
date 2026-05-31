# Insecure-Deserialization Remediation Playbook

The universal migration: switch from a behavioral format (pickle,
Java serialization, PHP unserialize, BinaryFormatter) to a
schema-validated structural format (JSON + Pydantic / dataclasses /
Jackson with allow-list / System.Text.Json).

## Python — pickle → JSON / msgpack / pydantic

### Before (Celery task queue with pickle)

```python
# Celery worker
CELERY_TASK_SERIALIZER = 'pickle'  # unsafe
result = pickle.loads(task_payload)
```

### After

```python
# Celery configuration
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
```

### Cache layer migration

```python
# Before
import pickle
data = pickle.loads(redis_client.get(key))

# After (using msgpack for binary efficiency)
import msgpack
data = msgpack.unpackb(redis_client.get(key), raw=False)

# Or JSON if size isn't critical
import json
data = json.loads(redis_client.get(key))
```

### Application-data migration

```python
# Before
class Order:
    def __init__(self, id, items, total): ...
    # Stored via pickle.dumps

# After (Pydantic with strict validation)
from pydantic import BaseModel
class Order(BaseModel):
    id: int
    items: list[str]
    total: float

# Serialize
payload = order.model_dump_json()
# Deserialize with validation
restored = Order.model_validate_json(payload)
```

### YAML migration

```python
# Before
import yaml
data = yaml.load(file_content)  # UNSAFE

# After
data = yaml.safe_load(file_content)  # restricts to basic types
```

If you previously relied on `yaml.load` to instantiate Python
classes from YAML, replace the YAML schema with explicit
construction:

```python
# Before YAML
# !MyClass
# arg1: hello
# arg2: 42

# Before code
import yaml
obj = yaml.load(content)  # auto-constructs MyClass

# After: data-only YAML + explicit constructor
data = yaml.safe_load(content)  # returns plain dict
obj = MyClass(arg1=data['arg1'], arg2=data['arg2'])
```

## Java — ObjectInputStream → Jackson with allow-list

### Before

```java
ObjectInputStream ois = new ObjectInputStream(inputStream);
MyObject obj = (MyObject) ois.readObject();
```

### After (Jackson, type-allow-listed)

```java
import com.fasterxml.jackson.databind.*;
import com.fasterxml.jackson.databind.jsontype.*;

ObjectMapper mapper = new ObjectMapper();
mapper.activateDefaultTyping(
    BasicPolymorphicTypeValidator.builder()
        .allowIfSubType("com.example.")  // your package only
        .build(),
    ObjectMapper.DefaultTyping.NON_FINAL
);
MyObject obj = mapper.readValue(inputStream, MyObject.class);
```

The `BasicPolymorphicTypeValidator` restricts which classes
Jackson will instantiate during deserialization. Without it,
Jackson is roughly as exploitable as ObjectInputStream.

### Legacy ObjectInputStream — minimal safety (last resort)

If you can't migrate from ObjectInputStream immediately:

```java
public class AllowlistedObjectInputStream extends ObjectInputStream {
    private static final Set<String> ALLOWED = Set.of(
        "com.example.User",
        "com.example.Order",
        "java.lang.String",
        "java.util.ArrayList"
    );

    public AllowlistedObjectInputStream(InputStream is) throws IOException {
        super(is);
    }

    @Override
    protected Class<?> resolveClass(ObjectStreamClass desc)
            throws IOException, ClassNotFoundException {
        if (!ALLOWED.contains(desc.getName())) {
            throw new InvalidClassException(
                "Unauthorized deserialization: " + desc.getName());
        }
        return super.resolveClass(desc);
    }
}
```

Use this as transitional protection only; migrate to a schema-
based format ASAP.

## PHP — unserialize → json_decode

### Before

```php
$obj = unserialize($_POST['data']);
```

### After

```php
$obj = json_decode($_POST['data'], true);
// Validate the shape:
if (!is_array($obj) || !isset($obj['id'], $obj['name'])) {
    throw new InvalidArgumentException("Invalid payload");
}
```

### If you must keep unserialize: restrict allowed classes

```php
$obj = unserialize($data, [
    'allowed_classes' => ['User', 'Order', 'OrderItem']
]);
```

In PHP 7.1+, passing `'allowed_classes' => false` restricts to
basic types only (still safer than the default).

## .NET — BinaryFormatter → System.Text.Json

### Before

```csharp
var formatter = new BinaryFormatter();
var obj = (MyClass)formatter.Deserialize(stream);
```

### After (System.Text.Json)

```csharp
using System.Text.Json;
var options = new JsonSerializerOptions {
    PropertyNameCaseInsensitive = true,
};
MyClass obj = JsonSerializer.Deserialize<MyClass>(jsonString, options);
```

### For polymorphic types — explicit type discriminator

```csharp
[JsonDerivedType(typeof(User), "user")]
[JsonDerivedType(typeof(Order), "order")]
public abstract class Entity { }

// Now the JSON looks like {"$type": "user", "id": 1, ...}
// And only the registered subtypes can be instantiated
```

### Avoid:

```csharp
// NEVER do this — re-enables full polymorphic deserialization
new JsonSerializerOptions {
    TypeInfoResolver = new DefaultJsonTypeInfoResolver { ... }
};
```

## Ruby — Marshal → JSON / safe YAML

### Before

```ruby
obj = Marshal.load(data)
```

### After

```ruby
require 'json'
data = JSON.parse(json_str, create_additions: false)  # create_additions: false REQUIRED
```

`create_additions: true` (the default in older Ruby) lets JSON
instantiate arbitrary classes via the `json_create` hook. Set
`create_additions: false` to disable.

### YAML — Psych 4.0+ defaults safe; older versions need explicit

```ruby
# Psych 4.0+ (default since Ruby 3.1)
require 'yaml'
data = YAML.load(content)  # safe by default

# Pre-4.0 explicit safety
data = YAML.safe_load(content, permitted_classes: [Symbol, Date])
```

## Node.js — node-serialize and friends

### Before (using the known-vulnerable node-serialize package)

```javascript
const serialize = require('node-serialize');
const obj = serialize.unserialize(data);  // RCE
```

### After

```javascript
const obj = JSON.parse(data);
// Validate shape with ajv or zod
const schema = z.object({ id: z.number(), name: z.string() });
const validated = schema.parse(obj);
```

### Avoid JSON.parse with reviver containing eval

```javascript
// BAD
const obj = JSON.parse(data, (key, value) => eval(value));

// GOOD
const obj = JSON.parse(data);
```

## HMAC-signed serialization (when migration isn't feasible)

If you must keep pickle / Marshal / unserialize / BinaryFormatter
because of legacy storage that can't be re-encoded, wrap with HMAC
authentication.

```python
import hmac, hashlib, pickle, os

KEY = os.environ["SERIALIZATION_HMAC_KEY"].encode()

def serialize_signed(obj):
    payload = pickle.dumps(obj)
    sig = hmac.new(KEY, payload, hashlib.sha256).digest()
    return sig + payload

def deserialize_signed(data):
    sig, payload = data[:32], data[32:]
    expected = hmac.new(KEY, payload, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        raise ValueError("HMAC verification failed")
    return pickle.loads(payload)
```

The HMAC step proves the payload was created by code that holds
the KEY. Any tampering invalidates the HMAC. Pickle.loads still
runs, but only on payloads that you yourself signed.

This is necessary infrastructure when migrating; it's not a
permanent solution. The KEY is now a high-value target — leak the
key and the deserialization is exploitable again.

## CI integration

```yaml
- name: Insecure-deserialization scan
  run: |
    python3 plugins/security/penetration-tester/skills/detecting-insecure-deserialization/scripts/scan_deserialization.py \
        . --min-severity high --format json --output deser-scan.json
- run: |
    if jq 'length > 0' deser-scan.json | grep -q true; then
      echo "::error::Insecure deserialization detected"
      exit 1
    fi
```

## Verification after remediation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/detecting-insecure-deserialization/scripts/scan_deserialization.py \
    /path/to/repo --min-severity high
```

Expected: exit 0, zero findings.
