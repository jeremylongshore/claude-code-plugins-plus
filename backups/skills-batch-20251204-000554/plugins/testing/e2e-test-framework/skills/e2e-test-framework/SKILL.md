---
name: generating-end-to-end-tests
description: |
  This skill enables Claude to generate end-to-end (E2E) tests for web applications. It leverages Playwright, Cypress, or Selenium to automate browser interactions and validate user workflows. Use this skill when the user requests to "create E2E tests", "generate end-to-end tests", or asks for help with "browser-based testing". The skill is particularly useful for testing user registration, login flows, shopping cart functionality, and other multi-step processes within a web application. It supports cross-browser testing and can be used to verify the responsiveness of web applications on different devices.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill automates the creation of end-to-end tests, which simulate real user interactions with a web application. By generating tests using Playwright, Cypress, or Selenium, Claude ensures comprehensive coverage of critical user workflows.

## How It Works

1. **Identify User Workflow**: Claude analyzes the user's request to determine the specific user workflow to be tested (e.g., user registration, product checkout).
2. **Generate Test Script**: Based on the identified workflow, Claude generates a test script using Playwright, Cypress, or Selenium. The script includes steps to navigate the web application, interact with elements, and assert expected outcomes.
3. **Configure Test Environment**: Claude configures the test environment, including browser selection (Chrome, Firefox, Safari, Edge) and any necessary dependencies.

## When to Use This Skill

This skill activates when you need to:
- Create end-to-end tests for a specific user flow (e.g., "create e2e tests for user login").
- Generate browser-based tests for a web application.
- Automate testing of multi-step processes in a web application (e.g., "generate end-to-end tests for adding an item to a shopping cart and completing the checkout process").

## Examples

### Example 1: Testing User Registration

User request: "Create E2E tests for the user registration workflow on my website."

The skill will:
1. Generate a Playwright script that automates the user registration process, including filling out the registration form, submitting it, and verifying the successful registration message.
2. Configure the test to run in Chrome and Firefox.

### Example 2: Testing Shopping Cart Functionality

User request: "Generate end-to-end tests for adding an item to a shopping cart and completing the checkout process."

The skill will:
1. Create a Cypress script that simulates adding a product to the shopping cart, navigating to the checkout page, entering shipping and payment information, and submitting the order.
2. Include assertions to verify that the correct product is added to the cart, the order total is accurate, and the order confirmation page is displayed.

## Best Practices

- **Specificity**: Provide clear and specific instructions regarding the user workflow to be tested.
- **Framework Choice**: If you have a preference for Playwright, Cypress, or Selenium, specify it in your request. Otherwise, Playwright will be used by default.
- **Environment Details**: Specify any relevant environment details, such as the target browser and the URL of the web application.

## Integration

This skill can be used in conjunction with other plugins to set up the web application, deploy it to a testing environment, and report test results.