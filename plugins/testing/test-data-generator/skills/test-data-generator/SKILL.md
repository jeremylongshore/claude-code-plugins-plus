---
name: generating-test-data
description: |
  This skill enables Claude to generate realistic test data for software development. It uses the test-data-generator plugin to create users, products, orders, and custom schemas for comprehensive testing. Use this skill when you need to populate databases, simulate user behavior, or create fixtures for automated tests. Trigger phrases include "generate test data", "create fake users", "populate database", "generate product data", "create test orders", or "generate data based on schema". This skill is especially useful for populating testing environments or creating sample data for demonstrations.
---

## Overview

This skill empowers Claude to generate realistic and diverse test data, streamlining software testing and development workflows. It leverages the test-data-generator plugin to produce data sets tailored to your specific needs, from user profiles to complex business transactions.

## How It Works

1. **Identify Data Requirements**: Claude analyzes your request to determine the type and volume of test data required (e.g., users, products, orders, custom schemas).
2. **Generate Data**: Claude uses the test-data-generator plugin to create realistic test data based on your specifications.
3. **Present Data**: Claude presents the generated data in a suitable format, such as JSON or a data file, ready for use in your testing environment.

## When to Use This Skill

This skill activates when you need to:
- Generate a large number of realistic user profiles for testing authentication and authorization.
- Create a dataset of products with varying attributes for testing e-commerce functionality.
- Simulate order placements and transactions for performance testing and load testing.
- Populate a database with realistic data for demonstration or training purposes.
- Generate data that adheres to a specific schema or data model.

## Examples

### Example 1: Generating User Data

User request: "Generate 500 test users with realistic names, emails, and addresses."

The skill will:
1. Invoke the test-data-generator plugin to create 500 user records.
2. Populate each record with realistic names, email addresses, and physical addresses.
3. Provide the generated data in JSON format.

### Example 2: Creating Product Data

User request: "Create product test data including name, description, price, and category for 100 different products."

The skill will:
1. Utilize the test-data-generator plugin to generate 100 product records.
2. Populate each product with relevant details like name, description, price, and category.
3. Deliver the data in a structured format suitable for database insertion.

## Best Practices

- **Schema Definition**: Provide a clear schema or data model when generating custom data to ensure accuracy and consistency.
- **Locale Considerations**: Specify the desired locale when generating data that is sensitive to regional variations (e.g., names, addresses, phone numbers).
- **Seed Values**: Use seed values for reproducible test data generation, ensuring consistency across multiple runs.

## Integration

This skill can be integrated with other plugins, such as database management tools, to directly populate databases with the generated test data. It can also be used in conjunction with API testing tools to generate realistic request payloads.