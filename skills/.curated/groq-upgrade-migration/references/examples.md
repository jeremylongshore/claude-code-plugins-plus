# Groq Upgrade & Migration — Worked Examples

Concrete before/after scenarios showing what the migration does to real code.

## Example 1: Replace a decommissioned chat model

A service still calling `mixtral-8x7b-32768` returns `400 model_decommissioned`
after Groq's 2025-03-05 deprecation.

Before:

```typescript
const res = await groq.chat.completions.create({
  model: "mixtral-8x7b-32768",
  messages: [{ role: "user", content: prompt }],
});
```

After (per the migration map — `mixtral-8x7b-32768` → `llama-3.3-70b-versatile`):

```typescript
const res = await groq.chat.completions.create({
  model: "llama-3.3-70b-versatile",
  messages: [{ role: "user", content: prompt }],
});
```

## Example 2: Route every call through the resolver

Instead of hand-editing each call site, wrap the model ID with `resolveModel`
(defined in [implementation.md](implementation.md) Step 3) so deprecated IDs are
rewritten at runtime and logged:

```typescript
const res = await groq.chat.completions.create({
  model: resolveModel(config.groqModel), // logs + swaps if deprecated
  messages,
});
```

Console output on a deprecated ID:

```
Model gemma2-9b-it is deprecated. Using llama-3.1-8b-instant instead.
```

## Example 3: Migrate a transcription model

`distil-whisper-large-v3-en` was retired in favor of the faster turbo variant.

Before:

```typescript
const t = await groq.audio.transcriptions.create({
  model: "distil-whisper-large-v3-en",
  file: fs.createReadStream("call.mp3"),
});
```

After:

```typescript
const t = await groq.audio.transcriptions.create({
  model: "whisper-large-v3-turbo",
  file: fs.createReadStream("call.mp3"),
});
```

## Example 4: Full scanner run on a clean repo

Running Step 4's scanner (see [implementation.md](implementation.md)) on a repo
that is already migrated:

```
=== Deprecated Model IDs ===
None found

=== Old Import Patterns ===
None found (correct import is 'groq-sdk')

=== Deprecated Method Calls ===
None found
```

A non-empty result under any heading is a call site to fix before the SDK bump
ships.
