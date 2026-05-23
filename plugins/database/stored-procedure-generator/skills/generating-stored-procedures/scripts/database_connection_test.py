#!/usr/bin/env python3
"""
Database Connection Test

Test connectivity to PostgreSQL, MySQL, or SQL Server databases.
Verifies credentials and permissions needed for stored procedure operations.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import sys
import argparse
import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ConnectionResult:
    """Result of connection test."""

    success: bool
    message: str
    version: Optional[str] = None
    permissions: List[str] = None


def check_postgresql(host: str, port: int, database: str, user: str, password: str = None) -> ConnectionResult:
    """Test PostgreSQL connection and permissions."""
    import os

    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password

    # Test basic connectivity
    cmd = ["psql", "-h", host, "-p", str(port), "-d", database, "-U", user, "-c", "SELECT version();"]

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return ConnectionResult(success=False, message=f"Connection failed: {result.stderr.strip()}")

        version = result.stdout.strip().split("\n")[2].strip() if result.stdout else None

        # Check permissions
        perm_cmd = [
            "psql",
            "-h",
            host,
            "-p",
            str(port),
            "-d",
            database,
            "-U",
            user,
            "-t",
            "-c",
            """
            SELECT string_agg(privilege_type, ', ')
            FROM information_schema.role_table_grants
            WHERE grantee = current_user;
            """,
        ]
        perm_result = subprocess.run(perm_cmd, env=env, capture_output=True, text=True, timeout=10)
        permissions = perm_result.stdout.strip().split(", ") if perm_result.returncode == 0 else []

        return ConnectionResult(success=True, message="Connection successful", version=version, permissions=permissions)

    except subprocess.TimeoutExpired:
        return ConnectionResult(success=False, message="Connection timed out")
    except FileNotFoundError:
        return ConnectionResult(success=False, message="psql not found - install PostgreSQL client")


def check_mysql(host: str, port: int, database: str, user: str, password: str = None) -> ConnectionResult:
    """Test MySQL connection and permissions."""
    cmd = ["mysql", "-h", host, "-P", str(port), "-D", database, "-u", user]
    if password:
        cmd.append(f"-p{password}")
    cmd.extend(["-e", "SELECT VERSION();"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return ConnectionResult(success=False, message=f"Connection failed: {result.stderr.strip()}")

        version = result.stdout.strip().split("\n")[-1] if result.stdout else None

        # Check permissions
        perm_cmd = ["mysql", "-h", host, "-P", str(port), "-D", database, "-u", user]
        if password:
            perm_cmd.append(f"-p{password}")
        perm_cmd.extend(["-e", "SHOW GRANTS;"])

        perm_result = subprocess.run(perm_cmd, capture_output=True, text=True, timeout=10)
        permissions = []
        if perm_result.returncode == 0:
            for line in perm_result.stdout.split("\n"):
                if "GRANT" in line:
                    permissions.append(line.strip())

        return ConnectionResult(success=True, message="Connection successful", version=version, permissions=permissions)

    except subprocess.TimeoutExpired:
        return ConnectionResult(success=False, message="Connection timed out")
    except FileNotFoundError:
        return ConnectionResult(success=False, message="mysql not found - install MySQL client")


def check_sqlserver(host: str, port: int, database: str, user: str, password: str = None) -> ConnectionResult:
    """Test SQL Server connection and permissions."""
    cmd = ["sqlcmd", "-S", f"{host},{port}", "-d", database, "-U", user, "-Q", "SELECT @@VERSION;"]
    if password:
        cmd.extend(["-P", password])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return ConnectionResult(success=False, message=f"Connection failed: {result.stderr.strip()}")

        version = result.stdout.strip().split("\n")[2] if result.stdout else None

        # Check permissions
        perm_cmd = [
            "sqlcmd",
            "-S",
            f"{host},{port}",
            "-d",
            database,
            "-U",
            user,
            "-Q",
            "SELECT permission_name FROM fn_my_permissions(NULL, 'DATABASE');",
        ]
        if password:
            perm_cmd.extend(["-P", password])

        perm_result = subprocess.run(perm_cmd, capture_output=True, text=True, timeout=10)
        permissions = []
        if perm_result.returncode == 0:
            for line in perm_result.stdout.split("\n"):
                if line.strip() and not line.startswith("-") and "permission_name" not in line.lower():
                    permissions.append(line.strip())

        return ConnectionResult(success=True, message="Connection successful", version=version, permissions=permissions)

    except subprocess.TimeoutExpired:
        return ConnectionResult(success=False, message="Connection timed out")
    except FileNotFoundError:
        return ConnectionResult(success=False, message="sqlcmd not found - install SQL Server tools")


def main():
    parser = argparse.ArgumentParser(description="Test database connectivity for stored procedure deployment")
    parser.add_argument(
        "--db-type", "-t", required=True, choices=["postgresql", "mysql", "sqlserver"], help="Database type"
    )
    parser.add_argument("--host", "-H", default="localhost", help="Database host")
    parser.add_argument("--port", "-P", type=int, help="Database port")
    parser.add_argument("--database", "-d", required=True, help="Database name")
    parser.add_argument("--user", "-u", required=True, help="Database user")
    parser.add_argument("--password", "-p", help="Database password")

    args = parser.parse_args()

    default_ports = {
        "postgresql": 5432,
        "mysql": 3306,
        "sqlserver": 1433,
    }
    port = args.port or default_ports.get(args.db_type, 5432)

    print(f"Testing connection to {args.db_type}://{args.host}:{port}/{args.database}")
    print(f"User: {args.user}")
    print()

    testers = {
        "postgresql": check_postgresql,
        "mysql": check_mysql,
        "sqlserver": check_sqlserver,
    }

    result = testers[args.db_type](args.host, port, args.database, args.user, args.password)

    if result.success:
        print("Status: SUCCESS")
        print(f"Version: {result.version or 'Unknown'}")
        if result.permissions:
            print("\nPermissions:")
            for perm in result.permissions[:10]:  # Limit output
                print(f"  - {perm}")
            if len(result.permissions) > 10:
                print(f"  ... and {len(result.permissions) - 10} more")
        return 0
    else:
        print("Status: FAILED")
        print(f"Error: {result.message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
