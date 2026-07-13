#!/usr/bin/env python3
"""
Backup Validator

Validates the integrity of database backup files.
Supports PostgreSQL, MySQL, MongoDB, and SQLite backup formats.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import argparse
import gzip
import hashlib
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class ValidationResult:
    """Result of backup validation."""

    valid: bool
    file_path: str
    file_size: int
    db_type: str
    compressed: bool
    encrypted: bool
    checksum: str
    errors: list
    warnings: list
    details: dict


def detect_file_type(file_path: Path) -> Tuple[str, bool, bool]:
    """Detect database type, compression, and encryption from file."""
    name = file_path.name.lower()
    suffixes = file_path.suffixes

    encrypted = ".gpg" in suffixes or ".enc" in suffixes
    compressed = ".gz" in suffixes or ".tar" in suffixes

    # Remove encryption/compression suffixes for base detection
    base_name = name
    for ext in [".gpg", ".enc", ".gz", ".tar"]:
        base_name = base_name.replace(ext, "")

    if base_name.endswith(".dump") or "postgresql" in base_name or "pg_" in base_name:
        return "postgresql", compressed, encrypted
    elif base_name.endswith(".sql") or "mysql" in base_name:
        return "mysql", compressed, encrypted
    elif base_name.endswith(".bson") or "mongodb" in base_name or "mongo" in base_name:
        return "mongodb", compressed, encrypted
    elif base_name.endswith(".db") or "sqlite" in base_name:
        return "sqlite", compressed, encrypted

    return "unknown", compressed, encrypted


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def validate_postgresql(file_path: Path, compressed: bool) -> ValidationResult:
    """Validate PostgreSQL backup file."""
    errors = []
    warnings = []
    details = {}

    # For custom format (.dump), use pg_restore --list
    try:
        result = subprocess.run(["pg_restore", "--list", str(file_path)], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            details["objects"] = len([l for l in lines if l.strip() and not l.startswith(";")])
            details["format"] = "custom"
        else:
            # Try reading as SQL
            if compressed:
                with gzip.open(file_path, "rt", errors="ignore") as f:
                    header = f.read(1000)
            else:
                with open(file_path, "r", errors="ignore") as f:
                    header = f.read(1000)

            if "PostgreSQL database dump" in header or "pg_dump" in header:
                details["format"] = "plain_sql"
            else:
                errors.append("Could not verify PostgreSQL backup format")

    except subprocess.TimeoutExpired:
        warnings.append("Validation timed out - file may be very large")
    except FileNotFoundError:
        warnings.append("pg_restore not found - limited validation")
        # Fallback: check file headers
        if compressed:
            try:
                with gzip.open(file_path, "rt", errors="ignore") as f:
                    header = f.read(500)
                if "PostgreSQL" in header or "pg_dump" in header:
                    details["format"] = "plain_sql_gzip"
            except Exception:
                errors.append("Could not read gzip file")

    return ValidationResult(
        valid=len(errors) == 0,
        file_path=str(file_path),
        file_size=file_path.stat().st_size,
        db_type="postgresql",
        compressed=compressed,
        encrypted=False,
        checksum=calculate_checksum(file_path),
        errors=errors,
        warnings=warnings,
        details=details,
    )


def validate_mysql(file_path: Path, compressed: bool) -> ValidationResult:
    """Validate MySQL backup file."""
    errors = []
    warnings = []
    details = {}

    try:
        if compressed:
            with gzip.open(file_path, "rt", errors="ignore") as f:
                header = f.read(2000)
        else:
            with open(file_path, "r", errors="ignore") as f:
                header = f.read(2000)

        # Check for MySQL dump signature
        if "MySQL dump" in header or "mysqldump" in header.lower():
            details["format"] = "mysqldump"

            # Try to extract version
            for line in header.split("\n"):
                if "Server version" in line:
                    details["server_version"] = line.split(":")[-1].strip()
                    break

            # Count tables
            if "CREATE TABLE" in header:
                details["has_schema"] = True
            if "INSERT INTO" in header:
                details["has_data"] = True

        else:
            errors.append("File does not appear to be a MySQL dump")

    except gzip.BadGzipFile:
        errors.append("Invalid gzip format")
    except Exception as e:
        errors.append(f"Error reading file: {e}")

    return ValidationResult(
        valid=len(errors) == 0,
        file_path=str(file_path),
        file_size=file_path.stat().st_size,
        db_type="mysql",
        compressed=compressed,
        encrypted=False,
        checksum=calculate_checksum(file_path),
        errors=errors,
        warnings=warnings,
        details=details,
    )


def validate_mongodb(file_path: Path, compressed: bool) -> ValidationResult:
    """Validate MongoDB backup (directory or archive)."""
    errors = []
    warnings = []
    details = {}

    if file_path.is_dir():
        # Directory format
        bson_files = list(file_path.rglob("*.bson*"))
        metadata_files = list(file_path.rglob("*.metadata.json*"))

        if bson_files:
            details["bson_files"] = len(bson_files)
            details["collections"] = len(metadata_files)
            details["format"] = "directory"
        else:
            errors.append("No BSON files found in backup directory")

    elif file_path.suffix == ".tar":
        # Tar archive
        try:
            result = subprocess.run(["tar", "-tf", str(file_path)], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                files = result.stdout.strip().split("\n")
                bson_count = len([f for f in files if ".bson" in f])
                if bson_count > 0:
                    details["bson_files"] = bson_count
                    details["format"] = "tar_archive"
                else:
                    errors.append("No BSON files in archive")
            else:
                errors.append("Could not read tar archive")
        except Exception as e:
            errors.append(f"Error reading archive: {e}")

    else:
        # Single BSON file
        if file_path.stat().st_size > 0:
            details["format"] = "single_bson"
        else:
            errors.append("Empty backup file")

    return ValidationResult(
        valid=len(errors) == 0,
        file_path=str(file_path),
        file_size=file_path.stat().st_size
        if file_path.is_file()
        else sum(f.stat().st_size for f in file_path.rglob("*") if f.is_file()),
        db_type="mongodb",
        compressed=compressed,
        encrypted=False,
        checksum=calculate_checksum(file_path) if file_path.is_file() else "N/A (directory)",
        errors=errors,
        warnings=warnings,
        details=details,
    )


def validate_sqlite(file_path: Path, compressed: bool) -> ValidationResult:
    """Validate SQLite backup file."""
    errors = []
    warnings = []
    details = {}

    # Decompress if needed
    if compressed and file_path.suffix == ".gz":
        # Read header from gzip
        try:
            with gzip.open(file_path, "rb") as f:
                header = f.read(16)
        except Exception as e:
            errors.append(f"Could not read gzip file: {e}")
            header = b""
    else:
        with open(file_path, "rb") as f:
            header = f.read(16)

    # SQLite magic bytes
    if header.startswith(b"SQLite format 3"):
        details["format"] = "sqlite3"

        # If not compressed, run integrity check
        if not compressed:
            try:
                result = subprocess.run(
                    ["sqlite3", str(file_path), "PRAGMA integrity_check;"], capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0 and "ok" in result.stdout.lower():
                    details["integrity_check"] = "passed"
                else:
                    warnings.append(f"Integrity check: {result.stdout.strip()}")
                    details["integrity_check"] = "failed"

                # Get table count
                result = subprocess.run(
                    ["sqlite3", str(file_path), "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    details["table_count"] = int(result.stdout.strip())

            except FileNotFoundError:
                warnings.append("sqlite3 not found - limited validation")
            except subprocess.TimeoutExpired:
                warnings.append("Validation timed out")
    elif compressed:
        warnings.append("Cannot fully validate compressed SQLite backup")
        details["format"] = "sqlite3_compressed"
    else:
        errors.append("File does not appear to be SQLite format")

    return ValidationResult(
        valid=len(errors) == 0,
        file_path=str(file_path),
        file_size=file_path.stat().st_size,
        db_type="sqlite",
        compressed=compressed,
        encrypted=False,
        checksum=calculate_checksum(file_path),
        errors=errors,
        warnings=warnings,
        details=details,
    )


def validate_backup(file_path: Path, db_type: Optional[str] = None) -> ValidationResult:
    """Validate a backup file."""
    if not file_path.exists():
        return ValidationResult(
            valid=False,
            file_path=str(file_path),
            file_size=0,
            db_type="unknown",
            compressed=False,
            encrypted=False,
            checksum="",
            errors=[f"File not found: {file_path}"],
            warnings=[],
            details={},
        )

    # Detect type if not specified
    detected_type, compressed, encrypted = detect_file_type(file_path)
    if db_type:
        detected_type = db_type

    if encrypted:
        return ValidationResult(
            valid=True,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            db_type=detected_type,
            compressed=compressed,
            encrypted=True,
            checksum=calculate_checksum(file_path),
            errors=[],
            warnings=["Encrypted backup - content validation skipped"],
            details={"encrypted": True},
        )

    validators = {
        "postgresql": validate_postgresql,
        "mysql": validate_mysql,
        "mongodb": validate_mongodb,
        "sqlite": validate_sqlite,
    }

    if detected_type in validators:
        result = validators[detected_type](file_path, compressed)
        result.encrypted = encrypted
        return result

    return ValidationResult(
        valid=False,
        file_path=str(file_path),
        file_size=file_path.stat().st_size,
        db_type=detected_type,
        compressed=compressed,
        encrypted=encrypted,
        checksum=calculate_checksum(file_path),
        errors=[f"Unknown database type: {detected_type}"],
        warnings=[],
        details={},
    )


def print_result(result: ValidationResult, verbose: bool = False) -> None:
    """Print validation result."""
    status = "VALID" if result.valid else "INVALID"
    print(f"\nBackup Validation: {status}")
    print("=" * 50)
    print(f"File: {result.file_path}")
    print(f"Size: {result.file_size:,} bytes ({result.file_size / 1024 / 1024:.2f} MB)")
    print(f"Type: {result.db_type}")
    print(f"Compressed: {result.compressed}")
    print(f"Encrypted: {result.encrypted}")
    print(f"Checksum (SHA256): {result.checksum[:16]}...")

    if result.details and verbose:
        print("\nDetails:")
        for key, value in result.details.items():
            print(f"  {key}: {value}")

    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")


def main():
    parser = argparse.ArgumentParser(description="Validate database backup file integrity")
    parser.add_argument("backup_file", help="Backup file to validate")
    parser.add_argument(
        "--db-type",
        "-t",
        choices=["postgresql", "mysql", "mongodb", "sqlite"],
        help="Database type (auto-detected if not specified)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--checksum-file", "-c", help="Write checksum to file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    file_path = Path(args.backup_file)
    result = validate_backup(file_path, args.db_type)

    if args.json:
        import json

        print(
            json.dumps(
                {
                    "valid": result.valid,
                    "file_path": result.file_path,
                    "file_size": result.file_size,
                    "db_type": result.db_type,
                    "compressed": result.compressed,
                    "encrypted": result.encrypted,
                    "checksum": result.checksum,
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "details": result.details,
                },
                indent=2,
            )
        )
    else:
        print_result(result, args.verbose)

    if args.checksum_file:
        Path(args.checksum_file).write_text(f"{result.checksum}  {result.file_path}\n")
        print(f"\nChecksum written to: {args.checksum_file}")

    return 0 if result.valid else 1


if __name__ == "__main__":
    sys.exit(main())
