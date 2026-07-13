# Function Calling Examples

## Python — Complete Tool-Use Loop

```python
import os
import json
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Define available tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the current stock price for a ticker symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol, e.g. 'AAPL'"
                    }
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_portfolio_value",
            "description": "Calculate total value of stock holdings",
            "parameters": {
                "type": "object",
                "properties": {
                    "holdings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string"},
                                "shares": {"type": "number"}
                            }
                        }
                    }
                },
                "required": ["holdings"]
            }
        }
    }
]

# Mock implementations
def get_stock_price(ticker: str) -> dict:
    prices = {"AAPL": 178.50, "GOOGL": 141.25, "MSFT": 378.90}
    return {"ticker": ticker, "price": prices.get(ticker, 0), "currency": "USD"}

def calculate_portfolio_value(holdings: list) -> dict:
    prices = {"AAPL": 178.50, "GOOGL": 141.25, "MSFT": 378.90}
    total = sum(prices.get(h["ticker"], 0) * h["shares"] for h in holdings)
    return {"total_value": total, "currency": "USD"}

FUNCTIONS = {
    "get_stock_price": get_stock_price,
    "calculate_portfolio_value": calculate_portfolio_value,
}

def chat_with_tools(prompt: str) -> str:
    """Run a multi-turn conversation with tool execution."""
    messages = [{"role": "user", "content": prompt}]

    for _ in range(5):  # max iterations to prevent infinite loops
        response = client.chat.completions.create(
            model="openai/gpt-4-turbo",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=500,
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return message.content

        messages.append(message)

        for call in message.tool_calls:
            fn = FUNCTIONS.get(call.function.name)
            args = json.loads(call.function.arguments)
            result = fn(**args) if fn else {"error": "Unknown function"}

            messages.append({
                "tool_call_id": call.id,
                "role": "tool",
                "content": json.dumps(result),
            })

    return "Max tool iterations reached"

# Usage
answer = chat_with_tools(
    "What is the total value of 100 shares of AAPL and 50 shares of GOOGL?"
)
print(answer)
# Output: "Based on current prices, your portfolio is worth $24,912.50
#          (100 × $178.50 for AAPL + 50 × $141.25 for GOOGL)."
```

## cURL — Single Tool Call

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4-turbo",
    "messages": [{"role": "user", "content": "What is the weather in Tokyo?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {"type": "string"}
          },
          "required": ["city"]
        }
      }
    }],
    "tool_choice": "auto"
  }' | jq '.choices[0].message.tool_calls'

# Expected:
# [
#   {
#     "id": "call_abc123",
#     "type": "function",
#     "function": {
#       "name": "get_weather",
#       "arguments": "{\"city\":\"Tokyo\"}"
#     }
#   }
# ]
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
