# Few-Shot Selectors — Static, Semantic, MMR, Dynamic

Reference for `langchain-prompt-engineering`. When and how to pick examples
dynamically, how to curate an example corpus, how to avoid leakage between
train and eval, and how to tune MMR lambda.

Pin: `langchain-core 1.0.x`, `langchain-community 1.0.x`,
`langchain-openai 1.0.x` (for embeddings).

## Decision tree

```
How many examples do you have?
├── 3-5 → Static list. Selector overhead not worth it.
├── 50-500 → SemanticSimilarityExampleSelector (FAISS + embeddings). Default.
└── 500+ or changing frequently → SemanticSimilarityExampleSelector backed by
                                  hosted vector store (Pinecone, PGVector).

Are your queries ambiguous or under-specified?
├── No → SemanticSimilarityExampleSelector is fine.
└── Yes → MaxMarginalRelevanceExampleSelector for diverse coverage.

Do you have per-tenant or per-user example corpora?
└── Yes → Build the selector per-request with the tenant's corpus (see
          langchain-embeddings-search P33 for the per-tenant pattern).
```

## Static — hardcoded list

```python
from langchain_core.prompts import FewShotChatMessagePromptTemplate, ChatPromptTemplate

examples = [
    {"question": "What is the total?", "answer": "$1,234.00"},
    {"question": "Who is the vendor?", "answer": "Acme Corp"},
    {"question": "When is it due?", "answer": "2026-05-15"},
]

example_prompt = ChatPromptTemplate.from_messages([
    ("user", "{{ question }}"),
    ("ai", "{{ answer }}"),
])

few_shot = FewShotChatMessagePromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
)
```

Use for fixed, small, well-chosen demonstrations. Reviewers can see all
examples in one screen. Trade-off: the same 3 examples burn tokens on every
call, even when they are irrelevant to the current query.

## Semantic similarity — the default

```python
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    OpenAIEmbeddings(model="text-embedding-3-small"),
    FAISS,
    k=5,  # 3-10 is the sweet spot
    input_keys=["question"],  # which keys to embed against
)
```

**k selection:**
- `k=3` — tight token budget, well-defined tasks
- `k=5` — default for most extraction / classification
- `k=7-10` — open-ended generation, complex domain
- `k > 10` — diminishing returns; invest in better examples instead

**Corpus size:**
- `< 20` — use static instead; embedding overhead dominates
- `50-500` — FAISS in-memory is ideal
- `> 500` — consider a persistent vector store so you don't rebuild on every boot

## MMR — maximal marginal relevance for diverse coverage

`SemanticSimilarityExampleSelector` can return 5 near-duplicates if your corpus
has clusters. MMR balances relevance against diversity:

```python
from langchain_core.example_selectors import MaxMarginalRelevanceExampleSelector

selector = MaxMarginalRelevanceExampleSelector.from_examples(
    examples,
    OpenAIEmbeddings(model="text-embedding-3-small"),
    FAISS,
    k=5,
    fetch_k=20,   # fetch top-20 by similarity, then diversify down to k=5
    lambda_mult=0.5,  # 0 = pure diversity, 1 = pure similarity
    input_keys=["question"],
)
```

**Lambda tuning:**
- `lambda_mult=0.8` — mostly similarity, slight diversity. Good when queries are specific.
- `lambda_mult=0.5` — balanced. Default for ambiguous queries.
- `lambda_mult=0.3` — heavily diverse. Good when the input is a single broad question
  and you want to show the model the range of possible patterns.

**fetch_k** should be 3-5× `k`. Too small → no diversity to choose from.
Too large → embedding cost per query inflates.

## Curating an example corpus

1. **Start from production traces**, not synthetic data. Pull 200-500 real
   queries + known-good outputs from LangSmith. Real distribution.
2. **Tag edge cases explicitly** — rare labels, multi-entity inputs,
   adversarial phrasings. Ensure at least 3 examples per rare label; semantic
   search under-retrieves rare clusters.
3. **Strip PII and secrets** before embedding. The corpus lives in your vector
   store; treat it like any other data surface.
4. **Version the corpus** like prompts — push to a LangSmith dataset,
   pin production to a specific version. When you add 20 new examples, that
   is a new corpus version.

## Preventing eval leakage

If examples from your eval set bleed into the selector's corpus, the selector
will retrieve the exact answer and inflate eval scores. Split before embedding:

```python
from sklearn.model_selection import train_test_split

all_examples = load_curated_examples()  # 300 items
train_examples, eval_examples = train_test_split(
    all_examples,
    test_size=0.2,  # 60 eval, 240 train
    random_state=42,
)
# Selector only sees train; eval harness only uses eval
selector = SemanticSimilarityExampleSelector.from_examples(
    train_examples, OpenAIEmbeddings(...), FAISS, k=5,
)
```

**Enforce the split with an assertion at selector-build time:**

```python
def build_selector(train, eval_set):
    train_ids = {e["id"] for e in train}
    eval_ids = {e["id"] for e in eval_set}
    assert not (train_ids & eval_ids), f"Leakage: {train_ids & eval_ids}"
    return SemanticSimilarityExampleSelector.from_examples(train, ...)
```

## Integration with the Claude XML pattern

Wrap each selected example in `<example>` tags so Claude reads them as
demonstrations, not as concatenated conversation turns:

```python
example_prompt = ChatPromptTemplate.from_messages([
    ("user", "<example><input>{{ question }}</input>"),
    ("ai", "<output>{{ answer }}</output></example>"),
])
```

This also helps with `MessagesPlaceholder("examples")` in the parent
`ChatPromptTemplate` — the examples flow in as conversation pairs but the
XML tags mark them as training demonstrations rather than real prior turns.

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| Retrieved examples all say the same thing | Corpus has clusters; similarity selector picks cluster center 5× | Switch to `MaxMarginalRelevanceExampleSelector` with `lambda_mult=0.5` |
| Eval scores inflated beyond production reality | Eval examples leaked into selector corpus | Enforce the split with an assertion at build time |
| Selector misses rare-label examples | Only 1-2 rare examples in corpus; semantic search favors dense clusters | Add at least 3 examples per rare label; consider a hybrid BM25+semantic selector |
| Token budget blown on few-shot | `k` too high or examples too long | Reduce `k`; shorten examples; summarize them |
| Embedding cost dominates latency | Re-embedding the full corpus on every query | Use `from_examples` once at startup; pass the selector to the template (it caches internally) |

## Sources

- LangChain: Example selectors — https://python.langchain.com/docs/how_to/example_selectors/
- LangChain: Select by similarity — https://python.langchain.com/docs/how_to/example_selectors_similarity/
- LangChain: Select by MMR — https://python.langchain.com/docs/how_to/example_selectors_mmr/
- LangChain: Few-shot chat prompts — https://python.langchain.com/docs/how_to/few_shot_examples_chat/
- Carbonell & Goldstein (1998), "The Use of MMR..." — foundational MMR paper
