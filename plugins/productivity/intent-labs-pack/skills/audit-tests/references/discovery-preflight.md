# Discovery & Pre-Flight

Auto-discovery and pre-flight checks before test execution.

> **Shell-alias caveat (IMPORTANT):** In many dev environments (notably zsh with modern tooling: eza/bat/fd/rg), `find` is aliased to `fd` and `grep` is aliased to `rg` — both accept different flags from the GNU originals. This SKILL's example commands assume **GNU coreutils**. When running them in an aliased shell:
>
> - Use the native `Grep` / `Glob` tools if you're Claude Code, OR
> - Call `/usr/bin/find` and `/usr/bin/grep` explicitly in bash tool calls, OR
> - Prefix with `command` to bypass aliases: `command find . -maxdepth 5 ...`
>
> Every `find`/`grep` example below should be treated as `/usr/bin/find` / `/usr/bin/grep` when executing.

---

## Auto-Discovery

Never assume. Always discover before running.

**Config file scan** — find test configs:

```bash
/usr/bin/find . -maxdepth 5 \( \
  -name "vitest.config.*" -o -name "jest.config.*" \
  -o -name "playwright.config.*" -o -name "cypress.config.*" \
  -o -name ".mocharc*" -o -name "pytest.ini" \
  -o -name "pyproject.toml" -o -name "conftest.py" \
  -o -name "go.mod" -o -name "Cargo.toml" -o -name "Gemfile" \
  -o -name "build.gradle*" -o -name "pom.xml" \
  -o -name "phpunit.xml*" -o -name "mix.exs" \
  -o -name "*.csproj" -o -name "*.sln" \
  -o -name "Makefile" \
\) -not -path "*/node_modules/*" -not -path "*/.git/*" \
   -not -path "*/vendor/*" -not -path "*/target/*" 2>/dev/null
```

**Build script scan:**

```bash
# Node projects
/usr/bin/find . -name "package.json" -not -path "*/node_modules/*" | \
  xargs grep -l '"test"\|"test:unit"\|"test:e2e"\|"test:ci"' 2>/dev/null

# Python
cat pyproject.toml 2>/dev/null | grep -A5 '\[tool.pytest\]'

# Makefiles (any language)
grep -i "^test\b\|^check\b\|^spec\b" Makefile 2>/dev/null

# Go
cat Makefile 2>/dev/null | grep "go test"
```

**Test directory scan:**

```bash
/usr/bin/find . -maxdepth 6 -type d \( \
  -name "__tests__"    \
  -o -name "tests"     \
  -o -name "test"      \
  -o -name "spec"      \
  -o -name "specs"     \
  -o -name "e2e"       \
  -o -name "cypress"   \
  -o -name "features"  \
  -o -name "integration" \
  -o -name "unit"      \
  -o -name "__mocks__" \
  -o -name "fixtures"  \
  -o -name "stubs"     \
  -o -name "mocks"     \
\) -not -path "*/node_modules/*" \
   -not -path "*/.git/*"         \
   -not -path "*/vendor/*" 2>/dev/null
```

**Doc-quality tooling scan** (NEW — Layer 2 doc & prose quality + Layer 4 doc-framework build):

```bash
# L2 doc lint / prose / link / frontmatter / formatting
/usr/bin/find . -maxdepth 5 \( \
  -name ".markdownlint.json" -o -name ".markdownlint.yaml" -o -name ".markdownlint.yml" \
  -o -name ".markdownlint-cli2.jsonc" -o -name ".markdownlint-cli2.yaml" \
  -o -name ".remarkrc" -o -name ".remarkrc.*" \
  -o -name ".vale.ini" -o -name "vale.ini" -o -name ".vale.toml" \
  -o -name "lychee.toml" -o -name ".lycheeignore" \
  -o -name ".markdown-link-check.json" \
  -o -name ".proselintrc" -o -name "proselint.json" \
  -o -name ".prettierrc*" -o -name "prettier.config.*" \
  -o -name "ajv.config.*" -o -name "schema.config.*" \
\) -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null

# L4 doc-framework build (gates that docs RENDER, not just lint)
/usr/bin/find . -maxdepth 3 \( \
  -name "astro.config.*" \
  -o -name "docusaurus.config.*" -o -name "docusaurus.config.js" -o -name "docusaurus.config.ts" \
  -o -name "next.config.*" \
  -o -name "mdx.config.*" -o -name ".mdxrc" -o -name "mdx-components.tsx" \
  -o -name "config.toml" -o -name "hugo.toml" -o -name "hugo.yaml" \
  -o -name "_config.yml" -o -name "_config.yaml" \
\) -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null

# Markdown corpus size — drives doc-quality threshold per taxonomy § L2
MD_COUNT=$(/usr/bin/find . -name "*.md" -o -name "*.mdx" 2>/dev/null \
  | /usr/bin/grep -vE "(/node_modules/|/\.git/|/dist/|/build/|/coverage/)" \
  | wc -l)
DOCS_DIR=$(ls -d 000-docs docs documentation 2>/dev/null | head -1)
SKILL_CORPUS=$(/usr/bin/find . -name "SKILL.md" 2>/dev/null \
  | /usr/bin/grep -vE "(/node_modules/|/\.git/)" | wc -l)
echo "MD_COUNT=$MD_COUNT DOCS_DIR=${DOCS_DIR:-none} SKILL_CORPUS=$SKILL_CORPUS"
```

**Doc-quality applicability decision** (per taxonomy.md § Layer 2 doc-quality gap addition):

| Signal | L2 Doc-quality required? |
|---|---|
| `MD_COUNT >= 50` | YES |
| `000-docs/` or `docs/` directory present | YES |
| `SKILL_CORPUS >= 10` (agentskills.io corpus) | YES |
| Astro / Docusaurus / Next.js content / Hugo / Jekyll detected | YES — both L2 doc-quality AND L4 doc-framework-build |
| Pure binary/code repo with `<50` md + no `docs/` | NO — code lint at L2 is sufficient |

When L2 doc-quality is required, `/audit-tests` reports presence/absence for each row in the L2 doc-quality table (markdownlint, vale, lychee, prettier-for-md, frontmatter validator) and surfaces missing ones as P1 gaps. `/implement-tests` installs the missing tools per its L2 doc-quality playbook.

**Language detection:**

```bash
ls package.json tsconfig.json 2>/dev/null   && echo "LANG: Node/TypeScript"
ls requirements.txt pyproject.toml 2>/dev/null && echo "LANG: Python"
ls go.mod 2>/dev/null                        && echo "LANG: Go"
ls Cargo.toml 2>/dev/null                    && echo "LANG: Rust"
ls Gemfile 2>/dev/null                       && echo "LANG: Ruby"
ls pom.xml build.gradle 2>/dev/null          && echo "LANG: Java/Kotlin"
ls composer.json 2>/dev/null                 && echo "LANG: PHP"
ls mix.exs 2>/dev/null                       && echo "LANG: Elixir"
ls *.cabal stack.yaml 2>/dev/null            && echo "LANG: Haskell"
ls *.csproj *.sln 2>/dev/null               && echo "LANG: C#/.NET"
ls Dockerfile docker-compose*.yml 2>/dev/null && echo "INFRA: Docker"
```

**Discovery decision matrix:**

| Signal | Action |
|--------|--------|
| `vitest.config.*` | → Vitest |
| `jest.config.*` or Jest in package.json | → Jest |
| `playwright.config.*` | → Playwright |
| `cypress.config.*` | → Cypress |
| `pytest.ini` / `pyproject.toml` with pytest | → Pytest |
| `go.mod` + `*_test.go` files | → Go Test |
| `Cargo.toml` | → Cargo |
| `Gemfile` + `spec/` directory | → RSpec |
| `pom.xml` / `build.gradle` | → JUnit/Gradle |
| `phpunit.xml` | → PHPUnit |
| `mix.exs` | → ExUnit |
| `*.csproj` / `*.sln` | → .NET/xUnit |
| `Makefile` with test target | → `make test` |
| k6 / Artillery / Locust scripts | → Performance |
| Nothing found | → Scaffold |

---

## Pre-Flight Checks

Run before any test execution — no exceptions.

**Package manager detection:**

| Signal | Manager | Prefix |
|--------|---------|--------|
| `pnpm-lock.yaml` | pnpm | `pnpm` |
| `yarn.lock` | yarn | `yarn` |
| `package-lock.json` | npm | `npx` |
| `bun.lockb` | bun | `bun` |
| `poetry.lock` | poetry | `poetry run` |
| `uv.lock` | uv | `uv run` |
| `go.mod` | go | `go` |
| `Cargo.toml` | cargo | `cargo` |
| `Gemfile.lock` | bundler | `bundle exec` |
| `build.gradle` | gradle | `./gradlew` |
| `pom.xml` | maven | `mvn` |

**Environment readiness:**

```bash
# Node — dependencies installed?
[ -d node_modules ] || echo "MISSING: node_modules — run install first"

# Python — venv active?
python -c "import sys; print(sys.prefix)"

# Env files
ls .env .env.test .env.local .env.ci .env.testing 2>/dev/null

# Build artifacts (if needed)
ls dist/ build/ .next/ out/ 2>/dev/null

# Docker running? (for service-dependent tests)
docker info 2>/dev/null | grep "Server Version" || echo "Docker not running"

# Port conflicts
lsof -i :3000 -i :4000 -i :5173 -i :8000 -i :8080 -i :5432 -i :6379 2>/dev/null | grep LISTEN
```

**Monorepo detection:**

```bash
ls pnpm-workspace.yaml nx.json turbo.json lerna.json rush.json 2>/dev/null
```

If monorepo → ask user: which package, or all?

```bash
pnpm --filter @scope/package test   # single package (pnpm)
pnpm -r test                        # all packages
npx turbo test                      # Turborepo
npx nx run-many --target=test --all # Nx
npx nx affected --target=test       # Nx — only changed
npx lerna run test                  # Lerna
```
