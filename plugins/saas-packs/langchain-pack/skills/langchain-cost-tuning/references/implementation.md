# LangChain Cost Tuning - Detailed Implementation

## Token Pricing Reference

```python
PRICING = {
    "openai": {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    },
    "anthropic": {
        "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    },
}

def estimate_cost(input_tokens, output_tokens, model="gpt-4o-mini"):
    provider, model_name = model.split("/") if "/" in model else ("openai", model)
    rates = PRICING.get(provider, {}).get(model_name, {"input": 0.001, "output": 0.002})
    return (input_tokens / 1000 * rates["input"]) + (output_tokens / 1000 * rates["output"])
```

## Cost Tracking Callback

```python
import tiktoken
from langchain_core.callbacks import BaseCallbackHandler

class CostTrackingCallback(BaseCallbackHandler):
    def __init__(self, model="gpt-4o-mini"):
        self.model = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.requests = 0

    def on_llm_end(self, response, **kwargs):
        if response.llm_output and "token_usage" in response.llm_output:
            usage = response.llm_output["token_usage"]
            self.total_input_tokens += usage.get("prompt_tokens", 0)
            self.total_output_tokens += usage.get("completion_tokens", 0)
            self.requests += 1

    @property
    def total_cost(self):
        return estimate_cost(self.total_input_tokens, self.total_output_tokens, self.model)

    def report(self):
        return {
            "requests": self.requests,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "estimated_cost": f"${self.total_cost:.4f}"
        }
```

## Prompt Optimization

```python
def optimize_prompt(text, max_tokens=2000, model="gpt-4o-mini"):
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    truncated = encoding.decode(tokens[:max_tokens - 10])
    return truncated + "... [truncated]"

def summarize_context(long_text, llm):
    if count_tokens(long_text) < 2000:
        return long_text
    summary_prompt = ChatPromptTemplate.from_template(
        "Summarize this text in 500 words or less, preserving key facts:\n\n{text}"
    )
    chain = summary_prompt | llm | StrOutputParser()
    return chain.invoke({"text": long_text})
```

## Model Tiering Strategy

```python
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableBranch

llm_cheap = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_medium = ChatOpenAI(model="gpt-4o", temperature=0)
llm_powerful = ChatOpenAI(model="o1", temperature=0)

def select_model(input_data):
    task_type = input_data.get("task_type", "simple")
    if task_type in ["chat", "faq", "simple"]:
        return "cheap"
    elif task_type in ["analysis", "summary", "medium"]:
        return "medium"
    return "powerful"

router = RunnableBranch(
    (lambda x: select_model(x) == "cheap", prompt | llm_cheap),
    (lambda x: select_model(x) == "medium", prompt | llm_medium),
    prompt | llm_powerful
)
```

## Semantic Caching

```python
from langchain_core.globals import set_llm_cache
from langchain_community.cache import RedisSemanticCache
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
set_llm_cache(RedisSemanticCache(
    redis_url="redis://localhost:6379",
    embedding=embeddings,
    score_threshold=0.95
))
```

## Budget Limit Callback

```python
from datetime import datetime

class BudgetLimitCallback(BaseCallbackHandler):
    def __init__(self, daily_budget=10.0, model="gpt-4o-mini"):
        self.daily_budget = daily_budget
        self.model = model
        self.daily_spend = 0.0
        self.last_reset = datetime.now().date()

    def on_llm_start(self, serialized, prompts, **kwargs):
        today = datetime.now().date()
        if today != self.last_reset:
            self.daily_spend = 0.0
            self.last_reset = today
        if self.daily_spend >= self.daily_budget:
            raise RuntimeError(f"Daily budget of ${self.daily_budget} exceeded")

    def on_llm_end(self, response, **kwargs):
        if response.llm_output and "token_usage" in response.llm_output:
            usage = response.llm_output["token_usage"]
            cost = estimate_cost(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), self.model)
            self.daily_spend += cost
```

## Cost Optimization Summary

| Strategy | Potential Savings | Implementation Effort |
|----------|-------------------|----------------------|
| Model tiering | 50-100x | Medium |
| Response caching | 50-99% | Low |
| Prompt optimization | 10-50% | Low |
| Semantic caching | 30-70% | Medium |
| Budget limits | Risk mitigation | Low |
