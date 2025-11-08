---
name: fuzzing-apis
description: |
  This skill enables Claude to perform automated fuzz testing on APIs to discover vulnerabilities, crashes, and unexpected behavior. It leverages malformed inputs, boundary values, and random payloads to generate comprehensive fuzz test suites. Use this skill when you need to identify potential SQL injection, XSS, command injection vulnerabilities, input validation failures, and edge cases in APIs. Trigger this skill by requesting fuzz testing, vulnerability scanning, or security analysis of an API. The skill is invoked using the `/fuzz-api` command.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill allows Claude to conduct automated fuzz testing on REST APIs. It identifies potential security flaws and robustness issues by injecting various malformed inputs, boundary values, and random data.

## How It Works

1. **Input Generation**: The skill generates a diverse set of test inputs, including malformed data, boundary values, and random payloads.
2. **API Interaction**: It sends these inputs to the specified API endpoints.
3. **Result Analysis**: It analyzes the API's responses and behavior to identify vulnerabilities, crashes, and unexpected results, such as SQL injection errors or XSS vulnerabilities.

## When to Use This Skill

This skill activates when you need to:
- Identify potential security vulnerabilities in an API.
- Test the robustness of an API against unexpected inputs.
- Ensure proper input validation is implemented in an API.

## Examples

### Example 1: Discovering SQL Injection Vulnerability

User request: "Fuzz test the /users endpoint for SQL injection vulnerabilities."

The skill will:
1. Generate SQL injection payloads.
2. Send these payloads to the /users endpoint.
3. Analyze the API's responses for SQL errors or unexpected behavior indicating a SQL injection vulnerability.

### Example 2: Testing Input Validation

User request: "Fuzz test the /products endpoint to check for input validation issues with price and quantity parameters."

The skill will:
1. Generate malformed inputs for price and quantity (e.g., negative values, extremely large numbers, non-numeric characters).
2. Send these inputs to the /products endpoint.
3. Analyze the API's responses for errors or unexpected behavior, indicating input validation failures.

## Best Practices

- **Specificity**: Be specific about the API endpoint or parameters you want to fuzz.
- **Context**: Provide context about the expected behavior of the API.
- **Iteration**: Run multiple fuzzing sessions with different input sets for thorough testing.

## Integration

This skill can be used in conjunction with other security analysis tools to provide a more comprehensive assessment of an API's security posture. It can also be integrated into a CI/CD pipeline to automate security testing.