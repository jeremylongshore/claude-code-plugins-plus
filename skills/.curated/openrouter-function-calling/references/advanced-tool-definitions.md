# Advanced Tool Definitions

## Advanced Tool Definitions

### Complex Parameters

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search for products in the catalog",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "filters": {
                        "type": "object",
                        "properties": {
                            "min_price": {"type": "number"},
                            "max_price": {"type": "number"},
                            "category": {
                                "type": "string",
                                "enum": ["electronics", "clothing", "home"]
                            },
                            "in_stock": {"type": "boolean"}
                        }
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["relevance", "price_low", "price_high", "rating"]
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }
    }
]
```

### Multiple Tools

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_user",
            "description": "Get user information by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_user",
            "description": "Update user information",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_orders",
            "description": "List orders for a user",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "shipped", "delivered"]
                    },
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["user_id"]
            }
        }
    }
]
```
