---
name: windsurf-release-automation
description: |
  Automate release processes with semantic versioning. Activate when users mention
  "release automation", "version bump", "changelog generation", "semantic release",
  or "publish release". Handles release engineering automation.
allowed-tools: Read,Write,Edit,Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Release Automation

Automate release processes with semantic versioning and changelog generation.

## Directory Structure

```
project-root/
    CHANGELOG.md                     # Release history
        # Version entries
        # Change categories
        # Breaking changes
        # Contributors

    package.json                     # Version source
        # Current version
        # Release scripts
        # Publish configuration

    .releaserc.js                    # Semantic release config
        # Branch configuration
        # Plugin settings
        # Commit analysis rules

    .windsurf/
        release/
            templates/
                changelog-entry.md       # Changelog template
                    # Version header format
                    # Category sections
                    # Link formatting

                release-notes.md         # Release notes template
                    # Summary section
                    # Highlights
                    # Migration guide

            config/
                version-rules.json       # Version bump rules
                    # Commit type to version mapping
                    # Breaking change detection
                    # Pre-release handling

                publish-config.json      # Publishing settings
                    # Registry configuration
                    # Artifact definitions
                    # Distribution channels

            history/
                releases.json            # Release history log
                    # Version and dates
                    # Commit ranges
                    # Artifact links
```

## Release Features

### Version Management
- Semantic version calculation
- Pre-release tagging
- Version consistency checks
- Git tag management

### Changelog Generation
- Commit analysis
- Category grouping
- Breaking change highlighting
- Contributor attribution

## Configuration Steps

1. **Configure Version Strategy**
   - Define commit conventions
   - Set branch policies
   - Configure pre-release handling

2. **Set Up Automation**
   - Install release tools
   - Configure CI integration
   - Set up publishing

3. **Execute Release**
   - Trigger release workflow
   - Review generated changelog
   - Verify published artifacts

## Success Criteria

- Correct semantic version tagging
- Comprehensive changelogs
- 50% reduction in release cycle time
