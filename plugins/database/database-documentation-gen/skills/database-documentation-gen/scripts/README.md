# Scripts

Bundled resources for database-documentation-gen skill

- [x] **init_db_docs.py**: Script to initialize the database documentation generation process, handling authentication and connection details.
- [x] **validate_config.py**: Script to validate the configuration file for the documentation generation process, ensuring all required parameters are present and valid.
- [x] **erd_generator.py**: Script to generate ERD diagrams from the database schema in Mermaid, PlantUML, and DBML formats.

## Usage

All scripts are executable Python scripts that can be run directly:

```bash
# Initialize a new database documentation project
python ${CLAUDE_SKILL_DIR}/scripts/init_db_docs.py --project my_database --db-type postgresql

# Validate the configuration
python ${CLAUDE_SKILL_DIR}/scripts/validate_config.py --config ./my_database/db_docs_config.json

# Generate ERD diagrams
python ${CLAUDE_SKILL_DIR}/scripts/erd_generator.py --config ./my_database/db_docs_config.json --format all
```

## Requirements

These scripts use only Python standard library modules, so no additional dependencies are required.
