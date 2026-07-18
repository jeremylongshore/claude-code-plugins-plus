# ElevenLabs Local Dev Loop — Worked Examples

Concrete end-to-end runs of the dev loop. Each example uses the code from
[implementation.md](implementation.md).

## Example 1: Run the unit test suite with zero API cost

The mock layer (`tests/__mocks__/elevenlabs.ts`) returns the known-good
`sample.mp3` fixture, so unit tests never call the real API or burn character
quota.

```bash
npm run test
```

The mocked test drives the service through the fake client:

```typescript
it("should generate audio from text (mocked)", async () => {
  const audio = await mockElevenLabsClient.textToSpeech.convert(
    "21m00Tcm4TlvDq8ikWAM",
    { text: "Test speech", model_id: "eleven_flash_v2_5" }
  );
  expect(audio).toBeDefined();
});
```

Expected: the suite passes offline, with no `ELEVENLABS_API_KEY` set and no
character charges.

## Example 2: Check quota before spending real credits

Run the quota checker before any integration run so a low balance fails fast
instead of surprising you mid-test.

```bash
npm run quota
```

Expected output on a healthy free tier:

```
Characters: 500 / 10,000 (5.0% used)
Remaining: 9,500 characters
```

When `remaining < 1000`, the script prints the low-quota warning and exits `1`,
which stops a CI step or a chained command before it hits the paid API.

## Example 3: Opt into a real integration run

Real API calls are gated behind `ELEVENLABS_INTEGRATION=1` so they only happen
when you explicitly ask for them.

```bash
npm run test:integration
```

This sets the flag that flips the guarded test on:

```typescript
const useRealApi = process.env.ELEVENLABS_INTEGRATION === "1";

it.skipIf(!useRealApi)("should generate real audio (integration)", async () => {
  const { ElevenLabsClient } = await import("@elevenlabs/elevenlabs-js");
  const client = new ElevenLabsClient();
  const audio = await client.textToSpeech.convert("21m00Tcm4TlvDq8ikWAM", {
    text: "Integration test.",
    model_id: "eleven_flash_v2_5",
  });
  expect(audio).toBeDefined();
});
```

Without the flag, this test is skipped and only the mocked path runs.

## Example 4: Hot-reload iteration while building

Use `tsx watch` for a fast edit-save-rerun loop on your entry point. Because
dev config selects `eleven_flash_v2_5` (0.5 credits/char, ~75ms latency), each
iteration is cheaper and faster than the production `eleven_multilingual_v2`
path.

```bash
npm run dev
```

Edit `src/index.ts`, save, and `tsx` restarts the process automatically — pair
this with the mock layer to keep the loop free until you deliberately switch to
integration mode.
