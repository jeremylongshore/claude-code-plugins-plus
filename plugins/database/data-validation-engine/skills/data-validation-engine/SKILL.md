---
name: validating-database-integrity
description: |
  Use when you need to ensure database integrity through comprehensive data validation.
  This skill validates data types, ranges, formats, referential integrity, and business rules.
  Trigger with phrases like "validate database data", "implement data validation rules",
  "enforce data integrity constraints", or "validate data formats".
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(psql:*, mysql:*)
version: 1.0.0
license: MIT
---

## Prerequisites

Before using this skill, ensure:
- Database connection credentials are available
- Appropriate database permissions for schema modifications
- Backup of production databases before applying constraints
- Understanding of existing data that may violate new constraints
- Access to database documentation for column specifications

## Instructions

### Step 1: Analyze Validation Requirements
1. Review database schema and identify columns requiring validation
2. Determine validation types needed (data type, range, format, referential)
3. Document existing data patterns that may conflict with new rules
4. Prioritize validation rules by business criticality

### Step 2: Define Validation Rules
1. Create validation rule definitions for each column
2. Specify data types, constraints, and acceptable ranges
3. Define regular expressions for format validation
4. Map foreign key relationships for referential integrity
5. Document business rule logic for complex validations

### Step 3: Implement Database Constraints
1. Generate SQL constraints for data type validation
2. Add CHECK constraints for range and format validation
3. Create foreign key constraints for referential integrity
4. Implement triggers for complex business rule validation
5. Test constraints with valid and invalid sample data

### Step 4: Validate Existing Data
1. Query existing data to identify constraint violations
2. Generate reports of data that would fail new constraints
3. Create data cleanup scripts to fix violations
4. Execute cleanup scripts in staging environment first
5. Re-validate cleaned data before applying constraints

### Step 5: Apply Validation Rules
1. Apply constraints to staging database first
2. Monitor for any application errors or failures
3. Validate that legitimate operations still function
4. Apply constraints to production database during maintenance window
5. Monitor database logs for constraint violation attempts

## Output

This skill produces:

**Database Constraints**: SQL DDL statements with CHECK, FOREIGN KEY, and NOT NULL constraints

**Validation Reports**: Analysis of existing data showing constraint violations with counts and examples

**Data Cleanup Scripts**: SQL UPDATE/DELETE statements to fix existing data that violates new constraints

**Test Results**: Documentation of constraint testing with valid/invalid data samples and outcomes

**Implementation Log**: Timestamped record of constraint application with success/failure status

## Error Handling

**Constraint Violation Errors**:
- Review existing data that violates the constraint
- Create data cleanup scripts to fix violations
- Re-run constraint application after cleanup
- Document exceptions that require manual review

**Permission Errors**:
- Verify database user has ALTER TABLE privileges
- Request elevated permissions from database administrator
- Use separate admin connection for schema changes
- Document permission requirements for future deployments

**Circular Dependency Errors**:
- Map all foreign key relationships before implementation
- Apply constraints in dependency order (referenced tables first)
- Use ALTER TABLE ADD CONSTRAINT for deferred constraint creation
- Consider disabling foreign key checks temporarily during bulk operations

**Performance Degradation**:
- Analyze constraint checking overhead with EXPLAIN ANALYZE
- Add appropriate indexes to support constraint validation
- Consider batch validation for large data updates
- Monitor query performance after constraint implementation

## Resources

**Database-Specific Constraint Syntax**:
- PostgreSQL: `{baseDir}/docs/postgresql-constraints.md`
- MySQL: `{baseDir}/docs/mysql-constraints.md`
- SQL Server: `{baseDir}/docs/sqlserver-constraints.md`

**Validation Rule Templates**: `{baseDir}/templates/validation-rules/`
- Email format validation
- Phone number validation
- Date range validation
- Numeric range validation
- Custom business rules

**Testing Guidelines**: `{baseDir}/docs/validation-testing.md`
**Constraint Performance Analysis**: `{baseDir}/docs/constraint-performance.md`
**Data Cleanup Procedures**: `{baseDir}/docs/data-cleanup-procedures.md`