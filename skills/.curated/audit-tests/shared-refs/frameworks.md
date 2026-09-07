# Unit & Integration Test Frameworks

Complete command reference for every supported framework.

---

## Vitest

```bash
pnpm vitest run                             # CI-safe run
pnpm vitest run --coverage                  # with coverage
pnpm vitest                                 # watch mode
pnpm vitest run path/to/file.test.ts        # single file
pnpm vitest run -t "test name"              # filter by name
pnpm vitest --ui                            # browser UI
pnpm vitest --typecheck                     # include type errors
pnpm vitest run --reporter=verbose          # full output
pnpm vitest run --reporter=json \
  --outputFile=results.json                 # CI parseable
pnpm vitest bench                           # benchmarks
```

---

## Jest

```bash
npx jest                                    # all tests
npx jest --watch                            # watch mode
npx jest path/to/file.test.js               # single file
npx jest --coverage                         # coverage
npx jest --verbose                          # verbose
npx jest --testNamePattern="name"           # filter
npx jest --bail                             # stop on first fail
npx jest --detectOpenHandles                # debug hangs
npx jest --runInBand                        # serial (debug)
npx jest --forceExit                        # force exit (last resort)
```

---

## Pytest (Python)

```bash
pytest                                      # all tests
pytest -v                                   # verbose
pytest tests/test_api.py                    # single file
pytest -k "test_auth"                       # filter by name
pytest -m "unit"                            # filter by marker
pytest --cov=src --cov-report=html          # coverage
pytest -x                                   # stop on first fail
pytest --lf                                 # rerun last failures
pytest -l                                   # show locals on fail
pytest --collect-only -q                    # list test IDs
pytest -n auto                              # parallel (pytest-xdist)
pytest --tb=short                           # shorter tracebacks
```

---

## Go Test

```bash
go test ./...                               # all packages
go test -v ./...                            # verbose
go test ./internal/api/...                  # specific package
go test -run TestFunctionName ./...         # filter
go test -cover ./...                        # coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out            # HTML report
go test -race ./...                         # race detection
go test -timeout 30s ./...                  # timeout
go test -count=1 ./...                      # disable cache
go test -bench=. ./...                      # benchmarks
go test -benchmem ./...                     # benchmark memory
```

---

## Cargo (Rust)

```bash
cargo test                                  # all tests
cargo test -- --nocapture                   # show output
cargo test test_name                        # filter
cargo test -- --test-threads=1              # serial
cargo test --lib                            # lib only
cargo test --doc                            # doc tests
cargo bench                                 # benchmarks
cargo tarpaulin                             # coverage
```

---

## RSpec (Ruby)

```bash
bundle exec rspec                           # all tests
bundle exec rspec spec/models/              # directory
bundle exec rspec spec/models/user_spec.rb  # single file
bundle exec rspec -e "authenticates"        # filter
bundle exec rspec --format documentation    # verbose
bundle exec rspec --fail-fast               # stop on first fail
bundle exec rspec --order random            # randomize
```

---

## JUnit / Gradle / Maven (Java/Kotlin)

```bash
# Gradle
./gradlew test
./gradlew test --tests "com.example.*"
./gradlew test --info
./gradlew jacocoTestReport                  # coverage

# Maven
mvn test
mvn test -Dtest=UserServiceTest
mvn verify                                  # includes integration
mvn surefire:test                           # unit only
```

---

## PHPUnit (PHP)

```bash
./vendor/bin/phpunit
./vendor/bin/phpunit tests/Unit/
./vendor/bin/phpunit --filter testAuth
./vendor/bin/phpunit --coverage-html coverage/
./vendor/bin/phpunit --testdox
```

---

## ExUnit (Elixir)

```bash
mix test
mix test test/models/user_test.exs
mix test --only tag:focus
mix test --cover
mix test --stale
```

---

## .NET / xUnit / NUnit (C#)

```bash
dotnet test
dotnet test --filter "Category=Unit"
dotnet test --collect:"XPlat Code Coverage"
dotnet test --logger "console;verbosity=detailed"
```

---

## BDD / Acceptance Runners (Wall 1)

See `{baseDir}/references/acceptance-tests-gherkin.md` for the full
ownership and hash-pinning protocol. Runners below execute engineer-authored
`.feature` files; step definitions are AI-writable.

### Python — behave

```bash
pip install behave
behave features/                           # run all scenarios
behave features/checkout.feature           # single file
behave --tags=@smoke                       # tag filter
behave --junit --junit-directory reports   # JUnit output
behave --format=progress3                  # dotted progress
```

### Python — pytest-bdd

```bash
pip install pytest-bdd
pytest features/                           # run via pytest
pytest --gherkin-terminal-reporter         # gherkin-style output
```

### JS/TS — @cucumber/cucumber

```bash
npm i -D @cucumber/cucumber
npx cucumber-js                            # all .feature files
npx cucumber-js features/checkout.feature  # single file
npx cucumber-js --tags "@smoke"            # tag filter
npx cucumber-js --format json:report.json  # JSON report
```

### JS/TS — playwright-bdd

```bash
npm i -D playwright-bdd @playwright/test
npx bddgen                                 # generate test files
npx playwright test                        # run under Playwright
```

### JS/TS — cypress-cucumber-preprocessor

```bash
npm i -D @badeball/cypress-cucumber-preprocessor
npx cypress run --spec 'features/**/*.feature'
```

### Java / Kotlin — Cucumber-JVM

```bash
# Gradle (build.gradle adds io.cucumber:cucumber-java)
./gradlew cucumber
./gradlew test --tests '*CucumberRunner*'
```

### Go — godog

```bash
go install github.com/cucumber/godog/cmd/godog@latest
godog run features/
godog run -f pretty features/
godog run --tags=@smoke features/
```

### .NET — Reqnroll (SpecFlow successor)

```bash
dotnet add package Reqnroll
dotnet test                                # scenarios run as tests
dotnet test --filter "TestCategory=smoke"
```

### Ruby — cucumber-ruby

```bash
bundle add cucumber
bundle exec cucumber
bundle exec cucumber features/checkout.feature
bundle exec cucumber --tags @smoke
```

### Elixir — white-bread

```elixir
# mix.exs: {:white_bread, "~> 4.5", only: :test}
```

```bash
mix white_bread.run
mix white_bread.run --path features/
```
