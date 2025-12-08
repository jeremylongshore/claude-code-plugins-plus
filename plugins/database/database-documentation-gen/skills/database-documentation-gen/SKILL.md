---
name: database-documentation-gen
description: |
  Generates comprehensive database documentation including ERD diagrams, data dictionaries,
  and schema analysis. Creates Mermaid, PlantUML, and DBML diagrams from database schemas.
  Use when documenting databases, creating ERDs, or generating data dictionaries.
  Trigger with "document database", "create ERD", "generate data dictionary".
allowed-tools: Read, Write, Edit, Bash, Glob
version: 1.0.0
---

# Database Documentation Generator

Automatically generates comprehensive documentation for database schemas, including ERD diagrams in multiple formats.

## Overview

This skill creates detailed database documentation using bundled Python scripts. It initializes documentation projects, validates configurations, and generates ERD diagrams in Mermaid, PlantUML, and DBML formats. Perfect for database architects, developers, and teams needing to document their data models.

## Prerequisites

**Required**:
- Python 3.6+: For running documentation scripts
- Write access: To create documentation directories

**Optional**:
- Database connection details for live schema extraction
- Mermaid Live Editor or PlantUML viewer for diagram rendering

## Instructions

### Step 1: Initialize Documentation Project

Run the initialization script to create project structure:

```bash
python {baseDir}/scripts/init_db_docs.py \
  --project [database_name] \
  --output [output_directory] \
  --db-type [postgresql|mysql|sqlite|sqlserver|oracle] \
  --host [hostname] \
  --port [port] \
  --database [database_name] \
  --user [username]
```

Example for PostgreSQL:
```bash
python {baseDir}/scripts/init_db_docs.py \
  --project myapp_db \
  --db-type postgresql \
  --host localhost \
  --port 5432 \
  --database myapp \
  --user dbuser
```

This creates:
- Project directory with organized structure
- Configuration file (`db_docs_config.json`)
- README with project overview

### Step 2: Validate Configuration

Ensure configuration is correct before proceeding:

```bash
python {baseDir}/scripts/validate_config.py \
  --config ./[project_name]/db_docs_config.json
```

The validator checks:
- JSON syntax validity
- Required configuration sections
- Database connection parameters
- Output format specifications
- Project directory structure

Review any warnings or errors and update the configuration file as needed.

### Step 3: Generate ERD Diagrams

Create Entity Relationship Diagrams in multiple formats:

```bash
python {baseDir}/scripts/erd_generator.py \
  --config ./[project_name]/db_docs_config.json \
  --format [mermaid|plantuml|dbml|all] \
  --schema [optional_schema.json]
```

Generate all formats:
```bash
python {baseDir}/scripts/erd_generator.py \
  --config ./myapp_db/db_docs_config.json \
  --format all
```

This produces:
- **Mermaid** (`.md`): For GitHub/GitLab rendering
- **PlantUML** (`.puml`): For detailed UML diagrams
- **DBML** (`.dbml`): For dbdiagram.io visualization

### Step 4: View Generated Documentation

The diagrams are saved in the `diagrams/` directory:

1. **Mermaid diagrams**: Copy content to any Markdown file or use [Mermaid Live Editor](https://mermaid.live)
2. **PlantUML diagrams**: Use PlantUML server or IDE plugins
3. **DBML diagrams**: Upload to [dbdiagram.io](https://dbdiagram.io) or [dbdocs.io](https://dbdocs.io)

## Output

- **Project Structure**: Organized directories for schemas, tables, views, procedures
- **Configuration File**: JSON configuration for documentation settings
- **ERD Diagrams**: Visual database schema in 3 formats
- **Project README**: Overview and structure documentation

## Error Handling

1. **Error**: `Configuration file not found`
   **Solution**: Ensure you run init_db_docs.py first or provide correct config path

2. **Error**: `Invalid JSON in configuration file`
   **Solution**: Check JSON syntax, use validate_config.py to identify issues

3. **Error**: `Missing project directories`
   **Solution**: Run init_db_docs.py to create proper structure

4. **Error**: `Invalid database type`
   **Solution**: Use one of: postgresql, mysql, sqlite, sqlserver, oracle

5. **Error**: `Port must be a number`
   **Solution**: Provide numeric port value (e.g., 5432 for PostgreSQL)

## Examples

### Example 1: Quick PostgreSQL Documentation

```bash
# Initialize
python {baseDir}/scripts/init_db_docs.py --project ecommerce --db-type postgresql

# Validate
python {baseDir}/scripts/validate_config.py --config ./ecommerce/db_docs_config.json

# Generate all diagram formats
python {baseDir}/scripts/erd_generator.py --config ./ecommerce/db_docs_config.json --format all
```

### Example 2: MySQL with Custom Settings

```bash
# Initialize with specific connection details
python {baseDir}/scripts/init_db_docs.py \
  --project blog_db \
  --db-type mysql \
  --host db.example.com \
  --port 3306 \
  --database blog \
  --user admin

# Generate only Mermaid diagram
python {baseDir}/scripts/erd_generator.py \
  --config ./blog_db/db_docs_config.json \
  --format mermaid
```

### Example 3: SQLite Local Database

```bash
# Initialize for SQLite (no host/port needed)
python {baseDir}/scripts/init_db_docs.py \
  --project local_app \
  --db-type sqlite \
  --database ./data/app.db

# Generate DBML for web visualization
python {baseDir}/scripts/erd_generator.py \
  --config ./local_app/db_docs_config.json \
  --format dbml
```

## Tips

- The scripts work with sample data if no live database is available
- All scripts use Python standard library only - no pip installs needed
- Generated diagrams include table relationships based on foreign keys
- Configuration can be edited manually after initialization
- Use `--quiet` flag with validate_config.py for CI/CD pipelines

## Resources

- Scripts Documentation: `{baseDir}/scripts/README.md`
- Sample configurations: `{baseDir}/assets/`
- Script source code: `{baseDir}/scripts/`