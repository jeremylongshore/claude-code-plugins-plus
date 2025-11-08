# Skill Scripts

This directory contains optional helper scripts that support this skill's functionality.

## Purpose

Scripts here can be:
- Referenced by the skill for automation
- Used as examples for users
- Executed during skill activation

## Guidelines

- All scripts should be well-documented
- Include usage examples in comments
- Make scripts executable (`chmod +x`)
- Use `#!/bin/bash` or `#!/usr/bin/env python3` shebangs

## Adding Scripts

1. Create script file (e.g., `analyze.sh`, `process.py`)
2. Add documentation header
3. Make executable: `chmod +x script-name.sh`
4. Test thoroughly before committing
