# Property-Based Tests, Fuzzing, and Chaos Engineering

## Contents

[Purpose](#purpose) · [Property-Based Testing (PBT)](#property-based-testing-pbt) · [Fuzzing](#fuzzing) · [Chaos Engineering](#chaos-engineering) · [Schemathesis — PBT from OpenAPI](#schemathesis--pbt-from-openapi) · [Enforcement Checklist](#enforcement-checklist) · [Sources](#sources)

## Purpose

Example-based unit tests ask: "for these specific inputs, is output
correct?" That class of test catches bugs for inputs the author thought
about — and **misses everything else**. Property-based tests and fuzzing
generate inputs automatically and look for invariant violations. Chaos
engineering does the same thing at the infrastructure level.

The mega-test-skill bar: any non-trivial repo should have at least one
property-based test *and* a fuzz target if it parses untrusted input
(network, files, user strings).

## Property-Based Testing (PBT)

PBT is the practice of writing tests that state a *property* ("encoding
then decoding returns the input") and letting a framework generate many
inputs searching for a counter-example.

### Core insight

A good property-based test is worth hundreds of example tests, because
the framework's generator explores edge cases (empty strings, unicode,
negative zero, nil, large integers) the author would forget.

### Canonical frameworks per language

| Language | Framework | Notes |
|---|---|---|
| Haskell | **QuickCheck** | The original (2000, Claessen & Hughes). |
| Python | **Hypothesis** | David MacIver. Excellent shrinking, stateful testing. |
| JavaScript/TypeScript | **fast-check** | Nicolas Dubien. Async-aware, fuzzer-grade. |
| Rust | **proptest** | AltSysrq. Successor to QuickCheck-rs. |
| Go | **testing/quick** (stdlib) + **gopter** | stdlib is minimal; gopter is richer. |
| Go | **fuzz** (built-in) | Go 1.18+; property-adjacent. |
| Java | **jqwik** | Johannes Link. JUnit 5 integration. |
| Scala | **ScalaCheck** | Canonical for the JVM. |
| Kotlin | **Kotest property** | `io.kotest:kotest-property`. |
| Clojure | **test.check** | Port of QuickCheck. |
| Ruby | **rantly** | Less polished than Hypothesis but functional. |
| Elixir | **StreamData** (built-in) | Part of `ex_unit`. |
| .NET | **FsCheck** | Pairs with xUnit/NUnit. |
| Erlang | **PropEr**, **QuickCheck-Erlang** | Commercial (Quviq) + OSS. |
| Swift | **SwiftCheck** | iOS/macOS testing. |
| OCaml | **qcheck** | — |
| C | **theft** | Scott Vokes. |
| C++ | **rapidcheck** | Template-heavy QuickCheck port. |

### Hypothesis example (Python)

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_is_idempotent(xs):
    assert sorted(sorted(xs)) == sorted(xs)

@given(st.text())
def test_encode_roundtrip(s):
    assert decode(encode(s)) == s
```

Hypothesis finds bugs the author didn't think about — empty lists,
unicode surrogates, duplicate items, NaN — and *shrinks* failures to
minimal reproductions.

### fast-check example (TS)

```ts
import fc from "fast-check";
test("sort is idempotent", () => {
  fc.assert(fc.property(
    fc.array(fc.integer()),
    xs => deepEqual(sort(sort(xs)), sort(xs))
  ));
});
```

### Stateful / model-based testing

The most advanced PBT mode: the framework generates *sequences* of
operations and verifies the system under test stays consistent with a
reference model.

- Hypothesis: `RuleBasedStateMachine`
- fast-check: `asyncModelRun` / `modelRun`
- ScalaCheck: commands
- proptest: `prop_compose!` + state machines

Use for: data structures, protocol implementations, stateful services.

### Properties worth testing

1. **Roundtrip**: `decode(encode(x)) == x`.
2. **Commutativity / associativity / idempotence**: math-shaped ops.
3. **Inverse**: `f(g(x)) == x` for mutually inverse functions.
4. **Invariant preservation**: after any state transition, invariant holds.
5. **Monotonicity**: ordering relationships preserved.
6. **Reference oracle**: two implementations agree (slow + fast, library + custom).

### Integration with coverage

Hypothesis, fast-check, proptest, and jqwik all integrate with coverage
tools. Treat PBT coverage as part of Wall 3.

## Fuzzing

Fuzzing feeds *untrusted, malformed, random* input to code to find
crashes, hangs, and memory errors. Focus: parsers, deserializers,
network input handlers, protocol implementations.

### Two schools

1. **Coverage-guided fuzzing** — feedback-driven, mutates inputs to
   maximize newly-reached code paths. Modern approach. AFL, libFuzzer,
   go-fuzz, cargo-fuzz, Jazzer.

2. **Structure-aware fuzzing** — uses grammar/schema to generate valid-looking
   input, then mutates at the structural level. Nautilus, dharma.

### Canonical tools per language

| Language | Tool | Scope |
|---|---|---|
| C/C++ | **libFuzzer** (LLVM) | In-process, fastest. `-fsanitize=fuzzer`. |
| C/C++ | **AFL++** | External process, many instrumentations. |
| C/C++ | **honggfuzz** | Google-flavored AFL alternative. |
| Rust | **cargo-fuzz** (libFuzzer) | `cargo fuzz run <target>` |
| Rust | **afl.rs** | AFL instrumentation. |
| Go | **`go test -fuzz`** (native) | Go 1.18+. |
| Go | **go-fuzz** (legacy) | Pre-1.18 world. |
| Python | **Atheris** (libFuzzer-based) | Google. Bytecode instrumentation. |
| Python | **python-afl** | Older. |
| JVM | **Jazzer** (Code-Intelligence) | libFuzzer for JVM. |
| JavaScript | **Jazzer.js** | libFuzzer for Node. |
| Kotlin | Jazzer (JVM) | — |
| .NET | **SharpFuzz** | Based on AFL. |
| Ruby | **afl-ruby** | Experimental. |
| Kernel | **syzkaller** (Google) | Linux/Windows kernel fuzzer. |

### cargo-fuzz example

```bash
cargo install cargo-fuzz
cargo fuzz init
# fuzz/fuzz_targets/parse.rs
#![no_main]
use libfuzzer_sys::fuzz_target;
fuzz_target!(|data: &[u8]| {
    let _ = myparser::parse(data);
});

cargo fuzz run parse -- -max_total_time=300
```

### Go native fuzz

```go
func FuzzDecode(f *testing.F) {
    f.Add([]byte("valid seed"))
    f.Fuzz(func(t *testing.T, data []byte) {
        _, _ = Decode(data) // just don't panic
    })
}
```

Run: `go test -fuzz=FuzzDecode -fuzztime=60s`.

### Corpus management

- Commit an initial corpus (interesting seed inputs) to the repo.
- Save discovered corpus findings as regression tests.
- On-failure artifact: a minimized reproducer goes into unit tests.

### OSS-Fuzz integration

Google's OSS-Fuzz runs continuous fuzzing on 1000+ OSS projects for
free. For high-impact libraries, enrolling is a P1 gate — bugs found
get automatic CVEs and disclosure timelines.

## Chaos Engineering

Fuzz for infrastructure. Deliberately inject failures into staging (or
carefully, production) to validate that the system survives.

### Principles (Netflix's Principles of Chaos)

1. Define steady state (SLOs, throughput, error rate).
2. Hypothesize: "steady state continues under failure X."
3. Inject failure X.
4. Measure. If hypothesis fails, fix.

### Tools

| Tool | Level |
|---|---|
| **Chaos Mesh** | Kubernetes-native CRDs (pod kill, network partition, I/O delay, JVM stress). CNCF project. |
| **Chaos Toolkit** | Python CLI + YAML experiments, cloud-agnostic. |
| **Litmus** | K8s-native, similar to Chaos Mesh. CNCF. |
| **Chaos Monkey** (Netflix) | Historical — now part of Simian Army → Spinnaker. Random instance termination. |
| **Gremlin** | Commercial, polished UI, comprehensive attack library. |
| **Pumba** | Docker-specific; pause/kill/network chaos on containers. |
| **Toxiproxy** (Shopify) | TCP proxy injecting latency, connection drops. Great for local dev. |
| **AWS Fault Injection Simulator (FIS)** | Managed chaos for AWS resources. |
| **Azure Chaos Studio** | Same for Azure. |
| **Steadybit** | Commercial, modern chaos platform. |

### What to test

Classic chaos scenarios:

1. **Service dependency fails** — primary DB goes down; app should serve from replica / cache / graceful degradation.
2. **Network partition** — one AZ isolated; app should use other AZ.
3. **Latency injection** — 500ms added to inter-service calls; app should have reasonable timeouts.
4. **Resource exhaustion** — CPU/memory saturated; app should shed load, not crash.
5. **Disk full** — writes fail; app should log and surface clean error.
6. **Clock skew** — token / cache TTL behavior.
7. **Pod eviction** — K8s kills a pod; app should survive via retries / HPA.

### Progression

- **Game days** (manual, quarterly) — planned chaos exercise with all hands.
- **Scheduled chaos** (weekly, automated) — chaos pipeline running in staging.
- **Continuous chaos** (Gremlin, Chaos Mesh in prod) — only for mature orgs.

## Schemathesis — PBT from OpenAPI

A unique tool: given an OpenAPI / GraphQL spec, Schemathesis generates
property-based tests automatically.

```bash
pip install schemathesis
schemathesis run --checks all https://example.com/openapi.json
```

Checks include: 500-error probing, response schema conformance, header
validation, status-code compliance, Links/Hypermedia traversal.

Because the spec *is* the contract, any schema divergence is caught
automatically. This is the fastest path to property-based coverage for
HTTP services.

Equivalent for GraphQL: built into Schemathesis (`schemathesis run
--app graphql-app`); also `easygraphql-tester`, `graphql-faker`.

## Enforcement Checklist

- [ ] At least one property-based test exists (roundtrip or invariant)
- [ ] PBT framework is a dev dependency
- [ ] If repo parses untrusted input: at least one fuzz target
- [ ] Fuzz corpus committed
- [ ] Fuzz runs in CI on a schedule (nightly or weekly)
- [ ] Fuzz findings fed back as regression unit tests
- [ ] For HTTP services: Schemathesis run in CI against staging
- [ ] For high-impact OSS libraries: enrolled in OSS-Fuzz
- [ ] Infrastructure repos: chaos experiments defined (Chaos Mesh / Toxiproxy) and run in staging regularly
- [ ] Game-day runbook documented (`docs/chaos-gameday.md`)

## Sources

- Claessen & Hughes (2000) — "QuickCheck: A Lightweight Tool for Random Testing of Haskell Programs" (ICFP)
- David MacIver — Hypothesis docs (hypothesis.readthedocs.io)
- Nicolas Dubien — fast-check docs (fast-check.dev)
- LLVM libFuzzer docs (llvm.org/docs/LibFuzzer.html)
- AFL++ docs (aflplus.plus)
- Google — "OSS-Fuzz: Continuous Fuzzing for Open Source Software"
- Netflix — Principles of Chaos (principlesofchaos.org)
- Rosenthal et al. — *Chaos Engineering* (O'Reilly)
- Casey Rosenthal & Nora Jones — *Learning Chaos Engineering*
- CNCF — Chaos Mesh, Litmus project docs
