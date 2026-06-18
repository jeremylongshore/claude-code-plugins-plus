# Capability Reference

Reference material for the `run-automation-suite` skill. The skill orchestrates Appium test execution on Kobiton's device cloud; this file holds the lookup tables and reconciliation rules the skill consults when parsing a test script and reconciling its capabilities against the rendered defaults for the selected device.

## Runtime detection

Detect the language and runtime for a test script from its file extension:

| Extension | Runtime | Common commands |
|-----------|---------|-----------------|
| `.js` / `.ts` / `.mjs` | Node.js | `node <script> <udid>`, `npm test`, `npx wdio`, `yarn test`, `pnpm test` |
| `.py` | Python | `python <script> <udid>`, `python3 <script> <udid>`, `pytest` |
| `.cs` / `.csproj` | .NET | `dotnet test` |
| `.java` / `.kt` | Java / Kotlin | `mvn test`, `gradle test`, `./gradlew test`, `java -cp ...` |
| `.rb` | Ruby | `ruby <script>`, `bundle exec rspec` |

**Picking the right command:** if the project has a manifest file (`package.json`, `pyproject.toml`, `pom.xml`, `build.gradle`, `Gemfile`), prefer the matching test runner (`npm test`, `pytest`, `mvn test`, `gradle test`, `bundle exec rspec`). Otherwise default to invoking the runtime directly on the script (e.g. `node <script>`, `python3 <script>`, `ruby <script>`).

## Capability fields

Key Appium / Kobiton capability fields to extract from a parsed test script:

- `platformName` (Android / iOS)
- `udid` (hardcoded or parameterized)
- `app` (app URL or `kobiton-store:` reference)
- `sessionName`, `sessionDescription`
- `automationName` (UiAutomator2, XCUITest, etc.)
- `browserName` (if browser-based test)
- `deviceOrientation`
- Any `kobiton:*` vendor extensions (especially `kobiton:runtime`)

## Reconciliation rules

After running `scripts/render-capabilities.js`, compare its JSON output against the capabilities parsed from the user's script using these three categories:

- **Must-match** (`platformName`, `platformVersion`, `appium:udid`, `appium:deviceName`, `appium:app` / `browserName`, `appium:automationName`, `kobiton:aiToolName`): if different, show the user what will change and edit the script automatically. Device/platform fields must match the selected device/app or the Kobiton session will fail to start correctly. For `kobiton:aiToolName`: if the rendered output includes a value, always overwrite any existing value in the user's script with it — adoption analytics must reflect the *current* AI CLI, not a stale value from a prior run under a different CLI. If the rendered output omits the capability (no runtime marker matched), leave the user's existing value untouched. **Enforcement:** unlike the device/platform fields (whose mismatch causes the Kobiton session to fail loudly), a missing `kobiton:aiToolName` produces no runtime error — the test runs but analytics are silently wrong. The skill MUST verify the injection landed by grepping the script for the literal string `kobiton:aiToolName` before executing; if missing while the rendered output has a value, complete the edit first. **Non-interactive:** edit silently and mention the one-line change inline for transparency; do NOT ask the user to confirm — the value is deterministic and there is nothing to negotiate.
- **Suggested defaults** (`kobiton:sessionName`, `kobiton:sessionDescription`, `kobiton:deviceOrientation`, `kobiton:captureScreenshots`, `appium:noReset`, `appium:fullReset`): if different or missing, show the diff and ask the user before changing. The user may have intentionally set different values.
- **User-controlled**: any capabilities in the user's script that are not in the rendered output - leave untouched. Never inject or modify `kobiton:runtime` unless the user explicitly asks.

## See also

- [`../SKILL.md`](../SKILL.md) - the orchestration skill that consumes this reference.
- [Kobiton available capabilities reference](https://docs.kobiton.com/automation-testing/capabilities/available-capabilities) - canonical platform docs for `kobiton:*` and supported `appium:*` capabilities.
- [Appium 2.x documentation](https://appium.io/docs/en/2.0/) - driver-specific capability docs (UiAutomator2, XCUITest).
- [`../templates/appium.ejs`](templates/appium.ejs) - the EJS template `render-capabilities.js` uses to produce the rendered JSON.
