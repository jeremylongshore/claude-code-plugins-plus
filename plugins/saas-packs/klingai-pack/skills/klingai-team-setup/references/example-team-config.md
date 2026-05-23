# Example Team Config

## Example Team Config

```json
{
  "organization_id": "org_abc123",
  "organization_name": "Acme Video Productions",
  "admin_email": "admin@acme.com",
  "global_monthly_limit": 50000,
  "members": [
    {
      "id": "usr_001",
      "email": "admin@acme.com",
      "name": "Alice Admin",
      "role": "admin",
      "projects": [],
      "monthly_limit": null
    },
    {
      "id": "usr_002",
      "email": "bob@acme.com",
      "name": "Bob Developer",
      "role": "developer",
      "projects": ["proj_marketing", "proj_product"],
      "monthly_limit": 5000
    },
    {
      "id": "usr_003",
      "email": "carol@acme.com",
      "name": "Carol Manager",
      "role": "manager",
      "projects": ["proj_marketing"],
      "monthly_limit": 10000
    }
  ],
  "projects": [
    {
      "id": "proj_marketing",
      "name": "Marketing Videos",
      "description": "Promotional and advertising content",
      "api_key": "klingai_proj_marketing_key",
      "members": ["usr_002", "usr_003"],
      "monthly_budget": 20000
    },
    {
      "id": "proj_product",
      "name": "Product Demos",
      "description": "Product demonstration videos",
      "api_key": "klingai_proj_product_key",
      "members": ["usr_002"],
      "monthly_budget": 10000
    }
  ]
}
```
