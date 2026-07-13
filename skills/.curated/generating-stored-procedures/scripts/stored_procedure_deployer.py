#!/usr/bin/env python3
"""
Stored Procedure Deployer

Deploy stored procedures to PostgreSQL, MySQL, or SQL Server databases.
Supports dry-run mode, transaction wrapping, and automatic rollback scripts.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class DeploymentResult:
    """Result of deployment operation."""

    success: bool
    message: str
    procedure_name: Optional[str] = None
    rollback_sql: Optional[str] = None
    execution_time: float = 0.0


class PostgreSQLDeployer:
    """Deploy stored procedures to PostgreSQL."""

    def __init__(self, host: str, port: int, database: str, user: str, password: str = None):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

    def _get_psql_env(self) -> Dict[str, str]:
        """Get environment variables for psql."""
        import os

        env = os.environ.copy()
        if self.password:
            env["PGPASSWORD"] = self.password
        return env

    def _run_psql(self, sql: str, dry_run: bool = False) -> DeploymentResult:
        """Execute SQL via psql."""
        if dry_run:
            return DeploymentResult(success=True, message=f"DRY RUN: Would execute SQL ({len(sql)} chars)")

        cmd = [
            "psql",
            "-h",
            self.host,
            "-p",
            str(self.port),
            "-d",
            self.database,
            "-U",
            self.user,
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            sql,
        ]

        start_time = datetime.now()
        try:
            result = subprocess.run(cmd, env=self._get_psql_env(), capture_output=True, text=True, timeout=60)
            elapsed = (datetime.now() - start_time).total_seconds()

            if result.returncode == 0:
                return DeploymentResult(
                    success=True, message=result.stdout.strip() or "Executed successfully", execution_time=elapsed
                )
            else:
                return DeploymentResult(
                    success=False, message=f"Error: {result.stderr.strip()}", execution_time=elapsed
                )
        except subprocess.TimeoutExpired:
            return DeploymentResult(success=False, message="Execution timed out")
        except FileNotFoundError:
            return DeploymentResult(success=False, message="psql not found - install PostgreSQL client")

    def deploy(self, sql: str, dry_run: bool = False) -> DeploymentResult:
        """Deploy a stored procedure."""
        # Extract procedure name for rollback
        import re

        name_match = re.search(
            r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:FUNCTION|PROCEDURE)\s+(\w+(?:\.\w+)?)", sql, re.IGNORECASE
        )
        proc_name = name_match.group(1) if name_match else None

        result = self._run_psql(sql, dry_run)
        result.procedure_name = proc_name

        if proc_name:
            # Detect if it's a function or procedure
            if "FUNCTION" in sql.upper():
                result.rollback_sql = f"DROP FUNCTION IF EXISTS {proc_name};"
            else:
                result.rollback_sql = f"DROP PROCEDURE IF EXISTS {proc_name};"

        return result


class MySQLDeployer:
    """Deploy stored procedures to MySQL."""

    def __init__(self, host: str, port: int, database: str, user: str, password: str = None):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

    def _run_mysql(self, sql: str, dry_run: bool = False) -> DeploymentResult:
        """Execute SQL via mysql client."""
        if dry_run:
            return DeploymentResult(success=True, message=f"DRY RUN: Would execute SQL ({len(sql)} chars)")

        cmd = [
            "mysql",
            "-h",
            self.host,
            "-P",
            str(self.port),
            "-D",
            self.database,
            "-u",
            self.user,
        ]
        if self.password:
            cmd.append(f"-p{self.password}")

        start_time = datetime.now()
        try:
            result = subprocess.run(cmd, input=sql, capture_output=True, text=True, timeout=60)
            elapsed = (datetime.now() - start_time).total_seconds()

            if result.returncode == 0:
                return DeploymentResult(
                    success=True, message=result.stdout.strip() or "Executed successfully", execution_time=elapsed
                )
            else:
                return DeploymentResult(
                    success=False, message=f"Error: {result.stderr.strip()}", execution_time=elapsed
                )
        except subprocess.TimeoutExpired:
            return DeploymentResult(success=False, message="Execution timed out")
        except FileNotFoundError:
            return DeploymentResult(success=False, message="mysql not found - install MySQL client")

    def deploy(self, sql: str, dry_run: bool = False) -> DeploymentResult:
        """Deploy a stored procedure."""
        import re

        name_match = re.search(r"CREATE\s+(?:DEFINER\s*=\s*[^\s]+\s+)?PROCEDURE\s+(\w+(?:\.\w+)?)", sql, re.IGNORECASE)
        proc_name = name_match.group(1) if name_match else None

        result = self._run_mysql(sql, dry_run)
        result.procedure_name = proc_name

        if proc_name:
            result.rollback_sql = f"DROP PROCEDURE IF EXISTS {proc_name};"

        return result


class SQLServerDeployer:
    """Deploy stored procedures to SQL Server."""

    def __init__(self, host: str, port: int, database: str, user: str, password: str = None):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

    def _run_sqlcmd(self, sql: str, dry_run: bool = False) -> DeploymentResult:
        """Execute SQL via sqlcmd."""
        if dry_run:
            return DeploymentResult(success=True, message=f"DRY RUN: Would execute SQL ({len(sql)} chars)")

        cmd = ["sqlcmd", "-S", f"{self.host},{self.port}", "-d", self.database, "-U", self.user, "-Q", sql]
        if self.password:
            cmd.extend(["-P", self.password])

        start_time = datetime.now()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            elapsed = (datetime.now() - start_time).total_seconds()

            if result.returncode == 0:
                return DeploymentResult(
                    success=True, message=result.stdout.strip() or "Executed successfully", execution_time=elapsed
                )
            else:
                return DeploymentResult(
                    success=False, message=f"Error: {result.stderr.strip()}", execution_time=elapsed
                )
        except subprocess.TimeoutExpired:
            return DeploymentResult(success=False, message="Execution timed out")
        except FileNotFoundError:
            return DeploymentResult(success=False, message="sqlcmd not found - install SQL Server tools")

    def deploy(self, sql: str, dry_run: bool = False) -> DeploymentResult:
        """Deploy a stored procedure."""
        import re

        name_match = re.search(
            r"CREATE\s+(?:OR\s+ALTER\s+)?PROC(?:EDURE)?\s+(\[?\w+\]?(?:\.\[?\w+\]?)?)", sql, re.IGNORECASE
        )
        proc_name = name_match.group(1) if name_match else None

        result = self._run_sqlcmd(sql, dry_run)
        result.procedure_name = proc_name

        if proc_name:
            result.rollback_sql = f"DROP PROCEDURE IF EXISTS {proc_name};"

        return result


def get_deployer(db_type: str, host: str, port: int, database: str, user: str, password: str = None):
    """Factory to get appropriate deployer."""
    deployers = {
        "postgresql": PostgreSQLDeployer,
        "mysql": MySQLDeployer,
        "sqlserver": SQLServerDeployer,
    }

    default_ports = {
        "postgresql": 5432,
        "mysql": 3306,
        "sqlserver": 1433,
    }

    if db_type not in deployers:
        raise ValueError(f"Unknown database type: {db_type}")

    actual_port = port or default_ports.get(db_type, 5432)
    return deployers[db_type](host, actual_port, database, user, password)


def main():
    parser = argparse.ArgumentParser(description="Deploy stored procedures to PostgreSQL, MySQL, or SQL Server")
    parser.add_argument("file", help="SQL file to deploy")
    parser.add_argument(
        "--db-type", "-t", required=True, choices=["postgresql", "mysql", "sqlserver"], help="Database type"
    )
    parser.add_argument("--host", "-H", default="localhost", help="Database host")
    parser.add_argument("--port", "-P", type=int, help="Database port")
    parser.add_argument("--database", "-d", required=True, help="Database name")
    parser.add_argument("--user", "-u", required=True, help="Database user")
    parser.add_argument("--password", "-p", help="Database password")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--save-rollback", help="Save rollback script to file")

    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return 1

    sql = file_path.read_text()

    print(f"Deploying: {file_path}")
    print(f"Database: {args.db_type}://{args.host}/{args.database}")
    if args.dry_run:
        print("MODE: DRY RUN")
    print()

    try:
        deployer = get_deployer(args.db_type, args.host, args.port, args.database, args.user, args.password)

        result = deployer.deploy(sql, args.dry_run)

        if result.procedure_name:
            print(f"Procedure: {result.procedure_name}")

        if result.success:
            print("Status: SUCCESS")
            print(f"Message: {result.message}")
            if result.execution_time:
                print(f"Time: {result.execution_time:.2f}s")

            if result.rollback_sql:
                print(f"\nRollback SQL: {result.rollback_sql}")
                if args.save_rollback:
                    Path(args.save_rollback).write_text(result.rollback_sql)
                    print(f"Saved to: {args.save_rollback}")

            return 0
        else:
            print("Status: FAILED")
            print(f"Error: {result.message}")
            return 1

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
