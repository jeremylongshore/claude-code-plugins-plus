# Acceptance Tests (Gherkin / BDD) — Wall 1

## Contents

[Ownership Rule](#section-1-ownership-rule) · [Per-Language Runner Matrix](#section-2-per-language-runner-matrix) · [Gherkin Quality Rubric](#section-3-gherkin-quality-rubric-advisory-human-owned) · [AUDIT Flow](#section-4-audit-flow) · [IMPLEMENT Flow](#section-5-implement-flow) · [Step Definition Guidance](#section-6-step-definition-guidance-ai-writable) · [Cross-References](#section-7-cross-references) · [Sources](#sources)

> **THE ENGINEER WRITES. THE AI MAKES PASS.**
>
> `.feature` files are a human artifact. The harness hash-pins them. Any AI
> diff that changes a `.feature` file fails with `HARNESS_TAMPERED`. Step
> definitions (glue code) are AI-writable; scenario text is not.

This reference covers Wall 1 of the Seven Walls: acceptance tests written in
Gherkin. Acceptance tests are the outermost loop of TDD — they encode
business intent in business language, and the inner TDD loop (unit tests,
coverage, mutation) only matters if these pass.

The skill runs two flows against this wall:

- **AUDIT flow**: hash-pin existing `.feature` files, run every scenario,
  report which public business entry points are uncovered.

- **IMPLEMENT flow**: scaffold `features/` directory, install the
  language-appropriate runner, write a starter `.feature` from the
  engineer's spoken intent, initialize the hash manifest.

---

## Section 1: Ownership Rule

| Artifact | Owner | Can AI touch? |
|----------|-------|---------------|
| `features/*.feature` | Human engineer | **No** — hash-pinned |
| `features/README.md` (ownership banner) | Human engineer | No |
| `features/steps/` (glue code) | AI | Yes — must make scenarios pass |
| `behave.ini` / `cucumber.js` / runner config | Shared | Edits flagged in AUDIT |

The harness runs `harness-hash.sh --verify` before every accepted diff.
Any byte change to a `.feature` file or the runner config without an
engineer-initiated `--init` fails the pipeline with exit 2.

---

## Section 2: Per-Language Runner Matrix

| Language | Runner | Install | Run | Config |
|----------|--------|---------|-----|--------|
| Python | behave | `pip install behave` | `behave features/` | `behave.ini` |
| Python | pytest-bdd | `pip install pytest-bdd` | `pytest features/` | `pyproject.toml` |
| JS/TS | @cucumber/cucumber | `npm i -D @cucumber/cucumber` | `npx cucumber-js` | `cucumber.js` |
| JS/TS | playwright-bdd | `npm i -D playwright-bdd` | `npx bddgen && npx playwright test` | `playwright.config.ts` |
| JS/TS | cypress-cucumber-preprocessor | `npm i -D @badeball/cypress-cucumber-preprocessor` | `npx cypress run` | `cypress.config.js` |
| Java / Kotlin | Cucumber-JVM | Gradle: `io.cucumber:cucumber-java` | `./gradlew cucumber` | `src/test/resources/features/` |
| Java | FitNesse | Download jar | `java -jar fitnesse.jar` | wiki pages |
| .NET | Reqnroll | `dotnet add package Reqnroll` | `dotnet test` | `reqnroll.json` |
| .NET | SpecFlow (legacy) | `dotnet add package SpecFlow` | `dotnet test` | `specflow.json` |
| Ruby | cucumber-ruby | `gem install cucumber` | `bundle exec cucumber` | `cucumber.yml` |
| Go | godog | `go install github.com/cucumber/godog/cmd/godog` | `godog run features/` | `godog.yaml` |
| Elixir | white-bread | `{:white_bread, "~> 4.5"}` in mix.exs | `mix white_bread.run` | `config/config.exs` |

Detection rules for the skill (look for existing config, in order):

1. `features/` directory exists → already using BDD, detect runner by neighboring config
2. `cucumber.js` / `cucumber.cjs` / `cucumber.mjs` → @cucumber/cucumber
3. `behave.ini` or `[tool.behave]` in `pyproject.toml` → behave
4. `reqnroll.json` / `specflow.json` → .NET
5. `godog.yaml` → godog
6. `@pytest-bdd` in `pyproject.toml` → pytest-bdd
7. None found → IMPLEMENT mode

---

## Section 3: Gherkin Quality Rubric (advisory, human-owned)

The harness does not enforce Gherkin prose quality — the engineer owns it.
`scripts/gherkin-lint.sh` applies this rubric as advisory guidance. Violations
are reported, not blocking.

### Good scenario structure

```gherkin
Feature: Premium customer checkout

  As a premium customer
  I want discounted pricing applied at checkout
  So that my loyalty is rewarded

  Background:
    Given I am signed in as a premium customer
    And my cart contains at least one item

  Scenario: Discount applies at checkout
    When I proceed to checkout
    Then the 15% premium discount is shown on the order summary
    And the discount is deducted from the total

  Scenario Outline: Discount scales by tier
    Given my tier is "<tier>"
    When I proceed to checkout
    Then the discount shown is "<discount>"

    Examples:
      | tier     | discount |
      | Silver   | 5%       |
      | Gold     | 10%      |
      | Platinum | 15%      |
```

### Rubric (what gherkin-lint checks)

| Rule | Enforced by | Penalty |
|------|-------------|---------|
| One behavior per scenario | gherkin-lint (multiple `When` blocks) | Warning |
| Declarative not imperative (no CSS selectors, no clicks on specific buttons) | awk pattern check | Warning |
| Business vocabulary (no technical jargon) | awk pattern check | Info |
| `Background` used when Givens repeat 3+ times | gherkin-lint | Info |
| Scenario Outline for data variants | gherkin-lint | Info |
| Max 10 steps per scenario | awk count | Warning |
| No `And` at start (use `Given`/`When`/`Then`) | gherkin-lint | Error |

Reference: [Writing Better Gherkin — cucumber.io](https://cucumber.io/docs/bdd/better-gherkin/).

---

## Section 4: AUDIT Flow

```bash
# 1. Pin the current state
bash scripts/harness-hash.sh --init

# 2. Run every scenario
case "$RUNNER" in
  behave)     behave features/ --junit ;;
  cucumber)   npx cucumber-js --format json:cucumber-report.json ;;
  godog)      godog run features/ --format=junit ;;
  reqnroll)   dotnet test ;;
esac

# 3. Measure coverage per public business entry point
#    (match Feature title → source module; reported as a table)
```

### AUDIT report section

```
ACCEPTANCE (Wall 1)
  Runner detected:    behave
  .feature files:     12
  Scenarios total:    47
  Scenarios passing:  44
  Scenarios failing:  3
  Uncovered entry points:
    - POST /refund  (no Feature references refunds)
    - Subscription cancellation flow
  Hash pin:           OK (last init 2026-04-18)
```

---

## Section 5: IMPLEMENT Flow

When the repo has **no** `features/` directory, the skill implements Wall 1:

1. **Create directory tree**

   ```
   features/
   ├── README.md          # ownership banner
   ├── .gitattributes     # export-ignore for test artifacts
   └── steps/             # glue code (AI-writable)
   ```

2. **Write `features/README.md`** with the ownership banner:

   ```markdown
   # Acceptance Features

   **THE ENGINEER WRITES. THE AI MAKES PASS.**

   Files in this directory (`*.feature`) are the specification. They are
   hash-pinned by `scripts/harness-hash.sh`. AI tooling may not modify
   them; any change fails CI with `HARNESS_TAMPERED`.

   AI tooling **may** write step definitions under `steps/` and must make
   every scenario pass.
   ```

3. **Install the language runner** from Section 2 matrix.

4. **Scaffold a starter `.feature`** from the engineer's spoken intent.
   Example — if the engineer said "I want a feature that makes sure
   premium customers get their discount applied":

   ```gherkin
   Feature: Premium customer checkout
     # Engineer-authored. Do not modify with AI tooling.

     Scenario: Discount applies at checkout
       Given I am signed in as a premium customer
       When I proceed to checkout
       Then the 15% premium discount is shown on the order summary
   ```

5. **Initialize the hash manifest**: `bash scripts/harness-hash.sh --init`.

6. **Wire CI**: add a `acceptance` job that runs the scenarios and the
   hash verify step.

7. **Report** the scaffolded files to the engineer for review. Commit
   nothing automatically.

---

## Section 6: Step Definition Guidance (AI-writable)

Step definitions are the glue between Gherkin prose and application code.
The AI may write and refactor them freely, but:

- **Must not weaken scenarios by stubbing them to pass** — step definitions
  exercise real code. If the feature needs infrastructure (database,
  HTTP server), the step definition brings it up.

- **Must not contain business logic** — that belongs in the application,
  not in steps. Steps wire inputs, invoke behavior, assert observations.

- **Keep step bodies thin** — under 10 lines is a good rubric.

Python (behave):

```python
# features/steps/checkout_steps.py
from behave import given, when, then

@given("I am signed in as a premium customer")
def step_signed_in_premium(context):
    context.user = create_user(tier="Platinum")
    context.session = login(context.user)

@when("I proceed to checkout")
def step_proceed_checkout(context):
    context.response = post("/checkout", session=context.session)

@then('the 15% premium discount is shown on the order summary')
def step_discount_shown(context):
    assert context.response.json()["discount_pct"] == 15
```

JS/TS (@cucumber/cucumber):

```ts
// features/steps/checkout.steps.ts
import { Given, When, Then } from '@cucumber/cucumber';

Given('I am signed in as a premium customer', async function () {
  this.user = await createUser({ tier: 'Platinum' });
  this.session = await login(this.user);
});
```

---

## Section 7: Cross-References

- Wall 2 (unit tests) → `{baseDir}/references/frameworks.md`
- Wall 5/6 (CRAP) → `{baseDir}/references/crap-and-complexity.md`
- Wall 7 (architecture) → `{baseDir}/references/architecture-constraints.md`
- Hash protocol → `{baseDir}/scripts/harness-hash.sh`
- Quality checks → `{baseDir}/scripts/gherkin-lint.sh`
- Escape detection → `{baseDir}/scripts/escape-scan.sh`

---

## Sources

- [Writing Better Gherkin — cucumber.io](https://cucumber.io/docs/bdd/better-gherkin/)
- [The Three Rules of TDD — Uncle Bob](http://www.butunclebob.com/ArticleS.UncleBob.TheThreeRulesOfTdd)
- [The Cycles of TDD — Clean Coder blog](https://blog.cleancoder.com/uncle-bob/2014/12/17/TheCyclesOfTDD.html)
- [Gherkin & BDD 2026 Guide — TestQuality](https://testquality.com/gherkin-user-stories-acceptance-criteria-guide/)
