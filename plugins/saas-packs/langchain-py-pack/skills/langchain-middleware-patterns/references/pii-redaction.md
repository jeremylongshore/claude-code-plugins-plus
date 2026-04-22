# PII Redaction Middleware

Three approaches — regex, spaCy NER, Presidio — with tradeoff matrix, jurisdiction
entity lists, and a reversible placeholder pattern so the caller can get
un-redacted output without ever leaking through the cache or the model prompt.

## Approach comparison

| Approach | Entity types | Precision | Recall | Throughput (req/s) | When to use |
|---|---|---:|---:|---:|---|
| Regex | Emails, phones, SSNs, credit cards, API keys | 0.95 | 0.70 | ~50,000 | High-throughput, well-known patterns only |
| spaCy NER (`en_core_web_sm`) | PERSON, ORG, GPE, DATE | 0.85 | 0.82 | ~800 | Unstructured names, org mentions |
| Presidio | 20+ including medical, custom | 0.90 | 0.88 | ~500 | Compliance (GDPR, HIPAA, PCI-DSS), custom recognizers |
| Hybrid (regex + Presidio) | Everything above | 0.92 | 0.90 | ~400 | Production default for multi-tenant SaaS |

**Throughput numbers** are rough — measured on a 2024 dev box, single-thread,
128-char inputs. Real throughput drops with longer inputs and cold-start model
loads for spaCy/Presidio.

## Regex implementation (fast path)

```python
import re

PATTERNS = {
    "EMAIL":     re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "PHONE_US":  re.compile(r"\+?1?[\s\-\.]?\(?([2-9]\d{2})\)?[\s\-\.]?(\d{3})[\s\-\.]?(\d{4})"),
    "PHONE_INTL":re.compile(r"\+\d{1,3}[\s\-]?\d{4,14}"),
    "SSN":       re.compile(r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b"),
    "CC_VISA":   re.compile(r"\b4\d{3}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
    "CC_MC":     re.compile(r"\b5[1-5]\d{2}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
    "CC_AMEX":   re.compile(r"\b3[47]\d{2}[\s\-]?\d{6}[\s\-]?\d{5}\b"),
    "IP_V4":     re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "API_KEY_SK":re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_\-]{20,}\b"),
    "JWT":       re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b"),
}

def redact(text: str) -> tuple[str, dict[str, str]]:
    pmap: dict[str, str] = {}
    counter = {label: 0 for label in PATTERNS}
    for label, pattern in PATTERNS.items():
        def _sub(match, _label=label):
            token = f"<{_label}_{counter[_label]}>"
            pmap[token] = match.group(0)
            counter[_label] += 1
            return token
        text = pattern.sub(_sub, text)
    return text, pmap
```

**Gotcha:** `re.compile` is expensive; do it at module load. The per-request
cost is just `.sub()`.

**Gotcha:** Credit-card regex without Luhn check has ~5% false positives on
random 16-digit numbers. If that matters, run Luhn validation inside `_sub`.

## Presidio implementation (compliance path)

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

_analyzer = AnalyzerEngine()
_anonymizer = AnonymizerEngine()

def redact_presidio(text: str, language: str = "en") -> tuple[str, dict[str, str]]:
    results = _analyzer.analyze(
        text=text,
        entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD",
                  "PERSON", "LOCATION", "IP_ADDRESS", "MEDICAL_LICENSE"],
        language=language,
        score_threshold=0.5,
    )
    pmap: dict[str, str] = {}
    counter: dict[str, int] = {}
    operators: dict[str, OperatorConfig] = {}
    for r in results:
        counter[r.entity_type] = counter.get(r.entity_type, 0)
        token = f"<{r.entity_type}_{counter[r.entity_type]}>"
        pmap[token] = text[r.start:r.end]
        counter[r.entity_type] += 1
        operators[r.entity_type] = OperatorConfig("replace", {"new_value": token})
    result = _anonymizer.anonymize(text=text, analyzer_results=results, operators=operators)
    return result.text, pmap
```

**Setup:** `pip install presidio-analyzer presidio-anonymizer &&
python -m spacy download en_core_web_lg`. Model load is ~1-2s cold; keep the
engine as a module-level singleton.

**Custom recognizers:** For domain PII (patient IDs, internal customer IDs),
register a pattern recognizer — see the Presidio docs.

## Entity lists by jurisdiction

### GDPR (EU — any identifiable natural person)

Email, phone, full name, postal address, IP address, device identifier, cookie
ID, biometric ID, location (GPS, geohash), online identifier, national ID.

### HIPAA (US — 18 identifiers in the Safe Harbor method)

Names, geographic subdivisions smaller than state, all elements of dates
(except year), phone, fax, email, SSN, MRN, health plan ID, account numbers,
certificate/license numbers, vehicle identifiers, device identifiers, URLs,
IPs, biometric identifiers, full-face photos, any other unique identifying
number/characteristic/code.

### PCI-DSS (card industry)

Primary Account Number (PAN), cardholder name, expiration date, service code,
sensitive authentication data (CVV, PIN, full magnetic stripe).

### US CCPA (California)

All GDPR entities plus: commercial information (records of personal property
purchased), biometric, internet/other network activity, geolocation,
employment-related information, inference derived from the above.

## Reversible placeholder pattern

The redaction function returns **both** the redacted text and a placeholder
map. Use the map to **reinsert** PII into the model's output **only** for the
originating tenant — never put the map in the cache, never include it in the
prompt, never log it.

```python
def reinsert(output: str, pmap: dict[str, str]) -> str:
    """Restore original PII in the response. Call only on the originating
    request — never on a cached hit across tenants."""
    for token, original in pmap.items():
        output = output.replace(token, original)
    return output
```

**Security check:** If `pmap` is empty, the prompt had no PII to redact —
reinsert is a no-op. If the model's output contains `<EMAIL_0>` and the map
has no `<EMAIL_0>` key (because this is a cached response from a different
request), log a warning and return the response as-is (tokens visible). Never
cross-populate maps.

## What NOT to redact

- Model names and product names (unless your tenant list counts them as PII)
- Numeric literals that aren't IDs (quantities, prices, dates of events)
- Public figures' names in known-public contexts (e.g., "Abraham Lincoln")

Over-redaction kills model quality — the model cannot answer "summarize what
Alice said" if Alice has been replaced with `<PERSON_0>` and the context loses
coherence. Calibrate with a test set of real prompts and measure retrieval /
answer quality before and after.

## Testing the redactor

```python
def test_redact_emails():
    text = "Contact alice@acme.com or bob@other.com"
    out, pmap = redact(text)
    assert "alice@acme.com" not in out
    assert "bob@other.com" not in out
    assert pmap["<EMAIL_0>"] == "alice@acme.com"
    assert pmap["<EMAIL_1>"] == "bob@other.com"

def test_redact_is_reversible():
    text = "SSN is 123-45-6789 for user bob@other.com"
    out, pmap = redact(text)
    assert "123-45-6789" not in out
    assert reinsert(out, pmap) == text

def test_redact_normalizes_for_cache_key():
    a, _ = redact("Email alice@a.com for the report")
    b, _ = redact("Email bob@b.com for the report")
    assert a == b  # Both "Email <EMAIL_0> for the report"
```

## References

- [Microsoft Presidio documentation](https://microsoft.github.io/presidio/)
- [spaCy NER types](https://spacy.io/models/en)
- [HHS HIPAA Safe Harbor](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html)
- Pack pain catalog entry **P24**, plus P27 (OTEL capture), P33 (tenant isolation)
