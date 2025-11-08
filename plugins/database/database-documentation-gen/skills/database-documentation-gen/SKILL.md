---
name: generating-database-documentation
description: |
  This skill enables Claude to automatically generate comprehensive documentation for existing database schemas using the database-documentation-gen plugin. It is triggered when the user requests database documentation, ERD diagrams, or a data dictionary. The plugin supports multiple database engines and generates documentation that includes ERD diagrams, table relationships, column descriptions, indexes, triggers, stored procedures, and interactive HTML documentation. Use this skill when you need to document existing database schemas for team onboarding, architectural reviews, or data governance purposes. The trigger terms include "database documentation", "ERD diagram", "data dictionary", and `/db-docs`.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to create detailed database documentation from existing database schemas. It leverages the database-documentation-gen plugin to automate the process, saving time and ensuring consistency. The generated documentation includes ERD diagrams, table relationships, and detailed information about database objects.

## How It Works

1. **Activation**: Claude recognizes the user's request for database documentation, ERD diagrams, or a data dictionary, triggering the database-documentation-gen plugin.
2. **Schema Analysis**: The plugin connects to the specified database and analyzes its schema, extracting information about tables, columns, relationships, indexes, triggers, and stored procedures.
3. **Documentation Generation**: The plugin generates comprehensive documentation in various formats, including ERD diagrams, data dictionaries, and interactive HTML documentation.

## When to Use This Skill

This skill activates when you need to:
- Generate documentation for a new or existing database.
- Create ERD diagrams for architectural reviews.
- Produce a data dictionary for data governance purposes.
- Onboard new team members to a database project.

## Examples

### Example 1: Documenting an Existing Database

User request: "Generate database documentation for the 'users' database."

The skill will:
1. Activate the database-documentation-gen plugin.
2. Connect to the 'users' database and analyze its schema.
3. Generate comprehensive documentation, including ERD diagrams and a data dictionary.

### Example 2: Creating an ERD Diagram

User request: "Create an ERD diagram for the 'orders' database."

The skill will:
1. Activate the database-documentation-gen plugin.
2. Connect to the 'orders' database and analyze its schema.
3. Generate an ERD diagram illustrating the relationships between tables in the 'orders' database.

## Best Practices

- **Database Credentials**: Ensure Claude has the necessary database credentials to access the database schema.
- **Database Selection**: Clearly specify the database for which documentation should be generated.
- **Output Format**: Consider specifying the desired output format for the documentation (e.g., HTML, Markdown).

## Integration

This skill can be integrated with other plugins to further enhance the documentation process. For example, it can be combined with a diagramming plugin to customize the ERD diagrams or with a document generation plugin to create more sophisticated documentation formats.