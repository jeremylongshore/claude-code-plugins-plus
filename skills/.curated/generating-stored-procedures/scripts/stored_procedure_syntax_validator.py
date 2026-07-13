#!/usr/bin/env python3
"""
Stored Procedure Syntax Validator

Validates SQL stored procedure syntax for PostgreSQL, MySQL, and SQL Server.
Performs static analysis without requiring database connection.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import re
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ValidationResult:
    """Result of syntax validation."""

    valid: bool
    errors: List[str]
    warnings: List[str]
    db_type: str
    procedure_name: Optional[str] = None


class PostgreSQLValidator:
    """Validate PostgreSQL/PL/pgSQL stored procedure syntax."""

    REQUIRED_PATTERNS = [
        (r"CREATE\s+(OR\s+REPLACE\s+)?(FUNCTION|PROCEDURE)", "Missing CREATE FUNCTION/PROCEDURE"),
        (r"LANGUAGE\s+(plpgsql|sql|plpython\w*)", "Missing LANGUAGE clause"),
    ]

    FUNCTION_PATTERNS = [
        (r"RETURNS\s+(\w+|SETOF\s+\w+|TABLE\s*\()", "Function missing RETURNS clause"),
    ]

    WARNING_PATTERNS = [
        (r"\bSELECT\s+\*\b", "Avoid SELECT * - specify columns explicitly"),
        (r"SECURITY\s+DEFINER(?!\s+SET\s+search_path)", "SECURITY DEFINER without SET search_path is risky"),
        (r'\bEXECUTE\s+[\'"]', "Dynamic SQL detected - ensure proper parameterization"),
    ]

    def validate(self, sql: str) -> ValidationResult:
        errors = []
        warnings = []
        proc_name = None

        # Extract procedure name
        name_match = re.search(
            r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:FUNCTION|PROCEDURE)\s+(\w+(?:\.\w+)?)", sql, re.IGNORECASE
        )
        if name_match:
            proc_name = name_match.group(1)

        # Check required patterns
        for pattern, error_msg in self.REQUIRED_PATTERNS:
            if not re.search(pattern, sql, re.IGNORECASE):
                errors.append(error_msg)

        # Check if function has RETURNS
        if re.search(r"CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION", sql, re.IGNORECASE):
            for pattern, error_msg in self.FUNCTION_PATTERNS:
                if not re.search(pattern, sql, re.IGNORECASE):
                    errors.append(error_msg)

        # Check warnings
        for pattern, warning_msg in self.WARNING_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                warnings.append(warning_msg)

        # Check balanced $$ delimiters
        dollar_count = sql.count("$$")
        if dollar_count % 2 != 0:
            errors.append("Unbalanced $$ delimiters")

        # Check for BEGIN/END balance in plpgsql
        if "plpgsql" in sql.lower():
            begin_count = len(re.findall(r"\bBEGIN\b", sql, re.IGNORECASE))
            end_count = len(re.findall(r"\bEND\b", sql, re.IGNORECASE))
            # Account for EXCEPTION blocks which don't need separate END
            if begin_count > end_count:
                errors.append(f"Unbalanced BEGIN/END blocks: {begin_count} BEGIN vs {end_count} END")

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings, db_type="postgresql", procedure_name=proc_name
        )


class MySQLValidator:
    """Validate MySQL stored procedure syntax."""

    REQUIRED_PATTERNS = [
        (r"CREATE\s+(?:DEFINER\s*=\s*[^\s]+\s+)?PROCEDURE", "Missing CREATE PROCEDURE"),
        (r"\bBEGIN\b", "Missing BEGIN keyword"),
        (r"\bEND\b", "Missing END keyword"),
    ]

    WARNING_PATTERNS = [
        (r"\bSELECT\s+\*\b", "Avoid SELECT * - specify columns explicitly"),
        (r"CONCAT\s*\([^)]*\+[^)]*\)", "Potential SQL injection - use prepared statements"),
        (r"@\w+\s*:=", "User variables persist across calls - initialize explicitly"),
    ]

    def validate(self, sql: str) -> ValidationResult:
        errors = []
        warnings = []
        proc_name = None

        # Extract procedure name
        name_match = re.search(r"CREATE\s+(?:DEFINER\s*=\s*[^\s]+\s+)?PROCEDURE\s+(\w+(?:\.\w+)?)", sql, re.IGNORECASE)
        if name_match:
            proc_name = name_match.group(1)

        # Check DELIMITER usage
        if "DELIMITER" not in sql.upper() and sql.count(";") > 1:
            warnings.append("Multiple semicolons without DELIMITER - may cause issues")

        # Check required patterns
        for pattern, error_msg in self.REQUIRED_PATTERNS:
            if not re.search(pattern, sql, re.IGNORECASE):
                errors.append(error_msg)

        # Check warnings
        for pattern, warning_msg in self.WARNING_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                warnings.append(warning_msg)

        # Check BEGIN/END balance
        begin_count = len(re.findall(r"\bBEGIN\b", sql, re.IGNORECASE))
        end_count = len(re.findall(r"\bEND\b", sql, re.IGNORECASE))
        if begin_count != end_count:
            errors.append(f"Unbalanced BEGIN/END blocks: {begin_count} BEGIN vs {end_count} END")

        # Check parameter modes
        params_match = re.search(r"PROCEDURE\s+\w+\s*\(([^)]+)\)", sql, re.IGNORECASE | re.DOTALL)
        if params_match:
            params = params_match.group(1)
            if params.strip() and not re.search(r"\b(IN|OUT|INOUT)\b", params, re.IGNORECASE):
                warnings.append("Parameters should specify IN/OUT/INOUT mode")

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings, db_type="mysql", procedure_name=proc_name
        )


class SQLServerValidator:
    """Validate SQL Server T-SQL stored procedure syntax."""

    REQUIRED_PATTERNS = [
        (r"CREATE\s+(OR\s+ALTER\s+)?PROC(EDURE)?", "Missing CREATE PROCEDURE"),
        (r"\bAS\b", "Missing AS keyword"),
        (r"\bBEGIN\b", "Missing BEGIN keyword"),
        (r"\bEND\b", "Missing END keyword"),
    ]

    WARNING_PATTERNS = [
        (r"\bSELECT\s+\*\b", "Avoid SELECT * - specify columns explicitly"),
        (r'EXEC\s*\(\s*[\'"]', "Dynamic SQL detected - use sp_executesql with parameters"),
        (r"(?<!SET\s)NOCOUNT", "Consider SET NOCOUNT ON for better performance"),
    ]

    def validate(self, sql: str) -> ValidationResult:
        errors = []
        warnings = []
        proc_name = None

        # Extract procedure name
        name_match = re.search(
            r"CREATE\s+(?:OR\s+ALTER\s+)?PROC(?:EDURE)?\s+(\[?\w+\]?(?:\.\[?\w+\]?)?)", sql, re.IGNORECASE
        )
        if name_match:
            proc_name = name_match.group(1)

        # Check required patterns
        for pattern, error_msg in self.REQUIRED_PATTERNS:
            if not re.search(pattern, sql, re.IGNORECASE):
                errors.append(error_msg)

        # Check warnings
        for pattern, warning_msg in self.WARNING_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                warnings.append(warning_msg)

        # Check for SET NOCOUNT ON
        if not re.search(r"SET\s+NOCOUNT\s+ON", sql, re.IGNORECASE):
            warnings.append("Missing SET NOCOUNT ON - recommended for performance")

        # Check BEGIN/END balance
        begin_count = len(re.findall(r"\bBEGIN\b", sql, re.IGNORECASE))
        end_count = len(re.findall(r"\bEND\b", sql, re.IGNORECASE))
        if begin_count != end_count:
            errors.append(f"Unbalanced BEGIN/END blocks: {begin_count} BEGIN vs {end_count} END")

        # Check for schema qualification
        if proc_name and "." not in proc_name:
            warnings.append("Procedure should be schema-qualified (e.g., dbo.ProcedureName)")

        # Check for GO statement
        if not re.search(r"\bGO\b", sql, re.IGNORECASE):
            warnings.append("Missing GO batch terminator")

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings, db_type="sqlserver", procedure_name=proc_name
        )


def detect_db_type(sql: str) -> str:
    """Auto-detect database type from SQL syntax."""
    sql_upper = sql.upper()

    # PostgreSQL indicators
    if "LANGUAGE PLPGSQL" in sql_upper or "$$" in sql or "RETURNS SETOF" in sql_upper:
        return "postgresql"

    # MySQL indicators
    if "DELIMITER" in sql_upper or "DEFINER=" in sql_upper or "SIGNAL SQLSTATE" in sql_upper:
        return "mysql"

    # SQL Server indicators
    if "@" in sql and ("AS BEGIN" in sql_upper or "SET NOCOUNT" in sql_upper):
        return "sqlserver"

    return "unknown"


def validate_file(file_path: Path, db_type: str = None) -> ValidationResult:
    """Validate a SQL file."""
    if not file_path.exists():
        return ValidationResult(valid=False, errors=[f"File not found: {file_path}"], warnings=[], db_type="unknown")

    sql = file_path.read_text()

    # Auto-detect if not specified
    if not db_type:
        db_type = detect_db_type(sql)

    validators = {
        "postgresql": PostgreSQLValidator(),
        "mysql": MySQLValidator(),
        "sqlserver": SQLServerValidator(),
    }

    if db_type not in validators:
        return ValidationResult(
            valid=False,
            errors=[f"Unknown database type: {db_type}. Use: postgresql, mysql, sqlserver"],
            warnings=[],
            db_type=db_type,
        )

    return validators[db_type].validate(sql)


def main():
    parser = argparse.ArgumentParser(
        description="Validate stored procedure syntax for PostgreSQL, MySQL, or SQL Server"
    )
    parser.add_argument("file", help="SQL file to validate")
    parser.add_argument(
        "--db-type",
        "-t",
        choices=["postgresql", "mysql", "sqlserver", "auto"],
        default="auto",
        help="Database type (default: auto-detect)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    file_path = Path(args.file)
    db_type = None if args.db_type == "auto" else args.db_type

    print(f"Validating: {file_path}")

    result = validate_file(file_path, db_type)

    print(f"Database type: {result.db_type}")
    if result.procedure_name:
        print(f"Procedure: {result.procedure_name}")
    print()

    if result.errors:
        print("ERRORS:")
        for error in result.errors:
            print(f"  - {error}")
        print()

    if result.warnings:
        print("WARNINGS:")
        for warning in result.warnings:
            print(f"  - {warning}")
        print()

    if result.valid:
        print("Result: VALID")
        return 0
    else:
        print("Result: INVALID")
        return 1


if __name__ == "__main__":
    sys.exit(main())
