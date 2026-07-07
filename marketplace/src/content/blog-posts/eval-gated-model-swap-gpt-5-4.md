---
title: "Shipping gpt-5.4 as One Config Line"
description: "Deploy gpt-5.4 to production as a one-line config with eval-gated rollout. Key finding: report word-ceilings came from the model, not the prompt."
date: "2026-07-03"
tags: ["ai-engineering", "openai", "release-engineering", "testing", "devops"]
featured: false
---
On 2026-07-03, DiagnosticPro shipped gpt-5.4 in production. The structural finding: gpt-4o silently capped reports at ~1,225 words across 36 benchmark runs—no matter the prompt. gpt-5.4 delivers depth. A real stored report came back at 15 sections, 3,393 words.

The rollout was step 2 of a two-axis, independently eval-gated ladder:

**Step 1 (June):** Prompt framework v3.0 (v3-b few-shot exemplar) beat v2.0 18/18 blind. Later corroborated by adding a third model to the grid.

**Step 2 (this day):** Model gpt-5.4. v3-b on gpt-5.4 beat v2.0 9-0-0 on both judges (+44 to +47 points)—the only cross-family-validated model change in RESULTS.md.

The engineering to keep `LLM_MODEL` a pure config switch: OpenAI's newer models reject `max_tokens` and want `max_completion_tokens`; some reasoning models also reject a non-default temperature. The `createChatCompletionAdaptive` function detects the model family, picks the param shape up front, and — if the model still 400s on the token param or the temperature — flips that one param and retries once before giving up.

```js
async function createChatCompletionAdaptive(openai, { model, messages, maxTokens, temperature }) {
  const usesMaxCompletionTokens = /^(gpt-5|o\d)/i.test(model);
  const state = { maxCompletion: usesMaxCompletionTokens, dropTemp: false };
  const build = () => {
    const body = { model, messages };
    if (!state.dropTemp) body.temperature = temperature;
    body[state.maxCompletion ? 'max_completion_tokens' : 'max_tokens'] = maxTokens;
    return body;
  };
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      return await openai.chat.completions.create(build());
    } catch (err) {
      if (err?.status === 400) {
        const msg = String(err?.message).toLowerCase();
        if (!state.maxCompletion && msg.includes('max_completion_tokens')) { state.maxCompletion = true; continue; }
        if (!state.dropTemp && msg.includes('temperature')) { state.dropTemp = true; continue; }
      }
      throw err;
    }
  }
}
```

Crucially, this mirrors the eval harness (`tests/prompt-eval/lib/common.mjs`), so production sends the exact same request the judges scored. Eval-prod parity is non-negotiable.

**Verification:** llm.test.js adds three test cases—gpt-4o keeps `max_tokens`; gpt-5.x uses `max_completion_tokens` with no wasted 400; an unrecognized model adapts on the 400 then succeeds. 98/98 pass. A twin run (gpt-5.4 + v3.0) completed a full paid customer journey 11/11. Stored row: model=gpt-5.4, 15 sections, 3,393 words, zero exemplar leak, DTC P0301 extracted, ~48s analysis latency inside the poll budget. Prod flipped: `LLM_MODEL=gpt-5.4` set + systemctl restart. Public healthz + unpaid smoke-test green.

Cost: ~$0.079/report (~3x gpt-4o) but under 2% of the $4.99 ticket. Rollback is one env line + restart; v2.0 prompt and gpt-4o model stay selectable for A/B or rollback.

**Takeaways:**

1. Gate each axis of a change on its own eval. Ship each as a one-line config switch, one-command rollback.
2. A prompt's length target can be silently capped by the model. Check word-count distributions in your eval, not just quality scores.
3. Make production send the same request your eval judged, or the eval doesn't transfer.

**Also shipped:** Across intent-os and prompts-intent-solutions, the doc-filing standard reached v4.4. Deleted a never-used shasum cross-repo rule; replaced it with a positive cluster-archetype definition (§3.1.2) for nested `000-docs` folders. The skill becomes canonical; the master copy becomes a published mirror.

## Related Posts

- [BM25 Before Vectors: An Eval-Gated Retrieval ADR](/posts/bm25-before-vectors-retrieval-backend-adr/) — the same "gate the decision on an eval" discipline, applied to a retrieval backend.
- [Run the Readiness Audit Before You Flip DNS](/posts/readiness-audit-before-the-dns-flip/) — the DiagnosticPro self-host rollout, one door earlier.
- [The LLM Should Never Do the Math](/posts/llm-never-does-the-math/) — where to draw the line on what the model is allowed to decide.
