# Routing Rules — X Bug Triage Plugin

## Precedence (strict order)

1. **Service owner** — active ownership metadata (confidence: 1.0)
2. **Oncall** — current oncall/escalation (confidence: 0.9)
3. **CODEOWNERS** — file analysis (confidence: 0.8)
4. **Recent assignees** — last 30 days (confidence: 0.6)
5. **Recent committers** — last 14 days for affected paths (confidence: 0.5)
6. **Fallback mapping** — static config (confidence: 0.3)

## Rules
- Weaker sources never silently overrule stronger
- Staleness: >30 days flagged, reduced confidence
- All fail → "Routing: uncertain — no routing signals available. Manual assignment required."
- Override from prior runs takes precedence
