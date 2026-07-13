# Insecure-Deserialization Theory

## Why deserialization is RCE

Most serialization formats are structural (JSON: numbers, strings,
lists, dicts; XML: a tagged tree). They describe data shape, not
behavior. Deserializing them is a parse step: validate, build value
trees, return.

A small subset of formats is BEHAVIORAL. Python pickle, Java
serialization, PHP unserialize, .NET BinaryFormatter all store
not just object state but the type information AND any
deserialization callbacks the type registered. Re-creating the
object during deserialization invokes those callbacks.

The attack: craft a serialized payload that describes an object
graph using types whose deserialization callbacks execute
arbitrary code. The application calls `pickle.loads(payload)` and
the constructor / `__reduce__` / `readObject` chain runs the
attacker's code IN the application's process.

This is not theoretical. There are public gadget-chain libraries
for every language with behavioral deserialization:

- Java: `ysoserial` (Spring, Commons Collections, Hibernate gadgets)
- .NET: `ysoserial.net` (TypeConfuseDelegate, ObjectDataProvider)
- Python: pickle is trivially exploitable via `__reduce__` returning `(eval, ('...code...',))`
- PHP: PHPGGC (PHP Generic Gadget Chains library)
- Ruby: Marshal exploitation via `_load` callbacks

If your application accepts any of these formats from any source
not under your direct control, you have a deserialization RCE
unless and until you switch formats.

## The "trusted source" trap

A common defense: "we only deserialize from a trusted source —
this database we control, this S3 bucket we own, etc."

Two problems:

1. **The "trusted source" is often less trusted than assumed.**
   The database might be writable by other services. The S3 bucket
   might be world-readable by accident (see skill #9). An attacker
   who reaches the storage layer (via SQL injection, IAM
   misconfiguration, supply-chain compromise) can plant a payload
   that the deserializer later picks up.

2. **The format is brittle even without attackers.** Pickle and
   Java serialization are not stable across language version
   changes; an upgrade can break deserialization of stored data.
   Switching to schema-validated JSON / Protobuf eliminates both
   the security and stability concerns.

The pragmatic posture: assume any deserialization input could
become attacker-controlled through some future change. Use safe
formats by default.

## Safe alternatives by use case

### Use case: "I need to store structured data and reload it"

→ JSON (with Pydantic, dataclasses, or msgspec for schema
validation). Or Protocol Buffers / Avro / MessagePack for binary
efficiency.

### Use case: "I need to round-trip arbitrary Python / Java / .NET objects"

→ Define a schema. If the data is genuinely polymorphic, use a
tagged-union pattern with explicit discriminator field. Validate
the discriminator against an allow-list before instantiating any
class.

```python
# JSON with explicit type discriminator + allow-list
TYPE_REGISTRY = {
    "User": User,
    "Order": Order,
    "Payment": Payment,
}
def deserialize(data: dict):
    type_name = data["__type"]
    if type_name not in TYPE_REGISTRY:
        raise ValueError(f"Unknown type: {type_name}")
    cls = TYPE_REGISTRY[type_name]
    return cls(**{k: v for k, v in data.items() if k != "__type"})
```

### Use case: "I have a binary cache file I trust"

→ HMAC-sign the file when writing; verify HMAC before
deserializing. The HMAC step proves the file wasn't tampered with
since you wrote it. Then deserialize.

```python
import hmac, hashlib, pickle

def write_signed(path, obj, key):
    payload = pickle.dumps(obj)
    sig = hmac.new(key, payload, hashlib.sha256).digest()
    with open(path, "wb") as f:
        f.write(sig + payload)

def read_signed(path, key):
    with open(path, "rb") as f:
        data = f.read()
    sig, payload = data[:32], data[32:]
    expected = hmac.new(key, payload, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        raise ValueError("HMAC mismatch")
    return pickle.loads(payload)  # safe because HMAC verified
```

This works only if the HMAC key is genuinely private. Once the
key is compromised, the protection is gone.

### Use case: "I need to deserialize YAML config"

→ Use the safe-load mode of your YAML library. Python's PyYAML
has `yaml.safe_load()`; Ruby Psych 4.0+ defaults to safe mode;
SnakeYAML (Java) supports `SafeConstructor`. These restrict
deserialization to basic types (strings, numbers, lists, dicts)
and refuse to instantiate arbitrary classes.

## Language-specific notes

### Python pickle

`pickle.loads(b)` on attacker-controlled bytes is roughly equivalent
to `exec()` on attacker-controlled code. There is no "safer pickle"
mode. Migrate to JSON / msgpack / pydantic-validated formats.

If you absolutely must keep pickle for round-tripping:

- HMAC-sign with a private key (see above)
- Restrict to in-process / same-machine usage; never accept pickle
  from a network input
- Use `pickletools.dis()` to verify payloads conform to expected
  opcodes (still not safe, just slightly harder to abuse)

### Java ObjectInputStream

Use Jackson with type-allow-list. For legacy code that must keep
`ObjectInputStream`:

```java
public class AllowlistedObjectInputStream extends ObjectInputStream {
    private static final Set<String> ALLOWED = Set.of(
        "com.example.User", "com.example.Order"
    );
    @Override
    protected Class<?> resolveClass(ObjectStreamClass desc) throws IOException, ClassNotFoundException {
        if (!ALLOWED.contains(desc.getName())) {
            throw new InvalidClassException("Not allowed: " + desc.getName());
        }
        return super.resolveClass(desc);
    }
}
```

### PHP unserialize

`unserialize($input, ["allowed_classes" => false])` restricts to
basic types (PHP 7+). For class-bearing payloads, use the array
form: `["allowed_classes" => ["User", "Order"]]`.

But the better answer is to switch to `json_decode` if the data
shape allows.

### .NET BinaryFormatter

BinaryFormatter is deprecated in .NET 7+ and slated for removal.
Migrate to `System.Text.Json` for general-purpose serialization,
or `MessagePack-CSharp` for performance. The migration is
straightforward in most codebases; the only friction is
round-tripping types BinaryFormatter handles implicitly that
require explicit converter registration in System.Text.Json.

## Gadget chain references

These are educational, not for use on production systems you
don't own:

- `ysoserial` — Java
- `ysoserial.net` — .NET
- `PHPGGC` — PHP
- Anthony Sotirov's pickle-exploit primers

Knowing the gadget-chain shape is useful for understanding the
risk; the operational answer is still "don't use unsafe
deserialization formats."

## Primary sources

- [CWE-502 Deserialization of Untrusted Data](https://cwe.mitre.org/data/definitions/502.html)
- [OWASP A08:2021 Software and Data Integrity Failures](https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/)
- [OWASP Deserialization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html)
- [Python pickle security docs](https://docs.python.org/3/library/pickle.html#restricting-globals)
- [Microsoft BinaryFormatter deprecation](https://learn.microsoft.com/en-us/dotnet/standard/serialization/binaryformatter-security-guide)
