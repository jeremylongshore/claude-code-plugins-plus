# Per-Command Response Shapes

Reference material for the `run-interactive-cli-session` skill. The skill drives a Kobiton device by translating natural-language intent into CLI commands; this file holds the parsing guidance for every command's response so the skill knows how to extract values, detect success, and surface results to the user.

Most WebDriver endpoints return a JSON envelope `{"value": <result>}`. A few commands (`wd get screenshot`, `wd get source`) are unwrapped by the CLI and emit raw bytes/text directly. Non-WebDriver commands (`session`, `device`, `file`, `app`, `test`) typically emit plain text and signal failure through exit code.

## WebDriver commands

| Command | Response on stdout | How to read |
|---|---|---|
| `wd post element` (find) | JSON envelope; the element ID lives under `.value` (W3C/Appium standard - may be `.value.ELEMENT` or `.value["element-6066-11e4-a52e-4f735466cecf"]` or a bare string) | Extract with `jq -r '.value.ELEMENT // .value["element-6066-11e4-a52e-4f735466cecf"] // .value'`, or pattern-match the string |
| `wd post element/<id>/click`, `.../value`, `.../clear`, `wd post orientation`, `wd post url`, `wd post actions`, `wd post execute` | JSON envelope `{"value": <result>}`; usually `null` on success | Treat null/empty `.value` as success; surface a non-null `.value` (e.g., script return) to the user |
| `wd get element/<id>/text`, `wd get url`, `wd get orientation` | JSON `{"value":"<string>"}` | `.value` is the requested string |
| `wd get window/rect` | JSON `{"value":{"width":<n>,"height":<n>,"x":<n>,"y":<n>}}` | Use `.value.width` etc. |
| `wd get screenshot` | Base64-encoded PNG (CLI unwraps the WebDriver JSON for you) | Pipe through `base64 -d` straight into a `.png` file |
| `wd get source` | Raw XML / hierarchy markup (CLI unwraps the WebDriver JSON for you) | Redirect straight into a `.xml` file |

## Session lifecycle

| Command | Response on stdout | How to read |
|---|---|---|
| `session create` | Text on stdout with key/value lines, including `kobitonSessionId: <id>` | `grep` or string-match the `kobitonSessionId:` line |
| `session ping` | Exit code 0 = alive, non-zero = expired | Trust exit status; don't parse stdout |
| `session end` | Text confirmation | No parsing needed |

## Device / file / app / test

| Command | Response on stdout | How to read |
|---|---|---|
| `device adb-shell <cmd>` | Raw stdout from the on-device shell. Shape depends on `<cmd>` - KV pairs (`dumpsys battery`), single line (`getprop`), multi-line table (`pm list`, `ps`), or free text (`logcat`) | (a) For single-value extractions, `grep` or `awk` the line. (b) For multi-line output, save to artifact then parse. (c) **Gotcha:** exit code 0 does NOT mean the inner command succeeded - adb returns 0 as long as it could deliver the command; check stderr or look for error strings in stdout. |
| `device screen` | JPEG image bytes - check `--help` for output flag (e.g., `--out`) | Redirect or use the documented output flag |
| `device forward`, `device ps`, `file list` | Plain text on stdout | Read directly |
| `file push`, `file pull` | Text confirmation; non-zero exit on failure | Surface failures by exit code |
| `app run <app-id>` | Text confirmation; the app launches on the device | Continue interacting after launch |
| `test run` | Streaming test-runner output | Run with `run_in_background: true`; parse the final summary block |

## See also

- [`../SKILL.md`](../SKILL.md) - the orchestration skill that consumes this reference.
- [`../SKILL.md#command-reference`](../SKILL.md#command-reference) - the inverse lookup (intent -> command shape) that complements this file (command -> response shape).
- [Appium 2.x documentation](https://appium.io/docs/en/2.0/) - canonical W3C WebDriver / Appium endpoint response schemas the CLI thinly wraps.
