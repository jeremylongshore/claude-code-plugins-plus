---
description: Generate comprehensive database documentation from existing schemas
shortcut: dbdocs
---

# Database Documentation Generator

Automatically generate comprehensive database documentation including ERD diagrams, table relationships, column descriptions, indexes, triggers, stored procedures, and interactive HTML documentation from your existing database schemas across multiple database engines.

## When to Use This Command

Use `/db-docs` when you need to:
- Document existing database schemas for team onboarding
- Generate ERD diagrams for architectural reviews
- Create data dictionaries for compliance requirements
- Build interactive database documentation websites
- Document relationships and foreign key constraints
- Generate migration guides between schema versions
- Create developer reference documentation
- Export schema documentation for audits
- Build database catalogs for data governance
- Generate test data documentation

DON'T use this when:
- Database is still in early design phase (use `/design-schema` instead)
- You only need query optimization docs (use `/optimize-query`)
- Working with NoSQL databases without fixed schemas
- Database has no meaningful structure to document

## Design Decisions

This command implements **SchemaSpy with PlantUML** as the primary approach because:
- Supports 30+ database types out of the box
- Generates interactive HTML with JavaScript navigation
- Creates high-quality vector ERD diagrams
- Analyzes implicit relationships via naming conventions
- Produces detailed table and column documentation
- Open-source with active community support

**Alternative considered: dbdocs.io**
- Cloud-based with collaboration features
- DBML (Database Markup Language) based
- Requires internet connection
- Recommended for team collaboration needs

**Alternative considered: SQL Server Data Tools**
- Excellent for SQL Server specifically
- Visual Studio integration
- Platform-specific limitation
- Recommended for pure Microsoft stacks

## Prerequisites

Before running this command:
1. Database connection credentials with schema read access
2. JDBC driver for your database type
3. Java Runtime Environment (JRE) 8+
4. GraphViz installed for diagram generation
5. Sufficient disk space for generated documentation

## Implementation Process

### Step 1: Database Introspection
Connect to database and extract complete schema metadata including tables, views, procedures, and relationships.

### Step 2: Relationship Analysis
Identify explicit foreign keys and implicit relationships based on naming patterns and data types.

### Step 3: ERD Generation
Create entity-relationship diagrams at multiple levels: full schema, per-module, and neighborhood views.

### Step 4: Documentation Generation
Generate HTML documentation with search, filtering, and interactive navigation features.

### Step 5: Export and Publishing
Package documentation for distribution via static hosting, PDF export, or integration with existing docs.

## Output Format

The command generates:
- `index.html` - Main documentation entry point
- `diagrams/` - ERD diagrams in multiple formats
  - `schema.svg` - Complete database diagram
  - `relationships.png` - Relationship overview
  - `tables/*.svg` - Individual table diagrams
- `tables/` - Individual table documentation
- `columns.html` - Searchable column index
- `constraints.html` - All constraints documentation
- `routines.html` - Stored procedures/functions
- `orphans.html` - Tables without relationships
- `anomalies.html` - Schema issues and warnings
- `metrics.json` - Database metrics and statistics
- `README.md` - Quick reference guide

## Code Examples

### Example 1: Comprehensive Database Documentation Generator

```javascript
// database-doc-generator.js
const { exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const mysql = require('mysql2/promise');
const { Client: PgClient } = require('pg');
const oracledb = require('oracledb');
const sql = require('mssql');
const ejs = require('ejs');
const marked = require('marked');
const plantuml = require('node-plantuml');

class DatabaseDocumentationGenerator {
  constructor(config) {
    this.config = {
      type: config.type || 'mysql', // mysql, postgresql, mssql, oracle
      host: config.host || 'localhost',
      port: config.port,
      database: config.database,
      username: config.username,
      password: config.password,
      outputDir: config.outputDir || './db-docs',
      includeViews: config.includeViews !== false,
      includeProcedures: config.includeProcedures !== false,
      includeIndexes: config.includeIndexes !== false,
      includeTriggers: config.includeTriggers !== false,
      generateERD: config.generateERD !== false,
      theme: config.theme || 'default',
      ...config
    };

    this.tables = [];
    this.views = [];
    this.procedures = [];
    this.relationships = [];
    this.indexes = [];
    this.triggers = [];
    this.connection = null;
  }

  async connect() {
    switch (this.config.type) {
      case 'mysql':
        this.connection = await mysql.createConnection({
          host: this.config.host,
          port: this.config.port || 3306,
          user: this.config.username,
          password: this.config.password,
          database: this.config.database
        });
        break;

      case 'postgresql':
        this.connection = new PgClient({
          host: this.config.host,
          port: this.config.port || 5432,
          user: this.config.username,
          password: this.config.password,
          database: this.config.database
        });
        await this.connection.connect();
        break;

      case 'mssql':
        this.connection = await sql.connect({
          server: this.config.host,
          port: this.config.port || 1433,
          user: this.config.username,
          password: this.config.password,
          database: this.config.database,
          options: {
            encrypt: true,
            trustServerCertificate: true
          }
        });
        break;

      case 'oracle':
        this.connection = await oracledb.getConnection({
          user: this.config.username,
          password: this.config.password,
          connectString: `${this.config.host}:${this.config.port || 1521}/${this.config.database}`
        });
        break;

      default:
        throw new Error(`Unsupported database type: ${this.config.type}`);
    }
  }

  async disconnect() {
    if (this.connection) {
      switch (this.config.type) {
        case 'mysql':
          await this.connection.end();
          break;
        case 'postgresql':
          await this.connection.end();
          break;
        case 'mssql':
          await this.connection.close();
          break;
        case 'oracle':
          await this.connection.close();
          break;
      }
    }
  }

  async extractSchema() {
    console.log('Extracting database schema...');

    // Extract tables
    this.tables = await this.getTables();

    // Extract columns for each table
    for (const table of this.tables) {
      table.columns = await this.getColumns(table.name);
      table.primaryKey = await this.getPrimaryKey(table.name);
      table.foreignKeys = await this.getForeignKeys(table.name);
      table.indexes = await this.getIndexes(table.name);
      table.triggers = await this.getTriggers(table.name);
      table.rowCount = await this.getRowCount(table.name);
      table.sizeInBytes = await this.getTableSize(table.name);

      // Add foreign keys to relationships
      this.relationships.push(...table.foreignKeys);
    }

    // Extract views
    if (this.config.includeViews) {
      this.views = await this.getViews();
      for (const view of this.views) {
        view.columns = await this.getColumns(view.name, true);
        view.definition = await this.getViewDefinition(view.name);
      }
    }

    // Extract stored procedures
    if (this.config.includeProcedures) {
      this.procedures = await this.getProcedures();
      for (const proc of this.procedures) {
        proc.parameters = await this.getProcedureParameters(proc.name);
        proc.definition = await this.getProcedureDefinition(proc.name);
      }
    }

    // Analyze implicit relationships
    this.analyzeImplicitRelationships();

    // Calculate metrics
    this.metrics = this.calculateMetrics();
  }

  async getTables() {
    let query;
    switch (this.config.type) {
      case 'mysql':
        query = `
          SELECT
            TABLE_NAME as name,
            TABLE_COMMENT as comment,
            ENGINE as engine,
            TABLE_ROWS as estimated_rows,
            CREATE_TIME as created_at,
            UPDATE_TIME as updated_at
          FROM information_schema.TABLES
          WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE'
          ORDER BY TABLE_NAME
        `;
        break;

      case 'postgresql':
        query = `
          SELECT
            tablename as name,
            obj_description(c.oid) as comment,
            pg_size_pretty(pg_total_relation_size(c.oid)) as size,
            n_live_tup as estimated_rows
          FROM pg_tables t
          JOIN pg_class c ON c.relname = t.tablename
          JOIN pg_stat_user_tables s ON s.relname = t.tablename
          WHERE schemaname = 'public'
          ORDER BY tablename
        `;
        break;

      case 'mssql':
        query = `
          SELECT
            t.name,
            ep.value as comment,
            p.rows as estimated_rows,
            t.create_date as created_at,
            t.modify_date as updated_at
          FROM sys.tables t
          LEFT JOIN sys.extended_properties ep
            ON ep.major_id = t.object_id AND ep.minor_id = 0
          LEFT JOIN sys.partitions p
            ON p.object_id = t.object_id AND p.index_id IN (0,1)
          WHERE t.is_ms_shipped = 0
          ORDER BY t.name
        `;
        break;
    }

    const [rows] = await this.connection.execute(query,
      this.config.type === 'mysql' ? [this.config.database] : []
    );

    return rows;
  }

  async getColumns(tableName, isView = false) {
    let query;
    switch (this.config.type) {
      case 'mysql':
        query = `
          SELECT
            COLUMN_NAME as name,
            DATA_TYPE as type,
            CHARACTER_MAXIMUM_LENGTH as max_length,
            IS_NULLABLE as nullable,
            COLUMN_DEFAULT as default_value,
            COLUMN_COMMENT as comment,
            EXTRA as extra,
            COLUMN_KEY as key_type
          FROM information_schema.COLUMNS
          WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
          ORDER BY ORDINAL_POSITION
        `;
        break;

      case 'postgresql':
        query = `
          SELECT
            column_name as name,
            data_type as type,
            character_maximum_length as max_length,
            is_nullable as nullable,
            column_default as default_value,
            col_description(pgc.oid, a.attnum) as comment
          FROM information_schema.columns c
          JOIN pg_class pgc ON pgc.relname = c.table_name
          JOIN pg_attribute a ON a.attrelid = pgc.oid AND a.attname = c.column_name
          WHERE table_schema = 'public' AND table_name = $1
          ORDER BY ordinal_position
        `;
        break;
    }

    const params = this.config.type === 'mysql'
      ? [this.config.database, tableName]
      : [tableName];

    const [rows] = await this.connection.execute(query, params);

    return rows.map(row => ({
      name: row.name,
      type: this.formatDataType(row),
      nullable: row.nullable === 'YES',
      default: row.default_value,
      comment: row.comment || '',
      isPrimaryKey: row.key_type === 'PRI',
      isForeignKey: row.key_type === 'MUL',
      isUnique: row.key_type === 'UNI',
      extra: row.extra || ''
    }));
  }

  formatDataType(column) {
    let type = column.type.toUpperCase();
    if (column.max_length) {
      type += `(${column.max_length})`;
    }
    return type;
  }

  async getForeignKeys(tableName) {
    let query;
    switch (this.config.type) {
      case 'mysql':
        query = `
          SELECT
            kcu.CONSTRAINT_NAME as name,
            kcu.COLUMN_NAME as column_name,
            kcu.REFERENCED_TABLE_NAME as referenced_table,
            kcu.REFERENCED_COLUMN_NAME as referenced_column,
            rc.UPDATE_RULE as update_rule,
            rc.DELETE_RULE as delete_rule
          FROM information_schema.KEY_COLUMN_USAGE kcu
          JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
            ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
          WHERE kcu.TABLE_SCHEMA = ?
            AND kcu.TABLE_NAME = ?
            AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
        `;
        break;

      case 'postgresql':
        query = `
          SELECT
            tc.constraint_name as name,
            kcu.column_name,
            ccu.table_name AS referenced_table,
            ccu.column_name AS referenced_column,
            rc.update_rule,
            rc.delete_rule
          FROM information_schema.table_constraints AS tc
          JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
          JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
          JOIN information_schema.referential_constraints rc
            ON rc.constraint_name = tc.constraint_name
          WHERE tc.table_name = $1 AND tc.constraint_type = 'FOREIGN KEY'
        `;
        break;
    }

    const params = this.config.type === 'mysql'
      ? [this.config.database, tableName]
      : [tableName];

    const [rows] = await this.connection.execute(query, params);

    return rows.map(row => ({
      name: row.name,
      sourceTable: tableName,
      sourceColumn: row.column_name,
      targetTable: row.referenced_table,
      targetColumn: row.referenced_column,
      onUpdate: row.update_rule,
      onDelete: row.delete_rule
    }));
  }

  analyzeImplicitRelationships() {
    // Find implicit relationships based on naming conventions
    console.log('Analyzing implicit relationships...');

    const implicitRelationships = [];

    for (const table of this.tables) {
      for (const column of table.columns) {
        // Check for common foreign key naming patterns
        const patterns = [
          /^(.+)_id$/i,
          /^id_(.+)$/i,
          /^fk_(.+)$/i,
          /^ref_(.+)$/i
        ];

        for (const pattern of patterns) {
          const match = column.name.match(pattern);
          if (match) {
            const potentialTable = match[1];

            // Check if referenced table exists
            const referencedTable = this.tables.find(t =>
              t.name.toLowerCase() === potentialTable.toLowerCase() ||
              t.name.toLowerCase() === potentialTable.toLowerCase() + 's' ||
              t.name.toLowerCase() === potentialTable.toLowerCase().replace(/_/g, '')
            );

            if (referencedTable && !this.isExistingRelationship(table.name, column.name)) {
              implicitRelationships.push({
                name: `implicit_${table.name}_${column.name}`,
                sourceTable: table.name,
                sourceColumn: column.name,
                targetTable: referencedTable.name,
                targetColumn: 'id',
                type: 'implicit',
                confidence: 0.8
              });
            }
          }
        }
      }
    }

    this.relationships.push(...implicitRelationships);
  }

  isExistingRelationship(tableName, columnName) {
    return this.relationships.some(r =>
      r.sourceTable === tableName && r.sourceColumn === columnName
    );
  }

  async generateERD() {
    console.log('Generating Entity Relationship Diagram...');

    const plantUmlCode = this.generatePlantUMLCode();

    // Save PlantUML source
    await fs.writeFile(
      path.join(this.config.outputDir, 'diagrams', 'schema.puml'),
      plantUmlCode
    );

    // Generate SVG diagram
    return new Promise((resolve, reject) => {
      const gen = plantuml.generate(plantUmlCode, { format: 'svg' });
      const chunks = [];

      gen.out.on('data', chunk => chunks.push(chunk));
      gen.out.on('end', async () => {
        const svg = Buffer.concat(chunks).toString();
        await fs.writeFile(
          path.join(this.config.outputDir, 'diagrams', 'schema.svg'),
          svg
        );
        resolve();
      });
      gen.out.on('error', reject);
    });
  }

  generatePlantUMLCode() {
    let puml = '@startuml Database Schema\n';
    puml += '!define Table(name,desc) class name as "desc" << (T,#FFAAAA) >>\n';
    puml += '!define View(name,desc) class name as "desc" << (V,#AAFFAA) >>\n';
    puml += '!define primary_key(x) <b>PK: x</b>\n';
    puml += '!define foreign_key(x) <i>FK: x</i>\n';
    puml += '!define unique(x) <u>x</u>\n';
    puml += '\n';

    // Add tables
    for (const table of this.tables) {
      puml += `Table(${table.name}, "${table.name}") {\n`;

      // Add columns
      for (const column of table.columns) {
        let columnDef = `  ${column.name}: ${column.type}`;

        if (column.isPrimaryKey) {
          columnDef = `  primary_key(${column.name}): ${column.type}`;
        } else if (column.isForeignKey) {
          columnDef = `  foreign_key(${column.name}): ${column.type}`;
        } else if (column.isUnique) {
          columnDef = `  unique(${column.name}): ${column.type}`;
        }

        if (!column.nullable) {
          columnDef += ' NOT NULL';
        }

        puml += columnDef + '\n';
      }

      puml += '}\n\n';
    }

    // Add views
    for (const view of this.views) {
      puml += `View(${view.name}, "${view.name}") {\n`;
      for (const column of view.columns) {
        puml += `  ${column.name}: ${column.type}\n`;
      }
      puml += '}\n\n';
    }

    // Add relationships
    for (const rel of this.relationships) {
      const relType = rel.type === 'implicit' ? '..' : '--';
      const label = rel.type === 'implicit' ? 'implicit' : '';
      puml += `${rel.sourceTable} "${rel.sourceColumn}" ${relType}> "${rel.targetColumn}" ${rel.targetTable} : ${label}\n`;
    }

    puml += '@enduml\n';
    return puml;
  }

  async generateHTML() {
    console.log('Generating HTML documentation...');

    const template = await fs.readFile(
      path.join(__dirname, 'templates', 'index.ejs'),
      'utf-8'
    );

    const html = ejs.render(template, {
      database: this.config.database,
      tables: this.tables,
      views: this.views,
      procedures: this.procedures,
      relationships: this.relationships,
      metrics: this.metrics,
      generatedAt: new Date().toISOString()
    });

    await fs.writeFile(
      path.join(this.config.outputDir, 'index.html'),
      html
    );

    // Generate individual table pages
    for (const table of this.tables) {
      await this.generateTablePage(table);
    }
  }

  async generateTablePage(table) {
    const template = `
<!DOCTYPE html>
<html>
<head>
  <title>${table.name} - Database Documentation</title>
  <link rel="stylesheet" href="../assets/style.css">
</head>
<body>
  <div class="container">
    <h1>${table.name}</h1>
    <p class="description">${table.comment || 'No description available'}</p>

    <div class="metadata">
      <span>Rows: ${table.rowCount || 'Unknown'}</span>
      <span>Size: ${table.sizeInBytes ? this.formatBytes(table.sizeInBytes) : 'Unknown'}</span>
      <span>Engine: ${table.engine || 'N/A'}</span>
    </div>

    <h2>Columns</h2>
    <table class="data-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Type</th>
          <th>Nullable</th>
          <th>Default</th>
          <th>Key</th>
          <th>Comment</th>
        </tr>
      </thead>
      <tbody>
        ${table.columns.map(col => `
        <tr>
          <td class="column-name">${col.name}</td>
          <td class="data-type">${col.type}</td>
          <td>${col.nullable ? 'YES' : 'NO'}</td>
          <td>${col.default || 'NULL'}</td>
          <td>
            ${col.isPrimaryKey ? '<span class="key pk">PK</span>' : ''}
            ${col.isForeignKey ? '<span class="key fk">FK</span>' : ''}
            ${col.isUnique ? '<span class="key uk">UQ</span>' : ''}
          </td>
          <td>${col.comment}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>

    ${table.foreignKeys.length > 0 ? `
    <h2>Foreign Keys</h2>
    <table class="data-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Column</th>
          <th>References</th>
          <th>On Update</th>
          <th>On Delete</th>
        </tr>
      </thead>
      <tbody>
        ${table.foreignKeys.map(fk => `
        <tr>
          <td>${fk.name}</td>
          <td>${fk.sourceColumn}</td>
          <td><a href="${fk.targetTable}.html">${fk.targetTable}</a>.${fk.targetColumn}</td>
          <td>${fk.onUpdate}</td>
          <td>${fk.onDelete}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>
    ` : ''}

    ${table.indexes.length > 0 ? `
    <h2>Indexes</h2>
    <table class="data-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Columns</th>
          <th>Type</th>
          <th>Unique</th>
        </tr>
      </thead>
      <tbody>
        ${table.indexes.map(idx => `
        <tr>
          <td>${idx.name}</td>
          <td>${idx.columns.join(', ')}</td>
          <td>${idx.type}</td>
          <td>${idx.unique ? 'YES' : 'NO'}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>
    ` : ''}

    <h2>Sample Queries</h2>
    <pre><code class="sql">-- Select all records
SELECT * FROM ${table.name};

-- Select with joins
${this.generateSampleJoinQuery(table)}

-- Insert record
INSERT INTO ${table.name} (${table.columns.filter(c => !c.extra.includes('auto_increment')).map(c => c.name).join(', ')})
VALUES (${table.columns.filter(c => !c.extra.includes('auto_increment')).map(c => this.getSampleValue(c)).join(', ')});

-- Update record
UPDATE ${table.name}
SET ${table.columns.filter(c => !c.isPrimaryKey).slice(0, 2).map(c => `${c.name} = ${this.getSampleValue(c)}`).join(',\n    ')}
WHERE ${table.primaryKey ? `${table.primaryKey} = 1` : 'condition'};
</code></pre>
  </div>
  <script src="../assets/highlight.js"></script>
</body>
</html>
    `;

    await fs.writeFile(
      path.join(this.config.outputDir, 'tables', `${table.name}.html`),
      template
    );
  }

  generateSampleJoinQuery(table) {
    if (table.foreignKeys.length === 0) {
      return `SELECT * FROM ${table.name} LIMIT 10;`;
    }

    const joins = table.foreignKeys.map(fk =>
      `LEFT JOIN ${fk.targetTable} ON ${table.name}.${fk.sourceColumn} = ${fk.targetTable}.${fk.targetColumn}`
    ).join('\n');

    return `SELECT
  ${table.name}.*,
  ${table.foreignKeys.map(fk => `${fk.targetTable}.*`).join(',\n  ')}
FROM ${table.name}
${joins}
LIMIT 10;`;
  }

  getSampleValue(column) {
    if (column.default) return column.default;

    const type = column.type.toLowerCase();
    if (type.includes('int')) return '1';
    if (type.includes('decimal') || type.includes('float')) return '0.00';
    if (type.includes('date')) return "'2024-01-01'";
    if (type.includes('time')) return "'2024-01-01 00:00:00'";
    if (type.includes('bool')) return 'TRUE';
    if (type.includes('json')) return "'{}'";
    return "'value'";
  }

  calculateMetrics() {
    return {
      totalTables: this.tables.length,
      totalViews: this.views.length,
      totalColumns: this.tables.reduce((sum, t) => sum + t.columns.length, 0),
      totalRelationships: this.relationships.length,
      totalIndexes: this.tables.reduce((sum, t) => sum + (t.indexes?.length || 0), 0),
      totalProcedures: this.procedures.length,
      totalRows: this.tables.reduce((sum, t) => sum + (t.rowCount || 0), 0),
      orphanTables: this.tables.filter(t =>
        !this.relationships.some(r => r.sourceTable === t.name || r.targetTable === t.name)
      ).length,
      tablesWithoutPK: this.tables.filter(t => !t.primaryKey).length,
      avgColumnsPerTable: Math.round(
        this.tables.reduce((sum, t) => sum + t.columns.length, 0) / this.tables.length
      ),
      avgRelationshipsPerTable: Math.round(
        this.relationships.length / this.tables.length * 10
      ) / 10
    };
  }

  formatBytes(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }

  async generateMarkdown() {
    console.log('Generating Markdown documentation...');

    let markdown = `# Database Documentation: ${this.config.database}\n\n`;
    markdown += `Generated: ${new Date().toISOString()}\n\n`;

    // Add metrics
    markdown += '## Database Metrics\n\n';
    markdown += `- **Total Tables**: ${this.metrics.totalTables}\n`;
    markdown += `- **Total Views**: ${this.metrics.totalViews}\n`;
    markdown += `- **Total Columns**: ${this.metrics.totalColumns}\n`;
    markdown += `- **Total Relationships**: ${this.metrics.totalRelationships}\n`;
    markdown += `- **Total Indexes**: ${this.metrics.totalIndexes}\n`;
    markdown += `- **Orphan Tables**: ${this.metrics.orphanTables}\n`;
    markdown += `- **Tables without Primary Key**: ${this.metrics.tablesWithoutPK}\n\n`;

    // Add table documentation
    markdown += '## Tables\n\n';
    for (const table of this.tables) {
      markdown += `### ${table.name}\n\n`;

      if (table.comment) {
        markdown += `${table.comment}\n\n`;
      }

      markdown += '#### Columns\n\n';
      markdown += '| Name | Type | Nullable | Default | Key | Comment |\n';
      markdown += '|------|------|----------|---------|-----|----------|\n';

      for (const column of table.columns) {
        const keys = [];
        if (column.isPrimaryKey) keys.push('PK');
        if (column.isForeignKey) keys.push('FK');
        if (column.isUnique) keys.push('UQ');

        markdown += `| ${column.name} | ${column.type} | ${column.nullable ? 'YES' : 'NO'} | ${column.default || 'NULL'} | ${keys.join(', ')} | ${column.comment} |\n`;
      }

      markdown += '\n';

      if (table.foreignKeys.length > 0) {
        markdown += '#### Foreign Keys\n\n';
        markdown += '| Constraint | Column | References | On Update | On Delete |\n';
        markdown += '|------------|--------|------------|-----------|----------|\n';

        for (const fk of table.foreignKeys) {
          markdown += `| ${fk.name} | ${fk.sourceColumn} | ${fk.targetTable}.${fk.targetColumn} | ${fk.onUpdate} | ${fk.onDelete} |\n`;
        }

        markdown += '\n';
      }
    }

    await fs.writeFile(
      path.join(this.config.outputDir, 'README.md'),
      markdown
    );
  }

  async generateDataDictionary() {
    console.log('Generating data dictionary...');

    const dictionary = {
      database: this.config.database,
      generated: new Date().toISOString(),
      metrics: this.metrics,
      tables: this.tables.map(table => ({
        name: table.name,
        comment: table.comment,
        columns: table.columns.map(col => ({
          name: col.name,
          type: col.type,
          nullable: col.nullable,
          default: col.default,
          comment: col.comment,
          constraints: {
            primaryKey: col.isPrimaryKey,
            foreignKey: col.isForeignKey,
            unique: col.isUnique
          }
        })),
        relationships: {
          parents: this.relationships.filter(r => r.sourceTable === table.name),
          children: this.relationships.filter(r => r.targetTable === table.name)
        }
      }))
    };

    await fs.writeFile(
      path.join(this.config.outputDir, 'data-dictionary.json'),
      JSON.stringify(dictionary, null, 2)
    );
  }

  async generate() {
    try {
      // Create output directories
      await fs.mkdir(this.config.outputDir, { recursive: true });
      await fs.mkdir(path.join(this.config.outputDir, 'diagrams'), { recursive: true });
      await fs.mkdir(path.join(this.config.outputDir, 'tables'), { recursive: true });
      await fs.mkdir(path.join(this.config.outputDir, 'assets'), { recursive: true });

      // Connect to database
      await this.connect();

      // Extract schema information
      await this.extractSchema();

      // Generate outputs
      if (this.config.generateERD) {
        await this.generateERD();
      }

      await this.generateHTML();
      await this.generateMarkdown();
      await this.generateDataDictionary();
      await this.generateAssets();

      console.log(`Documentation generated successfully in ${this.config.outputDir}`);

    } catch (error) {
      console.error('Error generating documentation:', error);
      throw error;
    } finally {
      await this.disconnect();
    }
  }

  async generateAssets() {
    // Generate CSS
    const css = `
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  line-height: 1.6;
  color: #333;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

h1, h2, h3 {
  color: #2c3e50;
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 10px;
}

.container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.metadata {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  margin: 20px 0;
}

.metadata span {
  margin-right: 20px;
  font-size: 14px;
  color: #666;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
}

.data-table th {
  background: #3498db;
  color: white;
  text-align: left;
  padding: 10px;
}

.data-table td {
  padding: 8px;
  border-bottom: 1px solid #ddd;
}

.data-table tr:hover {
  background: #f5f5f5;
}

.column-name {
  font-weight: bold;
  color: #2c3e50;
}

.data-type {
  color: #e74c3c;
  font-family: 'Courier New', monospace;
}

.key {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: bold;
  margin-right: 4px;
}

.key.pk {
  background: #f39c12;
  color: white;
}

.key.fk {
  background: #3498db;
  color: white;
}

.key.uk {
  background: #9b59b6;
  color: white;
}

pre {
  background: #f4f4f4;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 15px;
  overflow-x: auto;
}

code.sql {
  color: #2c3e50;
  font-family: 'Courier New', monospace;
}

a {
  color: #3498db;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
    `;

    await fs.writeFile(
      path.join(this.config.outputDir, 'assets', 'style.css'),
      css
    );
  }
}

// Usage
const generator = new DatabaseDocumentationGenerator({
  type: 'mysql',
  host: 'localhost',
  database: 'ecommerce',
  username: 'root',
  password: 'password',
  outputDir: './database-docs',
  generateERD: true,
  includeViews: true,
  includeProcedures: true
});

generator.generate()
  .then(() => console.log('Documentation generation complete'))
  .catch(error => console.error('Documentation generation failed:', error));

module.exports = DatabaseDocumentationGenerator;
```

### Example 2: Python Database Documentation Generator with SchemaSpy Integration

```python
# database_doc_generator.py
import os
import json
import subprocess
import sqlite3
import psycopg2
import mysql.connector
import pymongo
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from jinja2 import Template
import graphviz
import yaml
from dataclasses import dataclass, asdict
import pandas as pd

@dataclass
class Column:
    name: str
    data_type: str
    nullable: bool
    default: Optional[str]
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_unique: bool = False
    comment: Optional[str] = None

@dataclass
class ForeignKey:
    name: str
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    on_update: str
    on_delete: str

@dataclass
class Table:
    name: str
    columns: List[Column]
    primary_keys: List[str]
    foreign_keys: List[ForeignKey]
    indexes: List[Dict[str, Any]]
    comment: Optional[str] = None
    row_count: Optional[int] = None
    size_bytes: Optional[int] = None

class DatabaseDocGenerator:
    """Generate comprehensive database documentation"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.tables: List[Table] = []
        self.views: List[Dict[str, Any]] = []
        self.procedures: List[Dict[str, Any]] = []
        self.relationships: List[ForeignKey] = []
        self.metrics: Dict[str, Any] = {}

    def connect(self):
        """Connect to database based on type"""
        db_type = self.config['type']

        if db_type == 'postgresql':
            self.connection = psycopg2.connect(
                host=self.config['host'],
                port=self.config.get('port', 5432),
                database=self.config['database'],
                user=self.config['username'],
                password=self.config['password']
            )
        elif db_type == 'mysql':
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                port=self.config.get('port', 3306),
                database=self.config['database'],
                user=self.config['username'],
                password=self.config['password']
            )
        elif db_type == 'sqlite':
            self.connection = sqlite3.connect(self.config['database'])
        elif db_type == 'mongodb':
            from pymongo import MongoClient
            self.connection = MongoClient(
                host=self.config['host'],
                port=self.config.get('port', 27017)
            )[self.config['database']]
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def extract_schema(self):
        """Extract complete database schema"""
        print("Extracting database schema...")

        if self.config['type'] == 'mongodb':
            self._extract_mongodb_schema()
        else:
            self._extract_sql_schema()

        self._analyze_implicit_relationships()
        self._calculate_metrics()

    def _extract_sql_schema(self):
        """Extract schema for SQL databases"""
        cursor = self.connection.cursor()

        # Get tables
        if self.config['type'] == 'postgresql':
            cursor.execute("""
                SELECT tablename, obj_description(c.oid)
                FROM pg_tables t
                JOIN pg_class c ON c.relname = t.tablename
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
        elif self.config['type'] == 'mysql':
            cursor.execute("""
                SELECT TABLE_NAME, TABLE_COMMENT
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """, (self.config['database'],))
        elif self.config['type'] == 'sqlite':
            cursor.execute("""
                SELECT name, sql
                FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)

        tables_data = cursor.fetchall()

        for table_name, comment in tables_data:
            columns = self._get_columns(cursor, table_name)
            foreign_keys = self._get_foreign_keys(cursor, table_name)
            indexes = self._get_indexes(cursor, table_name)
            primary_keys = [col.name for col in columns if col.is_primary_key]

            table = Table(
                name=table_name,
                columns=columns,
                primary_keys=primary_keys,
                foreign_keys=foreign_keys,
                indexes=indexes,
                comment=comment
            )

            # Get table statistics
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                table.row_count = cursor.fetchone()[0]
            except:
                pass

            self.tables.append(table)
            self.relationships.extend(foreign_keys)

    def _get_columns(self, cursor, table_name: str) -> List[Column]:
        """Get columns for a table"""
        columns = []

        if self.config['type'] == 'postgresql':
            cursor.execute("""
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    col_description(pgc.oid, a.attnum) as comment
                FROM information_schema.columns c
                JOIN pg_class pgc ON pgc.relname = c.table_name
                JOIN pg_attribute a ON a.attrelid = pgc.oid
                    AND a.attname = c.column_name
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
        elif self.config['type'] == 'mysql':
            cursor.execute("""
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    COLUMN_COMMENT,
                    COLUMN_KEY
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (self.config['database'], table_name))
        elif self.config['type'] == 'sqlite':
            cursor.execute(f"PRAGMA table_info({table_name})")

        for row in cursor.fetchall():
            if self.config['type'] == 'sqlite':
                column = Column(
                    name=row[1],
                    data_type=row[2],
                    nullable=not row[3],
                    default=row[4],
                    is_primary_key=bool(row[5])
                )
            else:
                column = Column(
                    name=row[0],
                    data_type=row[1],
                    nullable=row[2] == 'YES',
                    default=row[3],
                    comment=row[4] if len(row) > 4 else None
                )

                if self.config['type'] == 'mysql' and len(row) > 5:
                    column.is_primary_key = row[5] == 'PRI'
                    column.is_foreign_key = row[5] == 'MUL'
                    column.is_unique = row[5] == 'UNI'

            columns.append(column)

        return columns

    def _get_foreign_keys(self, cursor, table_name: str) -> List[ForeignKey]:
        """Get foreign keys for a table"""
        foreign_keys = []

        if self.config['type'] == 'postgresql':
            cursor.execute("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS referenced_table,
                    ccu.column_name AS referenced_column,
                    rc.update_rule,
                    rc.delete_rule
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                JOIN information_schema.referential_constraints rc
                    ON rc.constraint_name = tc.constraint_name
                WHERE tc.table_name = %s
                    AND tc.constraint_type = 'FOREIGN KEY'
            """, (table_name,))
        elif self.config['type'] == 'mysql':
            cursor.execute("""
                SELECT
                    kcu.CONSTRAINT_NAME,
                    kcu.COLUMN_NAME,
                    kcu.REFERENCED_TABLE_NAME,
                    kcu.REFERENCED_COLUMN_NAME,
                    rc.UPDATE_RULE,
                    rc.DELETE_RULE
                FROM information_schema.KEY_COLUMN_USAGE kcu
                JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
                    ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
                WHERE kcu.TABLE_SCHEMA = %s
                    AND kcu.TABLE_NAME = %s
                    AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            """, (self.config['database'], table_name))
        elif self.config['type'] == 'sqlite':
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")

        for row in cursor.fetchall():
            if self.config['type'] == 'sqlite':
                fk = ForeignKey(
                    name=f"fk_{table_name}_{row[0]}",
                    source_table=table_name,
                    source_column=row[3],
                    target_table=row[2],
                    target_column=row[4],
                    on_update=row[5],
                    on_delete=row[6]
                )
            else:
                fk = ForeignKey(
                    name=row[0],
                    source_table=table_name,
                    source_column=row[1],
                    target_table=row[2],
                    target_column=row[3],
                    on_update=row[4],
                    on_delete=row[5]
                )

            foreign_keys.append(fk)

        return foreign_keys

    def _get_indexes(self, cursor, table_name: str) -> List[Dict[str, Any]]:
        """Get indexes for a table"""
        indexes = []

        if self.config['type'] == 'postgresql':
            cursor.execute("""
                SELECT
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE tablename = %s
            """, (table_name,))
        elif self.config['type'] == 'mysql':
            cursor.execute("""
                SELECT
                    INDEX_NAME,
                    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as columns,
                    INDEX_TYPE,
                    NON_UNIQUE
                FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                GROUP BY INDEX_NAME, INDEX_TYPE, NON_UNIQUE
            """, (self.config['database'], table_name))
        elif self.config['type'] == 'sqlite':
            cursor.execute(f"PRAGMA index_list({table_name})")

        for row in cursor.fetchall():
            if self.config['type'] == 'sqlite':
                index = {
                    'name': row[1],
                    'unique': bool(row[2])
                }
            else:
                index = {
                    'name': row[0],
                    'definition': row[1] if self.config['type'] == 'postgresql' else None,
                    'columns': row[1].split(',') if self.config['type'] == 'mysql' else [],
                    'type': row[2] if self.config['type'] == 'mysql' else None,
                    'unique': not row[3] if self.config['type'] == 'mysql' else False
                }

            indexes.append(index)

        return indexes

    def _analyze_implicit_relationships(self):
        """Find implicit relationships based on naming conventions"""
        print("Analyzing implicit relationships...")

        patterns = [
            r'(.+)_id$',
            r'id_(.+)$',
            r'fk_(.+)$',
            r'(.+)_fk$'
        ]

        for table in self.tables:
            for column in table.columns:
                if column.is_foreign_key:
                    continue

                for pattern in patterns:
                    import re
                    match = re.match(pattern, column.name, re.IGNORECASE)
                    if match:
                        potential_table = match.group(1)

                        # Check variations
                        variations = [
                            potential_table,
                            potential_table + 's',
                            potential_table[:-1] if potential_table.endswith('s') else potential_table,
                            potential_table.replace('_', '')
                        ]

                        for var in variations:
                            target_table = next(
                                (t for t in self.tables if t.name.lower() == var.lower()),
                                None
                            )

                            if target_table:
                                # Create implicit relationship
                                fk = ForeignKey(
                                    name=f"implicit_{table.name}_{column.name}",
                                    source_table=table.name,
                                    source_column=column.name,
                                    target_table=target_table.name,
                                    target_column='id',
                                    on_update='NO ACTION',
                                    on_delete='NO ACTION'
                                )
                                self.relationships.append(fk)
                                break

    def generate_erd(self):
        """Generate Entity Relationship Diagram"""
        print("Generating ERD...")

        dot = graphviz.Digraph(comment='Database Schema', format='svg')
        dot.attr(rankdir='TB', splines='ortho', nodesep='0.5')

        # Add tables as nodes
        for table in self.tables:
            label = f"<<TABLE border='1' cellspacing='0' cellpadding='4'>\n"
            label += f"<TR><TD colspan='2' bgcolor='lightblue'><B>{table.name}</B></TD></TR>\n"

            for column in table.columns[:10]:  # Limit to first 10 columns
                bgcolor = ''
                if column.is_primary_key:
                    bgcolor = " bgcolor='yellow'"
                elif column.is_foreign_key:
                    bgcolor = " bgcolor='lightgreen'"

                label += f"<TR><TD{bgcolor}>{column.name}</TD>"
                label += f"<TD>{column.data_type}</TD></TR>\n"

            if len(table.columns) > 10:
                label += f"<TR><TD colspan='2'>... {len(table.columns) - 10} more columns</TD></TR>\n"

            label += "</TABLE>>"

            dot.node(table.name, label=label, shape='plaintext')

        # Add relationships as edges
        for rel in self.relationships:
            style = 'solid' if not rel.name.startswith('implicit') else 'dashed'
            dot.edge(
                rel.source_table,
                rel.target_table,
                label=f"{rel.source_column}→{rel.target_column}",
                style=style
            )

        # Save diagram
        output_dir = Path(self.config['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)

        dot.render(output_dir / 'diagrams' / 'schema', cleanup=True)

    def generate_html(self):
        """Generate HTML documentation"""
        print("Generating HTML documentation...")

        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <title>{{ database }} - Database Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1, h2, h3 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:hover { background-color: #f5f5f5; }
        .metrics { display: flex; flex-wrap: wrap; gap: 20px; margin: 20px 0; }
        .metric { background: #f0f0f0; padding: 15px; border-radius: 5px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #4CAF50; }
        .metric-label { font-size: 14px; color: #666; }
        .toc { background: #f9f9f9; padding: 20px; border-radius: 5px; }
        .toc a { text-decoration: none; color: #333; }
        .toc a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>Database Documentation: {{ database }}</h1>
    <p>Generated: {{ generated_at }}</p>

    <div class="metrics">
        <div class="metric">
            <div class="metric-value">{{ metrics.total_tables }}</div>
            <div class="metric-label">Tables</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ metrics.total_columns }}</div>
            <div class="metric-label">Columns</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ metrics.total_relationships }}</div>
            <div class="metric-label">Relationships</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ metrics.total_indexes }}</div>
            <div class="metric-label">Indexes</div>
        </div>
    </div>

    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
        {% for table in tables %}
            <li><a href="#{{ table.name }}">{{ table.name }}</a></li>
        {% endfor %}
        </ul>
    </div>

    {% for table in tables %}
    <h2 id="{{ table.name }}">{{ table.name }}</h2>
    {% if table.comment %}
    <p>{{ table.comment }}</p>
    {% endif %}

    <h3>Columns</h3>
    <table>
        <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Nullable</th>
            <th>Default</th>
            <th>Key</th>
            <th>Comment</th>
        </tr>
        {% for column in table.columns %}
        <tr>
            <td>{{ column.name }}</td>
            <td>{{ column.data_type }}</td>
            <td>{{ 'YES' if column.nullable else 'NO' }}</td>
            <td>{{ column.default or 'NULL' }}</td>
            <td>
                {% if column.is_primary_key %}PK{% endif %}
                {% if column.is_foreign_key %}FK{% endif %}
                {% if column.is_unique %}UQ{% endif %}
            </td>
            <td>{{ column.comment or '' }}</td>
        </tr>
        {% endfor %}
    </table>

    {% if table.foreign_keys %}
    <h3>Foreign Keys</h3>
    <table>
        <tr>
            <th>Name</th>
            <th>Column</th>
            <th>References</th>
            <th>On Update</th>
            <th>On Delete</th>
        </tr>
        {% for fk in table.foreign_keys %}
        <tr>
            <td>{{ fk.name }}</td>
            <td>{{ fk.source_column }}</td>
            <td>{{ fk.target_table }}.{{ fk.target_column }}</td>
            <td>{{ fk.on_update }}</td>
            <td>{{ fk.on_delete }}</td>
        </tr>
        {% endfor %}
    </table>
    {% endif %}

    {% if table.indexes %}
    <h3>Indexes</h3>
    <table>
        <tr>
            <th>Name</th>
            <th>Unique</th>
            <th>Definition</th>
        </tr>
        {% for idx in table.indexes %}
        <tr>
            <td>{{ idx.name }}</td>
            <td>{{ 'YES' if idx.unique else 'NO' }}</td>
            <td>{{ idx.definition or idx.columns|join(', ') if idx.columns else '' }}</td>
        </tr>
        {% endfor %}
    </table>
    {% endif %}
    {% endfor %}
</body>
</html>
        """)

        html = template.render(
            database=self.config['database'],
            generated_at=datetime.now().isoformat(),
            metrics=self.metrics,
            tables=self.tables
        )

        output_path = Path(self.config['output_dir']) / 'index.html'
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(html)

    def _calculate_metrics(self):
        """Calculate database metrics"""
        self.metrics = {
            'total_tables': len(self.tables),
            'total_columns': sum(len(t.columns) for t in self.tables),
            'total_relationships': len(self.relationships),
            'total_indexes': sum(len(t.indexes) for t in self.tables),
            'orphan_tables': len([
                t for t in self.tables
                if not any(
                    r.source_table == t.name or r.target_table == t.name
                    for r in self.relationships
                )
            ]),
            'tables_without_pk': len([
                t for t in self.tables if not t.primary_keys
            ])
        }

    def run_schemaspy(self):
        """Run SchemaSpy for additional documentation"""
        print("Running SchemaSpy...")

        output_dir = Path(self.config['output_dir']) / 'schemaspy'
        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            'java', '-jar', 'schemaspy.jar',
            '-t', self.config['type'],
            '-host', self.config['host'],
            '-db', self.config['database'],
            '-u', self.config['username'],
            '-p', self.config['password'],
            '-o', str(output_dir),
            '-dp', self.config.get('driver_path', '.'),
            '-vizjs'
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"SchemaSpy documentation generated in {output_dir}")
        except subprocess.CalledProcessError as e:
            print(f"SchemaSpy failed: {e}")
        except FileNotFoundError:
            print("SchemaSpy not found. Download from http://schemaspy.org")

    def generate(self):
        """Generate complete documentation"""
        try:
            self.connect()
            self.extract_schema()
            self.generate_erd()
            self.generate_html()

            if self.config.get('use_schemaspy', False):
                self.run_schemaspy()

            print(f"Documentation generated in {self.config['output_dir']}")

        finally:
            if self.connection:
                self.connection.close()


# Usage
if __name__ == "__main__":
    config = {
        'type': 'postgresql',
        'host': 'localhost',
        'port': 5432,
        'database': 'myapp',
        'username': 'user',
        'password': 'password',
        'output_dir': './db-docs',
        'use_schemaspy': True
    }

    generator = DatabaseDocGenerator(config)
    generator.generate()
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Access denied to schema" | Insufficient database permissions | Grant SELECT permission on information_schema |
| "GraphViz not found" | Missing diagram generator | Install GraphViz: `apt-get install graphviz` |
| "Out of memory" | Large database schema | Increase Java heap size for SchemaSpy |
| "Connection timeout" | Database unreachable | Check network and firewall settings |
| "Unknown column type" | Custom database types | Add type mapping in configuration |

## Configuration Options

**Basic Usage:**
```bash
/db-docs \
  --type=postgresql \
  --host=localhost \
  --database=myapp \
  --output=./docs
```

**Available Options:**

`--type <database>` - Database type
- `mysql` - MySQL/MariaDB
- `postgresql` - PostgreSQL
- `mssql` - SQL Server
- `oracle` - Oracle Database
- `sqlite` - SQLite
- `mongodb` - MongoDB

`--include-views` - Document database views
- Default: `true`

`--include-procedures` - Document stored procedures
- Default: `true`

`--generate-erd` - Create entity relationship diagrams
- Default: `true`

`--analyze-implicit` - Find implicit relationships
- Default: `true`

`--output-format <format>` - Documentation format
- `html` - Interactive HTML (default)
- `markdown` - Markdown files
- `pdf` - PDF document
- `json` - JSON data dictionary
- `all` - All formats

`--theme <theme>` - HTML documentation theme
- `default` - Standard theme
- `dark` - Dark mode
- `minimal` - Minimal design
- `corporate` - Professional style

## Best Practices

DO:
- Run documentation generation in CI/CD pipeline
- Version control your database documentation
- Include business context in table/column comments
- Document implicit relationships and business rules
- Generate documentation after each schema migration
- Review orphan tables and missing relationships

DON'T:
- Expose production credentials in documentation
- Include sensitive data in examples
- Skip documenting views and procedures
- Ignore schema anomalies and warnings
- Generate documentation from development databases only

## Performance Considerations

- Large schemas (1000+ tables) may require increased memory
- ERD generation can be slow for complex relationships
- Consider splitting documentation by schema/module
- Use caching for repeated documentation generations
- Limit diagram complexity for better readability

## Security Considerations

- Use read-only database credentials
- Sanitize any example data in documentation
- Don't include connection strings in generated docs
- Review documentation for accidentally exposed sensitive column names
- Implement access control for documentation hosting

## Related Commands

- `/design-schema` - Design new database schemas
- `/optimize-query` - Optimize database queries
- `/migration` - Manage database migrations
- `/backup` - Backup database
- `/seed-data` - Generate test data

## Version History

- v1.0.0 (2024-10): Initial implementation with multi-database support
- Planned v1.1.0: Add MongoDB and graph database support