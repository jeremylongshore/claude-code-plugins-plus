# Changelog

## 1.0.2 - 2026-04-02

- Improved the accuracy of fetching Appium capabilities supported by Kobiton
- Implemented a reliable method for correlating active sessions with their corresponding device IDs


## 1.0.1 - 2026-04-01

- Added a user confirmation prompt when selecting an app version for testing
- Enabled Claude to open active test sessions for live screen previews


## 1.0.0 - 2026-03-31

- Initial release with 12 MCP tools and 1 skill
- Authentication: OAuth 2.1 with automatic browser login (primary), API key auth for CI/headless (alternative)
- Device management: list, status, reserve, terminate reservation
- Session management: list, details, artifacts, terminate
- App management: list, details, upload to store, confirm to upload
- Skills: run-automation-suite to parse capabilities from local Appium scripts and execute them directly (supports Node.js, Python, .NET, Java)
