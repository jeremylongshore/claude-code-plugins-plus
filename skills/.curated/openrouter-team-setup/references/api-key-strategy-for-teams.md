# Api Key Strategy For Teams

## API Key Strategy for Teams

### Separate Keys Per Environment

```
Development:
  Key: sk-or-dev-xxx
  Label: "Development"
  Limit: $10.00

Staging:
  Key: sk-or-stg-xxx
  Label: "Staging"
  Limit: $50.00

Production:
  Key: sk-or-prod-xxx
  Label: "Production"
  Limit: $500.00
```

### Keys Per Team/Service

```
Frontend Team:
  Key: sk-or-frontend-xxx
  Label: "Frontend"
  Limit: $100.00

Backend Team:
  Key: sk-or-backend-xxx
  Label: "Backend"
  Limit: $200.00

Data Team:
  Key: sk-or-data-xxx
  Label: "Data Processing"
  Limit: $300.00
```
