# OpenRouter Routing Rules -- Examples

## Basic Model Fallback Chain

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Use OpenRouter's native fallback via model list
def chat_with_fallback(prompt: str) -> str:
    """Try claude-3.5-sonnet first, fall back to gpt-4o if unavailable."""
    response = client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        messages=[{"role": "user", "content": prompt}],
        extra_body={
            "route": "fallback",
            "models": [
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4o",
                "openai/gpt-4-turbo",
            ],
        },
    )
    return response.choices[0].message.content
```

## Rule-Based Router

```python
from dataclasses import dataclass
from enum import Enum

class RoutingStrategy(Enum):
    CHEAPEST = "cheapest"
    FASTEST = "fastest"
    MOST_CAPABLE = "most_capable"
    BALANCED = "balanced"


@dataclass
class RoutingRule:
    strategy: RoutingStrategy
    models: list
    max_tokens_threshold: int = 4000


ROUTING_TABLE: dict[RoutingStrategy, list] = {
    RoutingStrategy.CHEAPEST: [
        "anthropic/claude-3-haiku",
        "openai/gpt-4o-mini",
        "mistralai/mistral-7b-instruct",
    ],
    RoutingStrategy.FASTEST: [
        "anthropic/claude-3-haiku",
        "openai/gpt-4o-mini",
    ],
    RoutingStrategy.MOST_CAPABLE: [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o",
    ],
    RoutingStrategy.BALANCED: [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
    ],
}


def select_model(prompt: str, strategy: RoutingStrategy = RoutingStrategy.BALANCED) -> str:
    """Select the primary model based on routing strategy and prompt characteristics."""
    token_estimate = len(prompt.split()) * 1.3

    # Force cheaper model for short, simple queries
    if token_estimate < 200 and strategy == RoutingStrategy.BALANCED:
        return ROUTING_TABLE[RoutingStrategy.CHEAPEST][0]

    models = ROUTING_TABLE[strategy]
    return models[0]  # Primary; fallback handled by extra_body.models


def route_request(prompt: str, strategy: RoutingStrategy = RoutingStrategy.BALANCED) -> str:
    model = select_model(prompt, strategy)
    fallbacks = ROUTING_TABLE[strategy][1:]

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        extra_body={
            "models": [model] + fallbacks,
            "route": "fallback",
        },
    )
    used_model = response.model
    if used_model != model:
        print(f"Fell back from {model} to {used_model}")

    return response.choices[0].message.content
```

## Provider Preference Rules

```python
def chat_prefer_anthropic(prompt: str) -> str:
    """Route to Anthropic providers first, fall back to OpenAI."""
    response = client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        messages=[{"role": "user", "content": prompt}],
        extra_body={
            "provider": {
                "order": ["Anthropic", "OpenAI", "Azure"],
                "allow_fallbacks": True,
            },
        },
    )
    return response.choices[0].message.content


def chat_avoid_provider(prompt: str, avoid: list) -> str:
    """Exclude specific providers from routing."""
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        extra_body={
            "provider": {
                "ignore": avoid,
                "allow_fallbacks": True,
            },
        },
    )
    return response.choices[0].message.content
```

## TypeScript Rule-Based Router

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
    baseURL: 'https://openrouter.ai/api/v1',
    apiKey: process.env.OPENROUTER_API_KEY,
});

type TaskType = 'code' | 'chat' | 'analysis' | 'summary';

const TASK_ROUTES: Record<TaskType, string[]> = {
    code: ['anthropic/claude-3.5-sonnet', 'openai/gpt-4o'],
    chat: ['openai/gpt-4o-mini', 'anthropic/claude-3-haiku'],
    analysis: ['anthropic/claude-3.5-sonnet', 'openai/gpt-4o'],
    summary: ['openai/gpt-4o-mini', 'mistralai/mistral-7b-instruct'],
};

function detectTaskType(prompt: string): TaskType {
    const lower = prompt.toLowerCase();
    if (lower.includes('code') || lower.includes('function') || lower.includes('implement')) {
        return 'code';
    }
    if (lower.includes('summarize') || lower.includes('tldr')) {
        return 'summary';
    }
    if (lower.includes('analyze') || lower.includes('compare')) {
        return 'analysis';
    }
    return 'chat';
}

async function routedChat(prompt: string): Promise<string> {
    const taskType = detectTaskType(prompt);
    const models = TASK_ROUTES[taskType];

    const response = await client.chat.completions.create({
        model: models[0],
        messages: [{ role: 'user', content: prompt }],
        // @ts-ignore -- OpenRouter extension
        models,
        route: 'fallback',
    } as any);

    return response.choices[0].message.content || '';
}
```

## Cost-Aware Dynamic Routing

```python
import urllib.request
import json

def get_model_pricing() -> dict:
    """Fetch current model pricing from OpenRouter."""
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return {
        m["id"]: {
            "prompt_cost": float(m.get("pricing", {}).get("prompt", 0)),
            "completion_cost": float(m.get("pricing", {}).get("completion", 0)),
        }
        for m in data.get("data", [])
    }


def cheapest_capable_model(
    candidate_models: list,
    pricing: dict,
    max_cost_per_1k_tokens: float = 0.01,
) -> str:
    """Return the cheapest model from candidates under the cost threshold."""
    affordable = [
        m for m in candidate_models
        if m in pricing and pricing[m]["prompt_cost"] <= max_cost_per_1k_tokens
    ]
    if not affordable:
        return candidate_models[0]  # Fall back to first regardless of cost
    return sorted(affordable, key=lambda m: pricing[m]["prompt_cost"])[0]
```
