# Data Flow Documentation

## Data Flow Documentation

### Document Data Flows

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────▶│   Your App  │────▶│ OpenRouter  │
│   Input     │     │   Server    │     │   API       │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                    │
                    ┌──────▼──────┐      ┌──────▼──────┐
                    │   Logs      │      │  Provider   │
                    │   (audit)   │      │  (OpenAI,   │
                    └─────────────┘      │  Anthropic) │
                                         └─────────────┘

Data Classification:
- User Input: May contain PII/sensitive data
- Logs: Store hashes only, not content
- Provider: Subject to their data policies
```

### Data Classification

```python
class DataClassification:
    """Classify and handle data appropriately."""

    CLASSIFICATIONS = {
        "public": {
            "can_log": True,
            "can_cache": True,
            "requires_encryption": False
        },
        "internal": {
            "can_log": True,
            "can_cache": True,
            "requires_encryption": True
        },
        "confidential": {
            "can_log": False,  # Hash only
            "can_cache": False,
            "requires_encryption": True
        },
        "restricted": {
            "can_log": False,
            "can_cache": False,
            "requires_encryption": True,
            "requires_approval": True
        }
    }

    def classify_request(self, prompt: str, metadata: dict) -> str:
        """Classify request based on content and metadata."""
        # Check for PII patterns
        if self._contains_pii(prompt):
            return "confidential"

        # Check metadata classification
        if metadata.get("classification"):
            return metadata["classification"]

        # Default to internal
        return "internal"

    def _contains_pii(self, text: str) -> bool:
        patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b\d{3}-\d{2}-\d{4}\b',
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        ]
        return any(re.search(p, text) for p in patterns)

    def get_handling_rules(self, classification: str) -> dict:
        return self.CLASSIFICATIONS.get(classification, self.CLASSIFICATIONS["internal"])
```
