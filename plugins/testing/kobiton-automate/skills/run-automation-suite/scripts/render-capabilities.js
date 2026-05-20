import {readFileSync} from 'fs'
import {resolve} from 'path'
import ejs from 'ejs'
import {parseArgs} from 'util'

const TEMPLATE_PATH = resolve(
  import.meta.dirname, '..', 'references', 'templates', 'appium.ejs'
)

const {values: flags} = parseArgs({
  options: {
    platformName:    {type: 'string'},
    udid:            {type: 'string'},
    deviceName:      {type: 'string'},
    platformVersion: {type: 'string'},
    automationName:  {type: 'string'},
    app:             {type: 'string'},
    browserName:     {type: 'string'},
    testingType:     {type: 'string', default: 'app'}
  },
  strict: false
})

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

  // Hardcoded defaults
  sessionName: 'Automation test session',
  sessionDescription: '',
  orientation: 'portrait',
  captureScreenshots: true,
  showCleanUpDeviceOnExit: true,
  cleanUpDeviceOnExit: false,
  useSpecificDevice: true,
  deviceGroup: 'ORGANIZATION',
  showDeviceGroup: false
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
