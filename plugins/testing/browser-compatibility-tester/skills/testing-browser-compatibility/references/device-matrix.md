# Device and Browser Matrix Patterns

Pre-built browser/device/OS matrices for common testing scenarios. Choose the matrix that matches your project's requirements, then customize as needed.

---

## Top 10 Browsers Matrix

Covers the browsers that represent ~95% of global web traffic. Use as the default for most web applications.

```yaml
matrix:
  desktop:
    - { browser: Chrome, version: "latest", os: "Windows 11" }
    - { browser: Chrome, version: "latest", os: "macOS Sonoma" }
    - { browser: Firefox, version: "latest", os: "Windows 11" }
    - { browser: Firefox, version: "latest", os: "macOS Sonoma" }
    - { browser: Safari, version: "17+", os: "macOS Sonoma" }
    - { browser: Edge, version: "latest", os: "Windows 11" }
  mobile:
    - { browser: Safari, device: "iPhone 15", os: "iOS 17" }
    - { browser: Chrome, device: "Pixel 8", os: "Android 14" }
    - { browser: Samsung Internet, device: "Galaxy S24", os: "Android 14" }
    - { browser: Chrome, device: "iPad Pro 12.9", os: "iPadOS 17" }
  viewports:
    - { name: "phone", width: 375, height: 812 }
    - { name: "tablet", width: 768, height: 1024 }
    - { name: "desktop", width: 1280, height: 720 }
    - { name: "widescreen", width: 1920, height: 1080 }
```

### Playwright Config

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  projects: [
    { name: 'chrome-win', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox-win', use: { ...devices['Desktop Firefox'] } },
    { name: 'safari-mac', use: { ...devices['Desktop Safari'] } },
    { name: 'edge-win', use: { channel: 'msedge' } },
    { name: 'iphone-15', use: { ...devices['iPhone 15'] } },
    { name: 'pixel-8', use: { ...devices['Pixel 7'] } }, // Playwright uses 'Pixel 7' profile as the closest match for Pixel 8
    { name: 'ipad-pro', use: { ...devices['iPad Pro 11'] } },
  ],
});
```

---

## Mobile-First Matrix

For applications where mobile traffic exceeds desktop. Prioritizes real-device testing on physical phones and tablets.

```yaml
matrix:
  primary_mobile:
    - { browser: Safari, device: "iPhone 15 Pro", os: "iOS 17" }
    - { browser: Safari, device: "iPhone 14", os: "iOS 16" }
    - { browser: Chrome, device: "Pixel 8", os: "Android 14" }
    - { browser: Chrome, device: "Galaxy S24", os: "Android 14" }
    - { browser: Samsung Internet, device: "Galaxy S24", os: "Android 14" }
    - { browser: Chrome, device: "Galaxy A54", os: "Android 13" }  # mid-range
  tablets:
    - { browser: Safari, device: "iPad Pro 12.9 (6th gen)", os: "iPadOS 17" }
    - { browser: Chrome, device: "Galaxy Tab S9", os: "Android 14" }
  desktop_baseline:
    - { browser: Chrome, version: "latest", os: "Windows 11" }
    - { browser: Safari, version: "17+", os: "macOS Sonoma" }
  viewports:
    - { name: "small-phone", width: 360, height: 640 }
    - { name: "phone", width: 393, height: 852 }
    - { name: "large-phone", width: 430, height: 932 }
    - { name: "tablet-portrait", width: 768, height: 1024 }
    - { name: "tablet-landscape", width: 1024, height: 768 }
```

### Kobiton Real-Device Config

```json
[
  {
    "platformName": "iOS",
    "appium:deviceName": "iPhone 15 Pro",
    "appium:platformVersion": "17",
    "browserName": "Safari",
    "kobiton:options": { "deviceGroup": "KOBITON", "captureScreenshots": true }
  },
  {
    "platformName": "Android",
    "appium:deviceName": "Galaxy S24",
    "appium:platformVersion": "14",
    "browserName": "chrome",
    "kobiton:options": { "deviceGroup": "KOBITON", "captureScreenshots": true }
  },
  {
    "platformName": "Android",
    "appium:deviceName": "Galaxy A54",
    "appium:platformVersion": "13",
    "browserName": "chrome",
    "kobiton:options": { "deviceGroup": "KOBITON", "captureScreenshots": true }
  }
]
```

---

## Enterprise Matrix

For B2B applications targeting corporate environments. Includes older browser versions and locked-down enterprise configurations.

```yaml
matrix:
  desktop_current:
    - { browser: Chrome, version: "latest", os: "Windows 11" }
    - { browser: Edge, version: "latest", os: "Windows 11" }
    - { browser: Firefox, version: "latest", os: "Windows 11" }
    - { browser: Safari, version: "17+", os: "macOS Sonoma" }
  desktop_legacy:
    - { browser: Chrome, version: "latest-1", os: "Windows 10" }
    - { browser: Edge, version: "latest-1", os: "Windows 10" }
    - { browser: Firefox ESR, version: "115", os: "Windows 10" }
    - { browser: Safari, version: "16", os: "macOS Ventura" }
  mobile_byod:
    - { browser: Safari, device: "iPhone 14", os: "iOS 16" }
    - { browser: Chrome, device: "Pixel 7", os: "Android 13" }
  viewports:
    - { name: "laptop", width: 1366, height: 768 }    # most common enterprise
    - { name: "desktop", width: 1920, height: 1080 }
    - { name: "phone", width: 375, height: 812 }
```

### BrowserStack Config

```json
[
  {
    "browserName": "Chrome",
    "bstack:options": {
      "os": "Windows", "osVersion": "11",
      "browserVersion": "latest"
    }
  },
  {
    "browserName": "Chrome",
    "bstack:options": {
      "os": "Windows", "osVersion": "10",
      "browserVersion": "latest-1"
    }
  },
  {
    "browserName": "Edge",
    "bstack:options": {
      "os": "Windows", "osVersion": "11",
      "browserVersion": "latest"
    }
  },
  {
    "browserName": "Firefox",
    "bstack:options": {
      "os": "Windows", "osVersion": "10",
      "browserVersion": "115.0"
    }
  }
]
```

---

## Kobiton Real-Device Matrix

Optimized for Kobiton's physical device lab. Tests on actual hardware to catch rendering, touch, and performance issues that emulators miss.

```yaml
matrix:
  ios_devices:
    - { device: "iPhone 15 Pro Max", os: "17.4", browser: Safari }
    - { device: "iPhone 15", os: "17.2", browser: Safari }
    - { device: "iPhone 14", os: "16.6", browser: Safari }
    - { device: "iPhone SE (3rd gen)", os: "17.0", browser: Safari }  # small screen
    - { device: "iPad Pro 12.9 (6th gen)", os: "17.2", browser: Safari }
  android_devices:
    - { device: "Galaxy S24 Ultra", os: "14", browser: Chrome }
    - { device: "Galaxy S23", os: "14", browser: Chrome }
    - { device: "Pixel 8 Pro", os: "14", browser: Chrome }
    - { device: "Galaxy A54", os: "13", browser: Chrome }     # mid-range
    - { device: "Galaxy Tab S9", os: "14", browser: Chrome }
  focus_areas:
    - touch_responsiveness     # real touch vs emulated
    - scroll_performance       # 60fps on actual hardware
    - camera_api               # getUserMedia on real devices
    - geolocation              # GPS hardware accuracy
    - network_conditions       # carrier throttling (3G/4G/5G)
    - battery_impact           # performance under low battery
```

### Device Query (check availability before test run)

```bash
# Get online iOS devices
curl -u "$KOBITON_USERNAME:$KOBITON_API_KEY" \
  "https://api.kobiton.com/v1/devices?isOnline=true&platformName=iOS" \
  | jq '.devices[] | {id, deviceName, platformVersion, isOnline}'

# Get online Android devices with specific OS
curl -u "$KOBITON_USERNAME:$KOBITON_API_KEY" \
  "https://api.kobiton.com/v1/devices?isOnline=true&platformName=Android&platformVersion=14" \
  | jq '.devices[] | {id, deviceName, platformVersion}'
```

---

## Choosing the Right Matrix

| Project Type | Recommended Matrix | Key Consideration |
|-------------|-------------------|-------------------|
| Consumer web app | Top 10 Browsers | Cover the 95% traffic baseline |
| Mobile-first / PWA | Mobile-First | Real devices for touch, GPS, camera |
| B2B / Enterprise SaaS | Enterprise | Windows 10 + Firefox ESR + locked viewports |
| E-commerce | Top 10 + Mobile-First | Combine both; checkout flows need real device validation |
| Regulatory / healthcare | Enterprise + Kobiton Real-Device | Compliance often requires proof on actual hardware |

### Expanding a Matrix

Start with the smallest matrix that covers your audience, then add devices when:

- Analytics show >2% traffic from an uncovered browser/device
- A customer reports an issue on a specific device
- You add features that use device-specific APIs (camera, GPS, NFC)
- You need to certify compliance on specific hardware
