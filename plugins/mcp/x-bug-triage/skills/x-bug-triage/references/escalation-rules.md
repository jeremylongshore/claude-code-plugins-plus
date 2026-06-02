# Escalation Rules — X Bug Triage Plugin

## Triggers (6)

| Trigger | Threshold |
|---------|-----------|
| Report velocity spike | 50 reports in 30 minutes |
| Data loss language | Keywords: lost, deleted, gone, disappeared, missing conversations |
| Security/privacy language | Keywords: unauthorized, leaked, exposed |
| Auth/billing cascade | 20 reports in 60 minutes |
| Cross-surface failure | 3+ surfaces affected |
| Enterprise blocking | Keywords: enterprise, API-critical, workflow blocked |

## Viral Thread Circuit Breaker
- 500 replies/hour → sample 100, stop processing rest
- Prevents resource exhaustion on viral threads

## Display Rules
- High/critical severity must always expose: why it is severe, consequence vs velocity source
- Low-volume-but-high-consequence is a valid high/critical rating
