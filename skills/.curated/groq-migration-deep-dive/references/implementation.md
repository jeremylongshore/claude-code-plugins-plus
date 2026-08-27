# Groq Migration — Full Implementation

Deep implementation detail for a zero-downtime migration to Groq: the
provider-abstraction layer, feature-flag traffic shifting, the automated
migration scanner, and the rollback procedure. SKILL.md summarizes these;
this file carries the complete, copy-pasteable code.

## Step 3: Provider Abstraction Layer

Build a provider-agnostic layer so you can route to either provider behind a
single interface. This is the foundation that makes zero-downtime traffic
shifting (Step 4) possible.

```typescript
// Build a provider-agnostic layer for zero-downtime migration
interface LLMProvider {
  name: string;
  complete(messages: any[], model: string, maxTokens: number): Promise<{
    content: string;
    model: string;
    tokens: { prompt: number; completion: number; total: number };
  }>;
}

class GroqProvider implements LLMProvider {
  name = "groq";
  private client: Groq;

  constructor() {
    this.client = new Groq();
  }

  async complete(messages: any[], model: string, maxTokens: number) {
    const result = await this.client.chat.completions.create({
      model,
      messages,
      max_tokens: maxTokens,
    });

    return {
      content: result.choices[0].message.content || "",
      model: result.model,
      tokens: {
        prompt: result.usage!.prompt_tokens,
        completion: result.usage!.completion_tokens,
        total: result.usage!.total_tokens,
      },
    };
  }
}

class OpenAIProvider implements LLMProvider {
  name = "openai";
  private client: OpenAI;

  constructor() {
    this.client = new OpenAI();
  }

  async complete(messages: any[], model: string, maxTokens: number) {
    const result = await this.client.chat.completions.create({
      model,
      messages,
      max_tokens: maxTokens,
    });

    return {
      content: result.choices[0].message.content || "",
      model: result.model,
      tokens: {
        prompt: result.usage!.prompt_tokens,
        completion: result.usage!.completion_tokens,
        total: result.usage!.total_tokens,
      },
    };
  }
}
```

## Step 4: Feature Flag Traffic Shifting

With both providers behind the `LLMProvider` interface, shift traffic
gradually by percentage. Start with a small canary, validate quality at each
step, and only remove the old provider once you are at 100%.

```typescript
// Gradually shift traffic from OpenAI to Groq
function getProvider(): LLMProvider {
  const groqPercentage = getFeatureFlag("groq_migration_pct"); // 0-100

  if (Math.random() * 100 < groqPercentage) {
    return new GroqProvider();
  }
  return new OpenAIProvider();
}

// Migration schedule:
// Week 1: groq_migration_pct = 10  (canary)
// Week 2: groq_migration_pct = 50  (validate quality)
// Week 3: groq_migration_pct = 90  (near-complete)
// Week 4: groq_migration_pct = 100 (done, remove OpenAI)
```

## Step 5: Automated Migration Scanner

Run this before you start to size the migration: it counts OpenAI import
sites, lists the model IDs in use, flags OpenAI-only features that Groq does
not implement (embeddings, images, fine-tuning), and finds the API-key
references you will need to update.

```bash
set -euo pipefail
echo "=== Migration Assessment ==="

echo ""
echo "--- OpenAI references ---"
grep -rn "from ['\"]openai['\"]" src/ --include="*.ts" --include="*.js" 2>/dev/null | wc -l
grep -rn "openai\." src/ --include="*.ts" --include="*.js" 2>/dev/null | head -5

echo ""
echo "--- Model IDs to migrate ---"
grep -roh "model.*['\"]gpt-[^'\"]*['\"]" src/ --include="*.ts" --include="*.js" 2>/dev/null | sort -u

echo ""
echo "--- OpenAI-specific features used ---"
grep -rn "\.images\.\|\.audio\.\|\.embeddings\.\|\.moderations\.\|\.files\.\|\.fine_tuning\." \
  src/ --include="*.ts" --include="*.js" 2>/dev/null || echo "None (chat.completions only -- easy migration)"

echo ""
echo "--- API keys to update ---"
grep -rn "OPENAI_API_KEY" src/ .env* --include="*.ts" --include="*.js" --include=".env*" 2>/dev/null | wc -l
```

## Rollback Plan

The whole point of the feature-flag design is a one-line rollback: set
`groq_migration_pct = 0` and every request returns to OpenAI immediately —
no redeploy required.

```bash
set -euo pipefail
# Immediate rollback: flip feature flag
# groq_migration_pct = 0

# Verify:
# - All requests routing to OpenAI
# - Error rates returned to baseline
# - No Groq API calls in logs
```
