# Analytics Api

## Analytics API

### API Access

```bash
# Get usage summary
curl -X GET "https://api.cursor.com/v1/analytics/summary" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }'
```

### Available Endpoints

```
GET /analytics/summary
- Overall usage metrics

GET /analytics/users
- Per-user breakdown

GET /analytics/teams
- Team-level metrics

GET /analytics/features
- Feature adoption data

GET /analytics/costs
- Cost breakdown
```

### Integration Examples

```python
# Python integration
import requests

def get_cursor_analytics(start_date, end_date):
    response = requests.get(
        "https://api.cursor.com/v1/analytics/summary",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={
            "start_date": start_date,
            "end_date": end_date
        }
    )
    return response.json()

# Use in dashboards, reports, etc.
```
