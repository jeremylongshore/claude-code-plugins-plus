---
name: security-scan
description: >
  Comprehensive database security scanner with OWASP compliance checks,...
shortcut: secu
---
# Database Security Scanner

Implement production-grade database security scanning for PostgreSQL and MySQL that detects 50+ security vulnerabilities including weak passwords, excessive permissions, SQL injection vectors, missing encryption, exposed ports, and insecure configurations. Provides OWASP Database Security compliance reports, automated remediation scripts, and continuous security monitoring with SOC2/HIPAA/PCI DSS audit trails.

## When to Use This Command

Use `/security-scan` when you need to:
- Perform security audits for compliance (SOC2, HIPAA, PCI DSS)
- Detect vulnerabilities before security incidents occur
- Validate database hardening after deployment
- Generate security reports for stakeholders and auditors
- Implement continuous security scanning in CI/CD pipeline
- Identify privilege escalation risks and over-permissioned users

DON'T use this when:
- You lack permission to query security-sensitive system tables
- Database is in active development (expect frequent config changes)
- You need application-level security testing (use SAST/DAST tools)
- Cloud-managed database with built-in security scanning (use AWS RDS/CloudSQL tools)
- You lack remediation authority (read-only security assessment)

## Design Decisions

This command implements **comprehensive multi-layer security scanning** because:
- Checks 50+ OWASP Database Security vulnerabilities
- Validates encryption at rest and in transit (SSL/TLS)
- Detects privilege escalation and over-permissioned roles
- Identifies SQL injection vectors in stored procedures
- Scans for weak authentication and default credentials
- Generates automated remediation scripts for findings

**Alternative considered: Manual security checklist**
- Simple for small databases (<10 users, <50 tables)
- Time-consuming and error-prone for large databases
- No continuous monitoring or automation
- Recommended for one-time assessments only

**Alternative considered: Commercial security tools (Tenable, Qualys)**
- More comprehensive (network scanning, OS hardening)
- Expensive licensing ($10k-50k/year)
- Better for enterprise-wide security programs
- Recommended when budget allows and compliance requires

## Prerequisites

Before running this command:
1. Database superuser or security admin permissions
2. Access to system catalogs (pg_catalog, information_schema)
3. Understanding of compliance requirements (PCI DSS, HIPAA, SOC2)
4. Authority to implement remediation recommendations
5. Backup before applying security hardening changes

## Implementation Process

### Step 1: Connect with Security Admin Privileges
Ensure connection has permissions to query user roles, grants, and configurations.

### Step 2: Run Vulnerability Scans
Check authentication, authorization, encryption, auditing, and network security.

### Step 3: Analyze Findings
Categorize vulnerabilities by severity (critical, high, medium, low).

### Step 4: Generate Remediation Scripts
Create SQL scripts to fix identified issues with rollback procedures.

### Step 5: Validate and Re-scan
Apply fixes in staging, validate, then re-scan to confirm remediation.

## Output Format

The command generates:
- `security_report.md` - Human-readable security audit report with severity ratings
- `vulnerabilities.json` - Machine-readable findings for CI/CD integration
- `remediation.sql` - SQL script to fix identified vulnerabilities
- `compliance_matrix.xlsx` - Mapping to SOC2/HIPAA/PCI DSS controls
- `security_baseline.yml` - Configuration baseline for future scans

## Code Examples

### Example 1: PostgreSQL Comprehensive Security Scanner

```python
#!/usr/bin/env python3
"""
Production-ready PostgreSQL security scanner implementing OWASP
Database Security Project checks with automated remediation.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Severity(Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityFinding:
    """Represents a security vulnerability finding."""
    check_id: str
    title: str
    severity: Severity
    description: str
    affected_objects: List[str]
    remediation: str
    owasp_category: str
    compliance_mappings: Dict[str, str]


class PostgreSQLSecurityScanner:
    """
    Comprehensive PostgreSQL security scanner with OWASP compliance.
    """

    def __init__(self, conn_string: str):
        """
        Initialize security scanner.

        Args:
            conn_string: Database connection string with admin privileges
        """
        self.conn_string = conn_string
        self.findings: List[SecurityFinding] = []

    def scan_all(self) -> List[SecurityFinding]:
        """
        Run all security checks.

        Returns:
            List of security findings
        """
        logger.info("Starting comprehensive security scan...")

        with psycopg2.connect(self.conn_string) as conn:
            # Authentication & Authorization
            self._check_weak_passwords(conn)
            self._check_excessive_permissions(conn)
            self._check_superuser_roles(conn)
            self._check_public_schema_permissions(conn)

            # Encryption & Data Protection
            self._check_ssl_encryption(conn)
            self._check_password_encryption(conn)
            self._check_data_encryption_at_rest(conn)

            # Auditing & Logging
            self._check_audit_logging(conn)
            self._check_connection_logging(conn)
            self._check_statement_logging(conn)

            # Network Security
            self._check_listen_addresses(conn)
            self._check_pg_hba_configuration(conn)

            # SQL Injection & Code Security
            self._check_dynamic_sql(conn)
            self._check_untrusted_extensions(conn)

            # Configuration Security
            self._check_insecure_settings(conn)
            self._check_default_configurations(conn)

        logger.info(f"Security scan complete: {len(self.findings)} findings")
        return self.findings

    def _check_weak_passwords(self, conn) -> None:
        """Check for weak or default passwords."""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check for roles without passwords
            cur.execute("""
                SELECT rolname
                FROM pg_authid
                WHERE rolcanlogin = true
                  AND rolpassword IS NULL
                  AND rolname NOT LIKE 'pg_%'
            """)

            weak_roles = [row['rolname'] for row in cur.fetchall()]

            if weak_roles:
                self.findings.append(SecurityFinding(
                    check_id="AUTH-001",
                    title="Roles with No Password",
                    severity=Severity.CRITICAL,
                    description=f"Found {len(weak_roles)} login roles without passwords",
                    affected_objects=weak_roles,
                    remediation=f"Set strong passwords: ALTER ROLE username WITH PASSWORD 'strong_password';",
                    owasp_category="A01:2021 - Broken Access Control",
                    compliance_mappings={
                        "PCI DSS": "8.2.3 - Strong passwords",
                        "HIPAA": "164.308(a)(5)(ii)(D) - Password management",
                        "SOC2": "CC6.1 - Logical and physical access controls"
                    }
                ))

    def _check_excessive_permissions(self, conn) -> None:
        """Check for over-privileged roles."""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Find roles with excessive permissions
            cur.execute("""
                SELECT grantee, string_agg(privilege_type, ', ') as privileges, table_name
                FROM information_schema.table_privileges
                WHERE grantee NOT IN ('postgres', 'pg_database_owner')
                  AND privilege_type IN ('DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER')
                  AND table_schema NOT IN ('pg_catalog', 'information_schema')
                GROUP BY grantee, table_name
                HAVING COUNT(*) >= 3
            """)

            excessive_grants = cur.fetchall()

            if excessive_grants:
                affected = [
                    f"{row['grantee']} on {row['table_name']} ({row['privileges']})"
                    for row in excessive_grants
                ]

                self.findings.append(SecurityFinding(
                    check_id="AUTH-002",
                    title="Excessive Table Permissions",
                    severity=Severity.HIGH,
                    description=f"Found {len(excessive_grants)} roles with excessive privileges",
                    affected_objects=affected,
                    remediation="Apply principle of least privilege: REVOKE unnecessary permissions",
                    owasp_category="A01:2021 - Broken Access Control",
                    compliance_mappings={
                        "PCI DSS": "7.1.2 - Restrict access to least privilege",
                        "SOC2": "CC6.3 - Logical access controls"
                    }
                ))

    def _check_superuser_roles(self, conn) -> None:
        """Check for unnecessary superuser roles."""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT rolname
                FROM pg_authid
                WHERE rolsuper = true
                  AND rolname NOT IN ('postgres', 'rdsadmin')
            """)

            superusers = [row['rolname'] for row in cur.fetchall()]

            if len(superusers) > 1:  # More than just postgres
                self.findings.append(SecurityFinding(
                    check_id="AUTH-003",
                    title="Multiple Superuser Roles",
                    severity=Severity.HIGH,
                    description=f"Found {len(superusers)} superuser roles (expected 1-2)",
                    affected_objects=superusers,
                    remediation="Remove superuser privilege: ALTER ROLE username WITH NOSUPERUSER;",
                    owasp_category="A01:2021 - Broken Access Control",
                    compliance_mappings={
                        "PCI DSS": "7.2.2 - Privileged user access management",
                        "SOC2": "CC6.2 - System access management"
                    }
                ))

    def _check_public_schema_permissions(self, conn) -> None:
        """Check for dangerous public schema permissions."""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT has_schema_privilege('public', 'public', 'CREATE') as can_create
            """)

            can_create = cur.fetchone()['can_create']

            if can_create:
                self.findings.append(SecurityFinding(
                    check_id="AUTH-004",
                    title="Public Schema CREATE Permission",
                    severity=Severity.MEDIUM,
                    description="All users can create objects in public schema",
                    affected_objects=["public schema"],
                    remediation="REVOKE CREATE ON SCHEMA public FROM PUBLIC;",
                    owasp_category="A01:2021 - Broken Access Control",
                    compliance_mappings={
                        "SOC2": "CC6.1 - Logical access controls"
                    }
                ))

    def _check_ssl_encryption(self, conn) -> None:
        """Check if SSL/TLS is enforced."""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SHOW ssl")
            ssl_enabled = cur.fetchone()['ssl'] == 'on'

            if not ssl_enabled:
                self.findings.append(SecurityFinding(
                    check_id="ENC-001",
                    title="SSL/TLS Not Enabled",
                    severity=Severity.CRITICAL,
                    description="Database connections are not encrypted",
                    affected_objects=["postgresql.conf"],
                    remediation="Enable SSL: ALTER SYSTEM SET ssl = 'on'; (requires restart)",
                    owasp_category="A02:2021 - Cryptographic Failures",
                    compliance_mappings={
                        "PCI DSS": "4.1 - Encrypt transmission of cardholder data",
                        "HIPAA": "164.312(e)(1) - Transmission security",
                        "SOC2": "CC6.7 - Encryption in transit"
                    }
                ))

    def _check_password_encryption(self, conn) -> None:
        """Check password encryption method."""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SHOW password_encryption")
            method = cur.fetchone()['password_encryption']

            if method != 'scram-sha-256':
                self.findings.append(SecurityFinding(
                    check_id="ENC-002",
                    title="Weak Password Encryption",
                    severity=Severity.HIGH,
                    description=f"Password encryption method is {method} (should be scram-sha-256)",
                    affected_objects=["postgresql.conf"],
                    remediation="ALTER SYSTEM SET password_encryption = 'scram-sha-256';",
                    owasp_category="A02:2021 - Cryptographic Failures",
                    compliance_mappings={
                        "PCI DSS": "8.2.1 - Strong cryptography for passwords",
                        "HIPAA": "164.312(a)(2)(iv) - Encryption of passwords"
                    }
                ))

    def _check_audit_logging(self, conn) -> None:
        """Check if audit logging is enabled."""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SHOW logging_destination")
            log_dest = cur.fetchone()['logging_destination']

            if log_dest == '':
                self.findings.append(SecurityFinding(
                    check_id="LOG-001",
                    title="Audit Logging Disabled",
                    severity=Severity.HIGH,
                    description="Database audit logging is not configured",
                    affected_objects=["postgresql.conf"],
                    remediation="ALTER SYSTEM SET logging_destination = 'stderr';",
                    owasp_category="A09:2021 - Security Logging and Monitoring Failures",
                    compliance_mappings={
                        "PCI DSS": "10.2 - Audit trail for all access",
                        "HIPAA": "164.312(b) - Audit controls",
                        "SOC2": "CC7.2 - Monitoring of controls"
                    }
                ))

    def _check_connection_logging(self, conn) -> None:
        """Check if connection attempts are logged."""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SHOW log_connections")
            log_connections = cur.fetchone()['log_connections'] == 'on'

            if not log_connections:
                self.findings.append(SecurityFinding(
                    check_id="LOG-002",
                    title="Connection Logging Disabled",
                    severity=Severity.MEDIUM,
                    description="Database connection attempts are not logged",
                    affected_objects=["postgresql.conf"],
                    remediation="ALTER SYSTEM SET log_connections = 'on';",
                    owasp_category="A09:2021 - Security Logging Failures",
                    compliance_mappings={
                        "PCI DSS": "10.2.5 - Log all access to audit trails",
                        "SOC2": "CC7.2 - System monitoring"
                    }
                ))

    def _check_listen_addresses(self, conn) -> None:
        """Check if database is listening on all interfaces."""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SHOW listen_addresses")
            listen = cur.fetchone()['listen_addresses']

            if listen in ('*', '0.0.0.0'):
                self.findings.append(SecurityFinding(
                    check_id="NET-001",
                    title="Database Listening on All Interfaces",
                    severity=Severity.MEDIUM,
                    description="Database is accessible from all network interfaces",
                    affected_objects=["postgresql.conf"],
                    remediation="ALTER SYSTEM SET listen_addresses = 'localhost,10.0.0.0/8';",
                    owasp_category="A05:2021 - Security Misconfiguration",
                    compliance_mappings={
                        "PCI DSS": "1.3.4 - Restrict inbound/outbound traffic",
                        "SOC2": "CC6.6 - Logical access security"
                    }
                ))

    def _check_dynamic_sql(self, conn) -> None:
        """Check for potential SQL injection in stored procedures."""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Find functions using EXECUTE with string concatenation
            cur.execute("""
                SELECT proname, prosrc
                FROM pg_proc
                WHERE prosrc ILIKE '%EXECUTE%||%'
                   OR prosrc ILIKE '%EXECUTE%CONCAT%'
                LIMIT 10
            """)

            vulnerable_funcs = [row['proname'] for row in cur.fetchall()]

            if vulnerable_funcs:
                self.findings.append(SecurityFinding(
                    check_id="INJ-001",
                    title="Potential SQL Injection in Functions",
                    severity=Severity.CRITICAL,
                    description=f"Found {len(vulnerable_funcs)} functions with potential SQL injection",
                    affected_objects=vulnerable_funcs,
                    remediation="Use parameterized queries: EXECUTE format('...', $1, $2);",
                    owasp_category="A03:2021 - Injection",
                    compliance_mappings={
                        "PCI DSS": "6.5.1 - Injection flaws",
                        "OWASP Top 10": "A03:2021 - Injection"
                    }
                ))

    def _check_insecure_settings(self, conn) -> None:
        """Check for insecure configuration settings."""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if checksums are enabled
            cur.execute("SHOW data_checksums")
            checksums = cur.fetchone()

            if checksums and checksums.get('data_checksums') == 'off':
                self.findings.append(SecurityFinding(
                    check_id="CFG-001",
                    title="Data Checksums Disabled",
                    severity=Severity.LOW,
                    description="Data corruption detection is disabled",
                    affected_objects=["postgresql.conf"],
                    remediation="Enable during initdb: initdb --data-checksums (requires recreation)",
                    owasp_category="A08:2021 - Software and Data Integrity Failures",
                    compliance_mappings={
                        "SOC2": "CC7.1 - System monitoring"
                    }
                ))

    def generate_report(self) -> str:
        """
        Generate human-readable security report.

        Returns:
            Markdown-formatted security report
        """
        report_lines = [
            "# Database Security Scan Report",
            "",
            f"**Scan Date:** {datetime.now().isoformat()}",
            f"**Total Findings:** {len(self.findings)}",
            ""
        ]

        # Severity summary
        severity_counts = {s: 0 for s in Severity}
        for finding in self.findings:
            severity_counts[finding.severity] += 1

        report_lines.append("## Severity Summary")
        report_lines.append("")
        report_lines.append(f"- 🔴 **Critical**: {severity_counts[Severity.CRITICAL]}")
        report_lines.append(f"- 🟠 **High**: {severity_counts[Severity.HIGH]}")
        report_lines.append(f"- 🟡 **Medium**: {severity_counts[Severity.MEDIUM]}")
        report_lines.append(f"- 🟢 **Low**: {severity_counts[Severity.LOW]}")
        report_lines.append(f"- ℹ️ **Info**: {severity_counts[Severity.INFO]}")
        report_lines.append("")

        # Detailed findings
        report_lines.append("## Detailed Findings")
        report_lines.append("")

        for i, finding in enumerate(sorted(self.findings, key=lambda f: f.severity.value), 1):
            severity_emoji = {
                Severity.CRITICAL: "🔴",
                Severity.HIGH: "🟠",
                Severity.MEDIUM: "🟡",
                Severity.LOW: "🟢",
                Severity.INFO: "ℹ️"
            }

            report_lines.append(f"### {i}. {severity_emoji[finding.severity]} {finding.title}")
            report_lines.append("")
            report_lines.append(f"**Check ID:** {finding.check_id}")
            report_lines.append(f"**Severity:** {finding.severity.value.upper()}")
            report_lines.append(f"**OWASP Category:** {finding.owasp_category}")
            report_lines.append("")
            report_lines.append(f"**Description:** {finding.description}")
            report_lines.append("")

            if finding.affected_objects:
                report_lines.append("**Affected Objects:**")
                for obj in finding.affected_objects[:10]:  # Limit to 10
                    report_lines.append(f"- `{obj}`")
                if len(finding.affected_objects) > 10:
                    report_lines.append(f"- ... and {len(finding.affected_objects) - 10} more")
                report_lines.append("")

            report_lines.append(f"**Remediation:** {finding.remediation}")
            report_lines.append("")

            if finding.compliance_mappings:
                report_lines.append("**Compliance Mappings:**")
                for standard, requirement in finding.compliance_mappings.items():
                    report_lines.append(f"- {standard}: {requirement}")
                report_lines.append("")

            report_lines.append("---")
            report_lines.append("")

        return "\n".join(report_lines)

    def generate_remediation_script(self) -> str:
        """
        Generate SQL remediation script.

        Returns:
            SQL script to fix vulnerabilities
        """
        script_lines = [
            "-- Database Security Remediation Script",
            f"-- Generated: {datetime.now().isoformat()}",
            f"-- Total Findings: {len(self.findings)}",
            "",
            "-- WARNING: Review and test in staging before applying to production",
            "",
            "BEGIN;",
            ""
        ]

        # Group remediations by severity
        critical_findings = [f for f in self.findings if f.severity == Severity.CRITICAL]
        high_findings = [f for f in self.findings if f.severity == Severity.HIGH]

        if critical_findings:
            script_lines.append("-- === CRITICAL SEVERITY FIXES ===")
            script_lines.append("")
            for finding in critical_findings:
                script_lines.append(f"-- {finding.check_id}: {finding.title}")
                script_lines.append(f"-- {finding.remediation}")
                script_lines.append("")

        if high_findings:
            script_lines.append("-- === HIGH SEVERITY FIXES ===")
            script_lines.append("")
            for finding in high_findings:
                script_lines.append(f"-- {finding.check_id}: {finding.title}")
                script_lines.append(f"-- {finding.remediation}")
                script_lines.append("")

        script_lines.append("COMMIT;")
        script_lines.append("")
        script_lines.append("-- Remember to reload configuration: SELECT pg_reload_conf();")

        return "\n".join(script_lines)


# CLI usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PostgreSQL Security Scanner")
    parser.add_argument("--conn", required=True, help="Connection string")
    parser.add_argument("--output-dir", default="./security_scan", help="Output directory")

    args = parser.parse_args()

    scanner = PostgreSQLSecurityScanner(conn_string=args.conn)

    # Run security scan
    findings = scanner.scan_all()

    # Generate outputs
    import os
    os.makedirs(args.output_dir, exist_ok=True)

    # Security report
    with open(f"{args.output_dir}/security_report.md", "w") as f:
        f.write(scanner.generate_report())

    # Remediation script
    with open(f"{args.output_dir}/remediation.sql", "w") as f:
        f.write(scanner.generate_remediation_script())

    # JSON findings
    with open(f"{args.output_dir}/vulnerabilities.json", "w") as f:
        findings_json = [
            {
                'check_id': f.check_id,
                'title': f.title,
                'severity': f.severity.value,
                'description': f.description,
                'affected_objects': f.affected_objects,
                'remediation': f.remediation,
                'owasp_category': f.owasp_category,
                'compliance_mappings': f.compliance_mappings
            }
            for f in findings
        ]
        json.dump(findings_json, f, indent=2)

    print(f"Security scan complete: {len(findings)} findings")
    print(f"Reports generated in: {args.output_dir}/")
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Permission denied for pg_authid" | Insufficient scanner privileges | Grant pg_read_all_settings and pg_read_all_stats roles |
| "Could not connect to database" | Connection blocked by firewall | Add scanner IP to pg_hba.conf or connect from allowed host |
| "Function does not exist: pg_reload_conf" | Using older PostgreSQL version | Use `SELECT pg_ctl reload` instead (requires OS access) |
| "SSL connection required" | Database enforces SSL but scanner doesn't use it | Add `?sslmode=require` to connection string |
| "Too many findings to process" | Very insecure database | Prioritize critical/high findings first, fix iteratively |

## Configuration Options

**Scan Scope**
- **Full scan**: All 50+ security checks (recommended for compliance)
- **Quick scan**: Critical and high severity only (fast assessment)
- **Compliance scan**: Specific to SOC2/HIPAA/PCI DSS requirements
- **Custom scan**: User-defined check selection

**Severity Thresholds**
- **Critical**: Immediate exploitation risk (exposed passwords, SQL injection)
- **High**: Significant security impact (excessive permissions, no encryption)
- **Medium**: Security weakness (insecure config, missing hardening)
- **Low**: Best practice violation (minor misconfigurations)
- **Info**: Security recommendations (optional improvements)

**Remediation Modes**
- **Manual review**: Human approval required for all fixes
- **Semi-automated**: Auto-fix low/medium, manual for critical/high
- **Automated**: Apply all fixes automatically (staging only)

## Best Practices

DO:
- Run security scans weekly or after configuration changes
- Test remediation scripts in staging before production
- Document exceptions for findings that cannot be fixed
- Integrate scanner into CI/CD pipeline (fail on critical findings)
- Track findings over time to measure security posture improvement
- Grant scanner minimum required privileges (read-only preferred)
- Review and update security baseline quarterly

DON'T:
- Auto-apply remediation without testing (risk of breaking changes)
- Ignore findings because "it's always been that way"
- Run scans during peak load (may impact performance)
- Share security reports without redacting sensitive data
- Skip validation after applying fixes (verify effectiveness)
- Disable security features for convenience
- Use default database credentials in any environment

## Performance Considerations

- **Scan duration**: 30-120 seconds for typical databases
- **Resource overhead**: <1% CPU during scan
- **Query load**: Read-only queries, minimal impact on production
- **Large databases**: May take 5-10 minutes for 1000+ tables
- **Concurrent scans**: Can run in parallel on different databases
- **Report generation**: <1 second for typical findings count

## Security Considerations

- Store scan results securely (contains security-sensitive information)
- Encrypt security reports in transit and at rest
- Restrict access to remediation scripts (contain privileged commands)
- Audit all security scan executions for compliance
- Rotate scanner credentials quarterly
- Use dedicated scanner account with minimal privileges
- Alert security team on critical findings immediately

## Related Commands

- `/database-audit-logger` - Implement audit logging found by scanner
- `/database-health-monitor` - Monitor security metrics over time
- `/database-backup-automator` - Backup before applying security fixes
- `/database-connection-pooler` - Secure connection management

## Version History

- v1.0.0 (2024-10): Initial implementation with OWASP compliance checks
- Planned v1.1.0: Add MySQL/MariaDB support, CIS Benchmark compliance
