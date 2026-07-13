# Compliance Features

## Compliance Features

### Tamper Detection

```python
import hmac

class TamperProofLogger:
    """Audit logger with tamper detection."""

    def __init__(self, secret_key: str, base_logger: AuditLogger):
        self.secret_key = secret_key.encode()
        self.base_logger = base_logger
        self.previous_hash = None

    def _sign_entry(self, entry: dict) -> str:
        """Create HMAC signature of entry."""
        content = json.dumps(entry, sort_keys=True)
        signature = hmac.new(
            self.secret_key,
            content.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def log(self, entry: AuditEntry):
        entry_dict = asdict(entry)

        # Add chain hash for tamper detection
        chain_content = json.dumps(entry_dict, sort_keys=True)
        if self.previous_hash:
            chain_content = self.previous_hash + chain_content

        entry_dict["chain_hash"] = hashlib.sha256(
            chain_content.encode()
        ).hexdigest()
        entry_dict["signature"] = self._sign_entry(entry_dict)

        self.previous_hash = entry_dict["chain_hash"]

        # Write to base logger
        with open(self.base_logger._get_log_file(), 'a') as f:
            f.write(json.dumps(entry_dict) + '\n')

    def verify_chain(self, log_file: str) -> bool:
        """Verify log chain integrity."""
        previous_hash = None

        with open(log_file) as f:
            for line in f:
                entry = json.loads(line)

                # Verify signature
                stored_sig = entry.pop("signature")
                expected_sig = self._sign_entry(entry)
                if stored_sig != expected_sig:
                    return False

                # Verify chain
                stored_chain = entry["chain_hash"]
                entry_copy = {k: v for k, v in entry.items() if k != "chain_hash"}
                chain_content = json.dumps(entry_copy, sort_keys=True)
                if previous_hash:
                    chain_content = previous_hash + chain_content

                expected_chain = hashlib.sha256(
                    chain_content.encode()
                ).hexdigest()

                if stored_chain != expected_chain:
                    return False

                previous_hash = stored_chain

        return True
```

### Export for Compliance

```python
def export_compliance_package(
    log_dir: str,
    output_file: str,
    start_date: str,
    end_date: str
):
    """Export logs for compliance review."""
    logs = query_logs(log_dir, start_date=start_date, end_date=end_date)
    report = generate_audit_report(log_dir)

    package = {
        "export_timestamp": datetime.utcnow().isoformat(),
        "period": {"start": start_date, "end": end_date},
        "summary": report,
        "logs": logs
    }

    with open(output_file, 'w') as f:
        json.dump(package, f, indent=2)

    return output_file
```
