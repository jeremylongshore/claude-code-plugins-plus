---
name: modeling-nosql-data
description: |
  This skill enables Claude to design NoSQL data models. It activates when the user requests assistance with NoSQL database design, including schema creation, data modeling for MongoDB or DynamoDB, or defining document structures. Use this skill when the user mentions "NoSQL data model", "design MongoDB schema", "create DynamoDB table", or similar phrases related to NoSQL database architecture. It assists in understanding NoSQL modeling principles like embedding vs. referencing, access pattern optimization, and sharding key selection.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill facilitates the design of efficient NoSQL data models, providing guidance on schema creation, denormalization strategies, and query optimization for document and key-value databases. It helps users translate their data requirements into production-ready NoSQL implementations.

## How It Works

1. **Identify Database Type**: Determines the target NoSQL database (e.g., MongoDB, DynamoDB).
2. **Analyze Data Requirements**: Understands the data entities, attributes, and relationships.
3. **Design Data Model**: Creates a NoSQL data model based on the identified database type and data requirements, considering embedding vs. referencing and access patterns.
4. **Suggest Schema Definition**: Provides a schema definition or table structure based on the designed data model.

## When to Use This Skill

This skill activates when you need to:
- Design a new NoSQL database schema.
- Optimize an existing NoSQL data model for performance.
- Translate relational data models to NoSQL.
- Choose appropriate sharding keys for a NoSQL database.
- Generate MongoDB or DynamoDB schema definitions.

## Examples

### Example 1: Designing a MongoDB Schema for an E-commerce Application

User request: "Design a MongoDB schema for an e-commerce application, focusing on products and customers."

The skill will:
1. Analyze the data requirements for products and customers, considering attributes like product name, price, description, customer ID, name, and address.
2. Design a MongoDB schema with embedded product reviews and customer order history, optimizing for common query patterns.

### Example 2: Creating a DynamoDB Table for a Social Media Platform

User request: "Create a DynamoDB table for storing social media posts, considering high read and write throughput."

The skill will:
1. Analyze the data requirements for social media posts, considering attributes like user ID, timestamp, content, and likes.
2. Design a DynamoDB table with appropriate primary and secondary indexes for efficient querying based on user ID and timestamp.

## Best Practices

- **Denormalization**: Embed related data when reads are more frequent than writes.
- **Access Patterns**: Optimize the data model for the most common query patterns.
- **Sharding**: Choose sharding keys that distribute data evenly across shards.

## Integration

This skill can be integrated with other plugins for generating code based on the designed data model, such as generating MongoDB queries or DynamoDB API calls.