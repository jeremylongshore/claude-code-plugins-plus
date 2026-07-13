# Directory Structure

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
