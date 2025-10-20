# Mobile App Tester

Mobile app test automation with Appium, Detox, XCUITest - test iOS and Android apps.

## Installation

```bash
/plugin install mobile-app-tester@claude-code-plugins-plus
```

## Usage

```bash
/mobile-test
# or shortcut
/mt
```

## Features

- **Cross-Platform**: iOS and Android support
- **Multiple Frameworks**: Detox, Appium, XCUITest, Espresso
- **Gesture Testing**: Swipe, tap, pinch, rotate
- **Device Farms**: AWS Device Farm, BrowserStack Mobile
- **Performance Testing**: Launch time, memory, battery
- **Platform-Specific**: Handle iOS/Android differences

## Example Workflow

```bash
# Generate mobile app tests
/mobile-test

# Claude creates:
#  E2E test suite
#  Page object models
#  Gesture handling
#  Permission management
#  Platform-specific tests
```

## Supported Platforms

- iOS (Simulator + Real Device)
- Android (Emulator + Real Device)
- React Native
- Native apps

## Testing Frameworks

- Detox (React Native)
- Appium (Cross-platform)
- XCUITest (iOS)
- Espresso (Android)
- Maestro

## Files

- `commands/mobile-test.md` - Mobile testing command

## License

MIT
