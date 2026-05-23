# Shared Services Setup

## Shared Services Setup

### Central LLM Service

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
security = HTTPBearer()

# User database (in practice, use real auth)
USERS = {
    "token123": {"user_id": "alice", "role": "admin"},
    "token456": {"user_id": "bob", "role": "developer"},
}

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    if token not in USERS:
        raise HTTPException(status_code=401, detail="Invalid token")
    return USERS[token]

@app.post("/chat")
async def chat(
    prompt: str,
    model: str = "anthropic/claude-3.5-sonnet",
    user: dict = Depends(get_current_user)
):
    # Check model access
    allowed = get_allowed_models(user["role"])
    if model not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Model {model} not allowed for your role"
        )

    # Check budget
    if not budget_mgr.can_spend(user["user_id"], 0.01):
        raise HTTPException(status_code=402, detail="Budget exceeded")

    # Make request
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    # Track usage
    tracker.record(user["user_id"], model, response)

    return {"response": response.choices[0].message.content}
```
