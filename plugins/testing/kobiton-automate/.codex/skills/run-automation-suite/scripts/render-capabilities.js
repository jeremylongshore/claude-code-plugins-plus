import {readFileSync} from 'node:fs'
import {resolve} from 'node:path'
import {parseArgs} from 'node:util'
import ejs from 'ejs'

const TEMPLATE_PATH = resolve(
  import.meta.dirname, '..', 'references', 'templates', 'appium.ejs'
)

const {values: flags} = parseArgs({
  options: {
    platformName:       {type: 'string'},
    udid:               {type: 'string'},
    deviceName:         {type: 'string'},
    platformVersion:    {type: 'string'},
    automationName:     {type: 'string'},
    app:                {type: 'string'},
    browserName:        {type: 'string'},
    testingType:        {type: 'string', default: 'app'},
    aiToolName:         {type: 'string'},
    newCommandTimeout:  {type: 'string'},
    scriptlessCapture:  {type: 'boolean'}
  },
  strict: false
})

// AI workspace identifier shipped on every wdio session as
// `kobiton:aiToolName`, used by Kobiton for adoption analytics
// (KOB-52724). Resolution order (mirrors kobiton-cli's
// resolve_ai_tool_name() in k repo — keep these in lock-step):
//   1. --aiToolName CLI arg — explicit override at the call site.
//      Always wins. `--aiToolName ""` opts out (no capability emitted).
//   2. KOBITON_AI_TOOL_NAME env var — host plugin can configure once
//      per process (e.g. a future Gemini/Codex skill's wrapper).
//   3. Well-known host-runtime markers, in order (verified 2026-05-19):
//        - CLAUDECODE=1     → "Claude"  (Anthropic Claude Code)
//        - COPILOT_CLI=1    → "Copilot" (GitHub Copilot CLI)
//        - GEMINI_CLI=1     → "Gemini"  (Google Gemini CLI)
//        - CODEX_THREAD_ID  → "Codex"   (OpenAI Codex CLI sets this
//          to the active thread UUID; CODEX_CLI=1 is accepted for
//          manual override but Codex itself does not set it)
//   4. Empty string — emits no `kobiton:aiToolName` capability.
//      Better than mis-attributing to a default tool.
function detectAiToolName() {
  if (process.env.CLAUDECODE) return 'Claude'
  if (process.env.COPILOT_CLI) return 'Copilot'
  if (process.env.GEMINI_CLI) return 'Gemini'
  if (process.env.CODEX_CLI || process.env.CODEX_THREAD_ID) return 'Codex'
  return ''
}
const aiToolName = flags.aiToolName !== undefined
  ? flags.aiToolName
  : (process.env.KOBITON_AI_TOOL_NAME ?? detectAiToolName())

// Validate required flags
const errors = []
if (!flags.platformName) errors.push('--platformName is required')
if (!flags.udid) errors.push('--udid is required')
if (!flags.deviceName) errors.push('--deviceName is required')
if (!flags.platformVersion) errors.push('--platformVersion is required')
if (flags.testingType === 'app' && !flags.app) {
  errors.push('--app is required when --testingType is app')
}
if (flags.testingType === 'web' && !flags.browserName) {
  errors.push('--browserName is required when --testingType is web')
}
if (errors.length) {
  process.stderr.write(errors.join('\n') + '\n')
  process.exit(1)
}

// Parse --newCommandTimeout: integer seconds. Optional. When omitted the
// capability is not emitted, preserving Appium's default behavior for
// run-automation-suite's existing callers (KOB-53296: drive-automation-session
// uses 1800 so its loop survives human-in-the-loop pauses).
let newCommandTimeout = 0
if (flags.newCommandTimeout !== undefined) {
  const n = Number(flags.newCommandTimeout)
  if (!Number.isInteger(n) || n <= 0) {
    process.stderr.write('--newCommandTimeout must be a positive integer (seconds)\n')
    process.exit(1)
  }
  newCommandTimeout = n
}

// Build template variables: CLI flags + hardcoded defaults
const templateVars = {
  // From CLI
  platformName: flags.platformName,
  udid: flags.udid,
  deviceName: flags.deviceName,
  platformVersion: flags.platformVersion,
  automationName: flags.automationName || '',
  app: flags.app || '',
  browser: flags.browserName || '',
  testingType: flags.testingType,
  newCommandTimeout,
  scriptlessCapture: Boolean(flags.scriptlessCapture),

  // Hardcoded defaults
  sessionName: 'Automation test session',
  sessionDescription: '',
  orientation: 'portrait',
  captureScreenshots: true,
  showCleanUpDeviceOnExit: true,
  cleanUpDeviceOnExit: false,
  useSpecificDevice: true,
  deviceGroup: 'ORGANIZATION',
  showDeviceGroup: false,

  // Resolved above (CLI flag > env > runtime marker, empty string when none match)
  aiToolName
}

// Render template and output JSON
try {
  const template = readFileSync(TEMPLATE_PATH, 'utf8')
  const rendered = ejs.render(template, templateVars)

  // Clean trailing commas before closing brace (EJS conditionals can leave them)
  const cleaned = rendered.replace(/,(\s*})/g, '$1')

  // Validate it's valid JSON
  const caps = JSON.parse(cleaned)
  process.stdout.write(JSON.stringify(caps, null, 2) + '\n')
} catch (err) {
  process.stderr.write(`Template render error: ${err.message}\n`)
  process.exit(1)
}
