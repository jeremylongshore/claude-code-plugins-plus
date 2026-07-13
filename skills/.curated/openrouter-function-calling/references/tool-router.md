# Tool Router

## Tool Router

### Dispatch Tool Calls

```python
class ToolRouter:
    """Route and execute tool calls."""

    def __init__(self):
        self.handlers = {}

    def register(self, name: str, handler: callable):
        """Register a function handler."""
        self.handlers[name] = handler

    def execute(self, tool_call) -> dict:
        """Execute a tool call."""
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        handler = self.handlers.get(function_name)
        if not handler:
            return {"error": f"Unknown function: {function_name}"}

        try:
            result = handler(**arguments)
            return result
        except Exception as e:
            return {"error": str(e)}

    def process_response(self, response) -> list:
        """Process all tool calls in response."""
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            return []

        return [
            {
                "tool_call_id": call.id,
                "role": "tool",
                "content": json.dumps(self.execute(call))
            }
            for call in tool_calls
        ]

# Setup router
router = ToolRouter()
router.register("get_weather", get_weather)
router.register("get_user", lambda user_id: {"id": user_id, "name": "John"})
router.register("list_orders", lambda user_id, **kwargs: [{"id": "1"}])
```
