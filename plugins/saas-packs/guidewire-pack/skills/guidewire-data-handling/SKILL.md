---
name: guidewire-data-handling
description: |
  Data handling for Guidewire: entity management, data migration, batch operations, and governance.
  Trigger: "guidewire data handling", "data-handling".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Data Handling

## Overview

Entity management via Gosu: create, update, delete with proper transaction handling. Data migration with ETL tools and batch processes. Staging tables for bulk imports. GDPR: implement data purge rules in Gosu, use anonymization for test data.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
