# recsys-pipeline-architect

Design composable recommendation, ranking, and feed pipelines using the six-stage **Source → Hydrator → Filter → Scorer → Selector → SideEffect** framework popularized by xAI's open-sourced [For You algorithm](https://github.com/xai-org/x-algorithm). Independent MIT reimplementation of the pattern.

## What This Plugin Provides

One auto-activating skill that walks the agent through eight clarifying steps (use case → sources → hydrations → filters → scorers → selector → side effects → scaffold), surfaces the architectural trade-offs (multi-action vs single-score, candidate isolation vs joint scoring, online vs offline batch) explicitly, and emits a runnable scaffold in the user's stack.

## Skill

- **`recsys-pipeline-architect`** — Auto-activates on phrases like "recommendation system", "feed algorithm", "ranking pipeline", "for you feed", "candidate pipeline", "content recommender", "RAG retrieval reranker", or any "top K items for (user, context)" problem statement.

## Upstream

Full skill content (including 5 load-on-demand reference docs and 3 runnable example scaffolds for Strapi v5, Go, and Python/FastAPI — every one green on its test suite) lives at the upstream repository:

https://github.com/mturac/recsys-pipeline-architect

Install upstream directly via skills.sh:

```bash
npx skills add mturac/recsys-pipeline-architect
```

## License

MIT. Pattern source: xAI X For You algorithm (Apache 2.0). See LICENSE.
