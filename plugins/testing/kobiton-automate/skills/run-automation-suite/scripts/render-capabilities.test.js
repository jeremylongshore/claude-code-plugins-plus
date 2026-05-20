import {describe, it, expect} from 'vitest'
import {execFileSync} from 'child_process'
import {resolve} from 'path'

const SCRIPT = resolve(import.meta.dirname, 'render-capabilities.js')

function run(args) {
  const result = execFileSync('node', [SCRIPT, ...args], {
    encoding: 'utf8',
    timeout: 5000
  })
  return JSON.parse(result)
}

function runExpectError(args) {
  try {
    execFileSync('node', [SCRIPT, ...args], {
      encoding: 'utf8',
      timeout: 5000,
      stdio: ['pipe', 'pipe', 'pipe']
    })
    throw new Error('Expected script to fail')
  } catch (err) {
    return {exitCode: err.status, stderr: err.stderr}
  }
}

describe('render-capabilities', () => {
  it('renders app testing capabilities', () => {
    const result = run([
      '--platformName', 'Android',
      '--udid', '21161FDF60051K',
      '--deviceName', 'Pixel 6',
      '--platformVersion', '15',
      '--automationName', 'UiAutomator2',
      '--app', 'kobiton-store:v72116',
      '--testingType', 'app'
    ])

    expect(result['platformName']).toBe('Android')
    expect(result['platformVersion']).toBe('15')
    expect(result['appium:udid']).toBe('21161FDF60051K')
    expect(result['appium:deviceName']).toBe('Pixel 6')
    expect(result['appium:automationName']).toBe('UiAutomator2')
    expect(result['appium:app']).toBe('kobiton-store:v72116')
    expect(result['kobiton:sessionName']).toBe('Automation test session')
    expect(result['kobiton:captureScreenshots']).toBe(true)
    expect(result['kobiton:deviceOrientation']).toBe('portrait')
    expect(result['appium:noReset']).toBe(true)
    expect(result['appium:fullReset']).toBe(false)
    expect(result['browserName']).toBeUndefined()
  })

  it('renders web testing capabilities', () => {
    const result = run([
      '--platformName', 'iOS',
      '--udid', '00008101-0004257E3C30001E',
      '--deviceName', 'iPhone 12',
      '--platformVersion', '16.2',
      '--automationName', 'XCUITest',
      '--browserName', 'safari',
      '--testingType', 'web'
    ])

    expect(result['platformName']).toBe('iOS')
    expect(result['platformVersion']).toBe('16.2')
    expect(result['browserName']).toBe('safari')
    expect(result['appium:app']).toBeUndefined()
    expect(result['appium:automationName']).toBe('XCUITest')
    expect(result['appium:udid']).toBe('00008101-0004257E3C30001E')
    expect(result['appium:deviceName']).toBe('iPhone 12')
  })

  it('fails when required --platformName is missing', () => {
    const {exitCode, stderr} = runExpectError([
      '--udid', 'ABC123',
      '--deviceName', 'Pixel 6',
      '--platformVersion', '15',
      '--testingType', 'app',
      '--app', 'kobiton-store:v1'
    ])

    expect(exitCode).toBe(1)
    expect(stderr).toContain('platformName')
  })

  it('fails when required --udid is missing', () => {
    const {exitCode, stderr} = runExpectError([
      '--platformName', 'Android',
      '--deviceName', 'Pixel 6',
      '--platformVersion', '15',
      '--testingType', 'app',
      '--app', 'kobiton-store:v1'
    ])

    expect(exitCode).toBe(1)
    expect(stderr).toContain('udid')
  })

  it('fails when required --deviceName is missing', () => {
    const {exitCode, stderr} = runExpectError([
      '--platformName', 'Android',
      '--udid', 'ABC123',
      '--platformVersion', '15',
      '--testingType', 'app',
      '--app', 'kobiton-store:v1'
    ])

    expect(exitCode).toBe(1)
    expect(stderr).toContain('deviceName')
  })

  it('fails when required --platformVersion is missing', () => {
    const {exitCode, stderr} = runExpectError([
      '--platformName', 'Android',
      '--udid', 'ABC123',
      '--deviceName', 'Pixel 6',
      '--testingType', 'app',
      '--app', 'kobiton-store:v1'
    ])

    expect(exitCode).toBe(1)
    expect(stderr).toContain('platformVersion')
  })

  it('fails when --testingType is app but --app is missing', () => {
    const {exitCode, stderr} = runExpectError([
      '--platformName', 'Android',
      '--udid', 'ABC123',
      '--deviceName', 'Pixel 6',
      '--platformVersion', '15',
      '--testingType', 'app'
    ])

    expect(exitCode).toBe(1)
    expect(stderr).toContain('app')
  })

  it('fails when --testingType is web but --browserName is missing', () => {
    const {exitCode, stderr} = runExpectError([
      '--platformName', 'iOS',
      '--udid', 'ABC123',
      '--deviceName', 'iPhone 12',
      '--platformVersion', '16.2',
      '--testingType', 'web'
    ])

    expect(exitCode).toBe(1)
    expect(stderr).toContain('browserName')
  })

})
