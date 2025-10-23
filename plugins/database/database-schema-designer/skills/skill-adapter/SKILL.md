---
name: designing-database-schemas
description: |
  This skill enables Claude to design and visualize database schemas. It leverages normalization guidance (1NF through BCNF), relationship mapping, and ERD generation to create efficient and well-structured databases. Use this skill when the user requests to "design a database schema", "create a database model", "generate an ERD", "normalize a database", or needs help with "database design best practices". The skill is triggered by terms like "database schema", "ERD diagram", "database normalization", and "relational database design".
---

## Overview

This skill assists in designing robust and normalized database schemas. It provides guidance on normalization principles, helps map relationships between entities, generates ERD diagrams for visualization, and ultimately produces SQL CREATE statements.

## How It Works

1. **Schema Definition**: Claude analyzes the user's request to understand the application's data requirements.
2. **Normalization & Relationship Mapping**: Claude applies normalization principles (1NF to BCNF) and defines relationships between entities (one-to-one, one-to-many, many-to-many).
3. **ERD Generation**: Claude generates a Mermaid diagram representing the Entity-Relationship Diagram.
4. **SQL Generation**: Claude creates SQL CREATE statements for the tables, columns, indexes, and constraints.

## When to Use This Skill

This skill activates when you need to:
- Design a new database schema from scratch.
- Normalize an existing database schema.
- Generate an ERD diagram for a database.
- Create SQL CREATE statements for a database.

## Examples

### Example 1: Designing a Social Media Database

User request: "Design a database schema for a social media application with users, posts, and comments."

The skill will:
1. Design tables for users, posts, and comments, including relevant attributes (e.g., user_id, username, post_id, content, timestamp).
2. Define relationships between the tables (e.g., one user can have many posts, one post can have many comments).
3. Generate an ERD diagram visualizing the relationships.
4. Create SQL CREATE TABLE statements for the tables, including primary keys, foreign keys, and indexes.

### Example 2: Normalizing an E-commerce Database

User request: "Normalize a database schema for an e-commerce application with customers, orders, and products."

The skill will:
1. Analyze the existing schema for normalization violations.
2. Decompose tables to eliminate redundancy and improve data integrity.
3. Create new tables and relationships to achieve a normalized schema (e.g., separating product details into a separate table).
4. Generate SQL CREATE TABLE statements for the new tables and ALTER TABLE statements to modify existing tables.

## Best Practices

- **Normalization**: Always aim for at least 3NF to minimize data redundancy and improve data integrity. Consider BCNF for more complex scenarios.
- **Indexing**: Add indexes to frequently queried columns to improve query performance.
- **Relationship Integrity**: Use foreign keys to enforce referential integrity and prevent orphaned records.

## Integration

This skill can be integrated with other Claude Code plugins, such as a SQL execution plugin, to automatically create the database schema in a database server. It can also work with a documentation plugin to generate documentation for the database schema.