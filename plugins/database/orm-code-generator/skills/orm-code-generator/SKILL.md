---
name: generating-orm-code
description: |
  This skill enables Claude to generate ORM models and database schemas. It is triggered when the user requests the creation of ORM models, database schemas, or wishes to generate code for interacting with databases. The skill supports various ORMs including TypeORM, Prisma, Sequelize, SQLAlchemy, Django ORM, Entity Framework, and Hibernate. Use this skill when the user mentions terms like "ORM model", "database schema", "generate entities", "create migrations", or specifies a particular ORM framework like "TypeORM entities" or "SQLAlchemy models". It facilitates both database-to-code and code-to-database schema generation.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to automate the creation of Object-Relational Mapping (ORM) models and database schemas, significantly accelerating backend development. It handles generating code for various ORM frameworks, simplifying database interactions.

## How It Works

1. **Identify ORM and Language**: The skill parses the user's request to determine the target ORM framework (e.g., TypeORM, SQLAlchemy) and programming language (e.g., TypeScript, Python).
2. **Schema/Model Definition**: Based on the request, the skill either interprets an existing database schema or defines a new schema based on provided model specifications.
3. **Code Generation**: The skill generates the corresponding ORM model code, including entities, relationships, and any necessary configuration files, tailored to the chosen ORM framework.

## When to Use This Skill

This skill activates when you need to:
- Create ORM models from a database schema.
- Generate a database schema from existing ORM models.
- Generate model code for a specific ORM framework (e.g., TypeORM, Prisma).

## Examples

### Example 1: Generating TypeORM entities

User request: "Generate TypeORM entities for a blog with users, posts, and comments, including relationships and validation rules."

The skill will:
1. Generate TypeScript code defining TypeORM entities for `User`, `Post`, and `Comment`, including properties, relationships (e.g., one-to-many), and validation decorators.
2. Output the generated code, ready to be integrated into a TypeORM project.

### Example 2: Creating a SQLAlchemy schema

User request: "Create a SQLAlchemy schema for an e-commerce application with products, categories, and orders."

The skill will:
1. Generate Python code defining SQLAlchemy models for `Product`, `Category`, and `Order`, including relationships (e.g., many-to-one), data types, and primary/foreign key constraints.
2. Output the generated code, ready to be used with SQLAlchemy.

## Best Practices

- **Specificity**: Be as specific as possible about the desired ORM framework and data model.
- **Relationships**: Clearly define relationships between entities (e.g., one-to-many, many-to-many).
- **Validation**: Specify validation rules to ensure data integrity.

## Integration

This skill integrates with other code generation tools and plugins within Claude Code, allowing for seamless integration into existing projects and workflows. It can be used in conjunction with database migration tools to create and manage database schemas.