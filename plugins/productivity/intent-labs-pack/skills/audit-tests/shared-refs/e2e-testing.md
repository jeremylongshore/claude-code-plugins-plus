# End-to-End Testing

---

## Playwright

```bash
npx playwright test                         # all tests
npx playwright test e2e/auth.spec.ts        # single file
npx playwright test --ui                    # interactive
npx playwright test --headed                # watch browser
npx playwright test --debug                 # step through
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
npx playwright test --update-snapshots      # refresh visual baseline
npx playwright show-report                  # HTML report
npx playwright install                      # install browsers
npx playwright install --with-deps          # + OS deps
```

---

## Cypress

```bash
npx cypress run                             # headless (CI)
npx cypress open                            # interactive
npx cypress run --spec "cypress/e2e/auth.cy.ts"
npx cypress run --browser chrome
npx cypress run --browser firefox
npx cypress run --record --key <KEY>
```

---

## Browser UI Tests (Vite dev server)

For test suites that run in-browser via a `/tests` route.

```bash
# Check if server already running
cat /tmp/running-vite-*.txt 2>/dev/null
lsof -i :5173 -i :4200 -i :3000 2>/dev/null | grep LISTEN
```

**Server running:** use `chrome-devtools-mcp` → navigate to `<URL>/tests`

**No server:**

```bash
cd <project-dir>
pnpm vite &
echo "http://localhost:5173" > /tmp/running-vite-$(basename $PWD).txt
```

Then navigate via `chrome-devtools-mcp`.

---

## WebdriverIO

```bash
npx wdio run wdio.conf.ts
npx wdio run wdio.conf.ts --spec tests/login.spec.ts
```

---

## Selenium (Python)

```bash
pytest tests/e2e/ --driver=Chrome
pytest tests/e2e/ --driver=Firefox
```

---

## Cucumber / BDD

```bash
bundle exec cucumber          # Ruby
npx cucumber-js               # JavaScript
behave features/              # Python
```
