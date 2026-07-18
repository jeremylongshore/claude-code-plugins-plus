# Groq Reference Architecture — Layer Diagram

The system splits into an application layer and a Groq service layer. The service
layer is the reusable core this skill builds: a model router that picks the right
model per request, a middleware band (cache, rate guard, metrics, logging, retry),
and a fallback chain that degrades gracefully when the primary model is rate-limited
or erroring.

```
┌──────────────────────────────────────────────────────────────┐
│                     Application Layer                         │
│  Chat UI  │  API Backend  │  Batch Processor  │  Agent       │
└─────┬─────┴──────┬────────┴────────┬──────────┴──────┬───────┘
      │            │                 │                 │
      ▼            ▼                 ▼                 ▼
┌──────────────────────────────────────────────────────────────┐
│                    Groq Service Layer                         │
│  ┌─────────────┐  ┌────────────┐  ┌─────────────────────┐   │
│  │ Model Router │  │ Middleware │  │ Fallback Chain      │   │
│  │             │  │            │  │                     │   │
│  │ speed →     │  │ Cache      │  │ Groq (primary)      │   │
│  │   8b-instant│  │ Rate Guard │  │   ↓ 429/5xx         │   │
│  │ quality →   │  │ Metrics    │  │ Groq (fallback model)│  │
│  │   70b-versa.│  │ Logging    │  │   ↓ still failing    │   │
│  │ vision →    │  │ Retry      │  │ OpenAI (backup)     │   │
│  │   llama-4   │  │            │  │   ↓ also failing     │   │
│  │ audio →     │  │            │  │ Graceful degrade    │   │
│  │   whisper   │  │            │  │                     │   │
│  └─────────────┘  └────────────┘  └─────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## How the layers interact

1. An application-layer caller (chat UI, API backend, batch processor, or agent)
   describes its request in terms of requirements — latency budget, whether it
   needs vision/tools/JSON, cost sensitivity — not a hardcoded model id.
2. The **Model Router** (`selectModel`) maps those requirements to the cheapest
   model that satisfies them: `8b-instant` for latency-critical or cost-sensitive
   paths, `70b-versatile` for tools/JSON quality work, `llama-4-scout` for vision,
   `whisper-large-v3-turbo` for audio.
3. The **Middleware** band wraps every call with an LRU cache (deterministic
   requests only), latency + token metrics, and a pluggable metrics sink.
4. The **Fallback Chain** attempts the primary model, drops to a different model
   in a separate rate-limit pool on 429/5xx, and finally returns a graceful
   degradation payload rather than throwing to the user.
