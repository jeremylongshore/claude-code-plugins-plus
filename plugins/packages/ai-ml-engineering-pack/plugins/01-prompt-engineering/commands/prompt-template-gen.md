---
name: prompt-template-gen
description: >
  Generate reusable prompt templates with variables and best practices
shortcut: ptg
category: other
type: command
version: 1.0.0
author: Jeremy Longshore
estimated_time: 2-5 minutes
---
# Prompt Template Generator

Generate production-ready prompt templates with variable substitution, type validation, and optimization best practices built-in.

## What You'll Get

When you run this command, you'll receive:

1. **Prompt template** with variable placeholders
2. **Python implementation** with type hints and validation
3. **TypeScript implementation** for Node.js projects
4. **Usage examples** showing how to use the template
5. **Testing utilities** for quality validation
6. **Cost estimation** based on expected token usage

## Usage

```
/prompt-template-gen <task_description>
```

**Examples:**
- `/ptg "Generate product descriptions from features"`
- `/ptg "Extract structured data from customer reviews"`
- `/ptg "Classify support tickets by urgency and category"`
- `/ptg "Summarize meeting notes with action items"`

## Generated Output

### Example: Product Description Generator

**Input:**
```
/ptg "Generate product descriptions from features"
```

**Output:**

#### 1. Prompt Template

```python
PRODUCT_DESCRIPTION_TEMPLATE = """Generate an engaging product description for e-commerce.

Product Name: {product_name}
Category: {category}
Features: {features}
Target Audience: {target_audience}

Style: {tone}
Length: {word_count} words

Focus on benefits, not just features. Use persuasive language appropriate for {target_audience}.

Output format: Single paragraph, {word_count} words, no bullet points.
"""
```

#### 2. Python Implementation

```python
from typing import Literal, Optional
from dataclasses import dataclass
import anthropic

@dataclass
class ProductDescriptionInput:
    """Type-safe input for product description generation."""
    product_name: str
    category: str
    features: list[str]
    target_audience: str
    tone: Literal["professional", "casual", "enthusiastic", "luxury"] = "professional"
    word_count: int = 150

    def __post_init__(self):
        """Validate inputs."""
        if not self.product_name:
            raise ValueError("product_name cannot be empty")
        if len(self.features) == 0:
            raise ValueError("features must contain at least one item")
        if self.word_count < 50 or self.word_count > 500:
            raise ValueError("word_count must be between 50 and 500")

class ProductDescriptionGenerator:
    """Generate product descriptions using LLM."""

    TEMPLATE = """Generate an engaging product description for e-commerce.

Product Name: {product_name}
Category: {category}
Features: {features}
Target Audience: {target_audience}

Style: {tone}
Length: {word_count} words

Focus on benefits, not just features. Use persuasive language appropriate for {target_audience}.

Output format: Single paragraph, {word_count} words, no bullet points."""

    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        """Initialize with API key and model selection.

        Args:
            api_key: Anthropic API key
            model: Model to use (haiku for cost, sonnet for quality)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate(self, input_data: ProductDescriptionInput) -> dict:
        """Generate product description.

        Args:
            input_data: Validated product information

        Returns:
            dict with 'description', 'tokens_used', 'cost'
        """
        # Format prompt
        prompt = self.TEMPLATE.format(
            product_name=input_data.product_name,
            category=input_data.category,
            features="\n".join(f"- {f}" for f in input_data.features),
            target_audience=input_data.target_audience,
            tone=input_data.tone,
            word_count=input_data.word_count
        )

        # Call API
        message = self.client.messages.create(
            model=self.model,
            max_tokens=input_data.word_count * 2,  # Token buffer
            messages=[{"role": "user", "content": prompt}]
        )

        # Calculate cost
        cost = self._calculate_cost(message.usage)

        return {
            "description": message.content[0].text,
            "tokens_used": {
                "input": message.usage.input_tokens,
                "output": message.usage.output_tokens
            },
            "cost": cost,
            "model": self.model
        }

    def _calculate_cost(self, usage) -> float:
        """Calculate cost based on model pricing."""
        pricing = {
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075}
        }

        rates = pricing.get(self.model, pricing["claude-3-haiku-20240307"])
        input_cost = (usage.input_tokens / 1000) * rates["input"]
        output_cost = (usage.output_tokens / 1000) * rates["output"]

        return input_cost + output_cost

# Usage example
generator = ProductDescriptionGenerator(api_key="your-api-key")

product_input = ProductDescriptionInput(
    product_name="UltraGrip Pro Gaming Mouse",
    category="Gaming Peripherals",
    features=[
        "16,000 DPI optical sensor",
        "Customizable RGB lighting",
        "8 programmable buttons",
        "Ergonomic design for extended gaming sessions"
    ],
    target_audience="competitive gamers",
    tone="enthusiastic",
    word_count=150
)

result = generator.generate(product_input)
print(f"Description: {result['description']}")
print(f"Cost: ${result['cost']:.4f}")
print(f"Tokens: {result['tokens_used']['input']} in, {result['tokens_used']['output']} out")
```

#### 3. TypeScript Implementation

```typescript
import Anthropic from "@anthropic-ai/sdk";

interface ProductDescriptionInput {
  productName: string;
  category: string;
  features: string[];
  targetAudience: string;
  tone?: "professional" | "casual" | "enthusiastic" | "luxury";
  wordCount?: number;
}

interface GenerationResult {
  description: string;
  tokensUsed: {
    input: number;
    output: number;
  };
  cost: number;
  model: string;
}

class ProductDescriptionGenerator {
  private client: Anthropic;
  private model: string;

  private static readonly TEMPLATE = `Generate an engaging product description for e-commerce.

Product Name: {productName}
Category: {category}
Features: {features}
Target Audience: {targetAudience}

Style: {tone}
Length: {wordCount} words

Focus on benefits, not just features. Use persuasive language appropriate for {targetAudience}.

Output format: Single paragraph, {wordCount} words, no bullet points.`;

  constructor(apiKey: string, model: string = "claude-3-haiku-20240307") {
    this.client = new Anthropic({ apiKey });
    this.model = model;
  }

  async generate(input: ProductDescriptionInput): Promise<GenerationResult> {
    // Validate input
    this.validateInput(input);

    // Format prompt
    const prompt = this.formatPrompt(input);

    // Call API
    const message = await this.client.messages.create({
      model: this.model,
      max_tokens: (input.wordCount || 150) * 2,
      messages: [{ role: "user", content: prompt }],
    });

    // Calculate cost
    const cost = this.calculateCost(message.usage);

    return {
      description: message.content[0].text,
      tokensUsed: {
        input: message.usage.input_tokens,
        output: message.usage.output_tokens,
      },
      cost,
      model: this.model,
    };
  }

  private validateInput(input: ProductDescriptionInput): void {
    if (!input.productName) {
      throw new Error("productName is required");
    }
    if (!input.features || input.features.length === 0) {
      throw new Error("features must contain at least one item");
    }
    const wordCount = input.wordCount || 150;
    if (wordCount < 50 || wordCount > 500) {
      throw new Error("wordCount must be between 50 and 500");
    }
  }

  private formatPrompt(input: ProductDescriptionInput): string {
    const tone = input.tone || "professional";
    const wordCount = input.wordCount || 150;
    const features = input.features.map((f) => `- ${f}`).join("\n");

    return ProductDescriptionGenerator.TEMPLATE
      .replace("{productName}", input.productName)
      .replace("{category}", input.category)
      .replace("{features}", features)
      .replace("{targetAudience}", input.targetAudience)
      .replace("{tone}", tone)
      .replace("{wordCount}", wordCount.toString())
      .replace("{targetAudience}", input.targetAudience)
      .replace("{wordCount}", wordCount.toString());
  }

  private calculateCost(usage: { input_tokens: number; output_tokens: number }): number {
    const pricing: Record<string, { input: number; output: number }> = {
      "claude-3-haiku-20240307": { input: 0.00025, output: 0.00125 },
      "claude-3-sonnet-20240229": { input: 0.003, output: 0.015 },
      "claude-3-opus-20240229": { input: 0.015, output: 0.075 },
    };

    const rates = pricing[this.model] || pricing["claude-3-haiku-20240307"];
    const inputCost = (usage.input_tokens / 1000) * rates.input;
    const outputCost = (usage.output_tokens / 1000) * rates.output;

    return inputCost + outputCost;
  }
}

// Usage example
const generator = new ProductDescriptionGenerator("your-api-key");

const result = await generator.generate({
  productName: "UltraGrip Pro Gaming Mouse",
  category: "Gaming Peripherals",
  features: [
    "16,000 DPI optical sensor",
    "Customizable RGB lighting",
    "8 programmable buttons",
    "Ergonomic design for extended gaming sessions",
  ],
  targetAudience: "competitive gamers",
  tone: "enthusiastic",
  wordCount: 150,
});

console.log(`Description: ${result.description}`);
console.log(`Cost: $${result.cost.toFixed(4)}`);
console.log(`Tokens: ${result.tokensUsed.input} in, ${result.tokensUsed.output} out`);
```

#### 4. Testing Framework

```python
import pytest
from product_description_generator import ProductDescriptionGenerator, ProductDescriptionInput

class TestProductDescriptionGenerator:
    """Test suite for product description generator."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return ProductDescriptionGenerator(
            api_key="test-key",
            model="claude-3-haiku-20240307"
        )

    def test_valid_input(self, generator):
        """Test generation with valid input."""
        input_data = ProductDescriptionInput(
            product_name="Test Product",
            category="Test Category",
            features=["Feature 1", "Feature 2"],
            target_audience="test users",
            tone="professional",
            word_count=100
        )

        result = generator.generate(input_data)

        assert "description" in result
        assert result["tokens_used"]["input"] > 0
        assert result["tokens_used"]["output"] > 0
        assert result["cost"] > 0

    def test_invalid_product_name(self):
        """Test validation of empty product name."""
        with pytest.raises(ValueError, match="product_name cannot be empty"):
            ProductDescriptionInput(
                product_name="",
                category="Test",
                features=["Feature 1"],
                target_audience="users"
            )

    def test_invalid_features(self):
        """Test validation of empty features."""
        with pytest.raises(ValueError, match="features must contain at least one item"):
            ProductDescriptionInput(
                product_name="Product",
                category="Test",
                features=[],
                target_audience="users"
            )

    def test_invalid_word_count(self):
        """Test validation of word count range."""
        with pytest.raises(ValueError, match="word_count must be between 50 and 500"):
            ProductDescriptionInput(
                product_name="Product",
                category="Test",
                features=["Feature"],
                target_audience="users",
                word_count=1000  # Too high
            )

    def test_cost_calculation(self, generator):
        """Test cost calculation accuracy."""
        class MockUsage:
            input_tokens = 100
            output_tokens = 150

        cost = generator._calculate_cost(MockUsage())

        expected_cost = (100 / 1000 * 0.00025) + (150 / 1000 * 0.00125)
        assert abs(cost - expected_cost) < 0.0001

# Run tests
# pytest test_product_description_generator.py -v
```

#### 5. Cost Estimation

```python
def estimate_monthly_cost(
    requests_per_month: int,
    avg_word_count: int = 150,
    model: str = "claude-3-haiku-20240307"
):
    """Estimate monthly LLM costs for product descriptions.

    Args:
        requests_per_month: Expected API calls per month
        avg_word_count: Average description length
        model: Claude model to use

    Returns:
        dict with cost breakdown
    """
    # Approximate token counts
    avg_input_tokens = 150  # Template + product info
    avg_output_tokens = avg_word_count * 1.3  # Words to tokens ratio

    pricing = {
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075}
    }

    rates = pricing[model]

    input_cost = (requests_per_month * avg_input_tokens / 1000) * rates["input"]
    output_cost = (requests_per_month * avg_output_tokens / 1000) * rates["output"]
    total_cost = input_cost + output_cost

    return {
        "model": model,
        "requests_per_month": requests_per_month,
        "estimated_monthly_cost": total_cost,
        "cost_per_request": total_cost / requests_per_month,
        "input_cost": input_cost,
        "output_cost": output_cost
    }

# Example scenarios
print("Cost Estimates:")
print("\nScenario 1: Small e-commerce (1,000 products/month)")
print(estimate_monthly_cost(1000, model="claude-3-haiku-20240307"))
# Result: ~$0.28/month with Haiku

print("\nScenario 2: Medium e-commerce (10,000 products/month)")
print(estimate_monthly_cost(10000, model="claude-3-haiku-20240307"))
# Result: ~$2.81/month with Haiku

print("\nScenario 3: Large e-commerce (100,000 products/month)")
print(estimate_monthly_cost(100000, model="claude-3-haiku-20240307"))
# Result: ~$28.13/month with Haiku
```

#### 6. Optimization Tips

```python
# Tip 1: Batch processing for better throughput
async def batch_generate(generator, products: list[ProductDescriptionInput]):
    """Generate descriptions for multiple products efficiently."""
    import asyncio

    tasks = [generator.generate(product) for product in products]
    results = await asyncio.gather(*tasks)
    return results

# Tip 2: Caching for similar products
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_cached_description(product_hash: str):
    """Cache descriptions for identical products."""
    # Implementation...
    pass

# Tip 3: Fallback to cheaper model
def generate_with_fallback(input_data):
    """Try Haiku first, fall back to Sonnet if quality is poor."""
    try:
        result = generator_haiku.generate(input_data)
        if quality_check(result["description"]) > 0.8:
            return result
        else:
            return generator_sonnet.generate(input_data)
    except Exception:
        return generator_sonnet.generate(input_data)
```

## Template Variations

The command can generate templates for common tasks:

### Classification Template
```
/ptg "Classify customer support tickets by urgency and category"
```

### Extraction Template
```
/ptg "Extract structured contact information from business cards"
```

### Summarization Template
```
/ptg "Summarize academic papers with key findings and methodology"
```

### Analysis Template
```
/ptg "Analyze customer sentiment from product reviews"
```

### Translation Template
```
/ptg "Translate marketing copy while preserving tone and cultural context"
```

## Best Practices Built-In

Every generated template includes:

1. **Type Safety:** Strong typing in both Python and TypeScript
2. **Input Validation:** Catch errors before API calls
3. **Cost Tracking:** Monitor spending per request
4. **Error Handling:** Graceful failure and retries
5. **Testing:** Unit tests for reliability
6. **Documentation:** Clear usage examples
7. **Optimization:** Model selection guidance

## When to Use

Use this command when you:
- Need a repeatable LLM task (hundreds+ times)
- Want production-ready code, not one-off scripts
- Care about cost optimization
- Need type safety and validation
- Want testing infrastructure included

## Time Savings

**Manual approach:** 2-4 hours
- Write prompt
- Implement API calls
- Add error handling
- Create tests
- Optimize costs

**With this command:** 2-5 minutes
- Describe task
- Get production-ready code
- Copy and customize

**ROI:** 24-48x time multiplier

---

**Next Steps:**
1. Run `/ptg "<your task description>"`
2. Copy generated code to your project
3. Install dependencies (`pip install anthropic` or `npm install @anthropic-ai/sdk`)
4. Add your API key
5. Test with sample data
6. Deploy to production

**Estimated cost per use:** $0.001 - $0.01 depending on model and task complexity.
