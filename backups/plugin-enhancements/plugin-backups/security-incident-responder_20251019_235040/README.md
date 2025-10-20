# Security Incident Responder Plugin

Assist with security incident response, investigation, and remediation following established incident response frameworks.

## Features

- **Incident Classification** - Categorize security incidents
- **Response Playbooks** - Guided response procedures
- **Evidence Collection** - Gather forensic data
- **Timeline Construction** - Build incident timeline
- **Remediation Steps** - Guided recovery process
- **Post-Incident Reporting** - Lessons learned documentation

## Installation

```bash
/plugin install security-incident-responder@claude-code-plugins-plus
```

## Usage

```bash
/incident-response
# Or shortcut
/incident
```

## Incident Response Phases

### 1. Preparation
- Incident response plan
- Contact lists
- Tools and access
- Communication templates

### 2. Detection & Analysis
- Alert triage
- Incident classification
- Severity assessment
- Initial containment

### 3. Containment
- Short-term containment
- System backup
- Long-term containment
- Evidence preservation

### 4. Eradication
- Remove malware
- Close vulnerabilities
- Patch systems
- Harden configurations

### 5. Recovery
- Restore systems
- Verify functionality
- Monitor for reinfection
- Return to normal operations

### 6. Post-Incident Activity
- Lessons learned
- Documentation
- Process improvements
- Training updates

## Incident Types

- Data breach
- Ransomware attack
- DDoS attack
- Account compromise
- Malware infection
- Insider threat
- Supply chain attack
- API abuse

## Example Response

```
SECURITY INCIDENT RESPONSE
==========================
Incident ID: INC-2025-10-11-001
Date: 2025-10-11 14:30 UTC
Severity: HIGH
Type: Data Breach - SQL Injection

INITIAL ASSESSMENT
------------------
Detection Method: Automated alerting
Affected Systems: Production database
Data at Risk: User credentials (50,000 records)
Attack Vector: SQL injection in login endpoint

IMMEDIATE ACTIONS (0-1 hour)
-----------------------------
 1. Isolate affected system [14:35 UTC]
 2. Block attacker IP addresses [14:40 UTC]
 3. Preserve logs and evidence [14:45 UTC]
 4. Notify security team [14:50 UTC]
□ 5. Deploy WAF rules [In Progress]

CONTAINMENT (1-4 hours)
-----------------------
□ 1. Take database snapshot
□ 2. Patch SQL injection vulnerability
□ 3. Review all database queries
□ 4. Enable query logging
□ 5. Deploy intrusion detection

INVESTIGATION
-------------
Timeline:
- 14:15 UTC: Attacker begins probing
- 14:20 UTC: Successful SQL injection
- 14:25 UTC: Data exfiltration begins
- 14:30 UTC: Automated alert triggers
- 14:35 UTC: Response initiated

Evidence Collected:
- Web server logs
- Database query logs
- Network packet captures
- Application error logs

Attack Details:
POST /api/login
username: admin' UNION SELECT username,password,email FROM users--
Result: Full user table extracted

REMEDIATION STEPS
-----------------
1. Fix SQL injection (IMMEDIATE)
   - Replace with parameterized queries
   - Deploy within 2 hours

2. Force password reset (HIGH)
   - Reset all user passwords
   - Notify users of breach
   - Complete within 24 hours

3. Enable MFA (HIGH)
   - Implement TOTP-based MFA
   - Deploy within 1 week

4. Database encryption (MEDIUM)
   - Enable at-rest encryption
   - Complete within 2 weeks

COMMUNICATION PLAN
------------------
Internal:
- Security team: Immediate notification (Complete)
- Engineering team: Within 1 hour (Complete)
- Management: Within 2 hours (Pending)
- Legal: Within 4 hours (Pending)

External:
- Affected users: Within 72 hours (Required by GDPR)
- Regulatory bodies: Within 72 hours (Required by GDPR)
- Law enforcement: If criminal activity confirmed

POST-INCIDENT ACTIONS
--------------------
□ 1. Document lessons learned
□ 2. Update incident response plan
□ 3. Conduct security training
□ 4. Implement additional controls
□ 5. Schedule follow-up review (30 days)
```

## Response Playbooks

### Data Breach Response
1. Identify scope of breach
2. Contain affected systems
3. Assess data exposure
4. Preserve evidence
5. Notify stakeholders
6. Regulatory reporting
7. Remediation
8. Post-breach monitoring

### Ransomware Response
1. Isolate infected systems
2. Identify ransomware variant
3. Assess backup integrity
4. Evaluate payment vs. recovery
5. Notify authorities
6. Restore from backups
7. Patch vulnerabilities
8. Monitor for reinfection

### DDoS Response
1. Confirm attack type
2. Enable DDoS mitigation
3. Scale infrastructure
4. Block attack sources
5. Notify ISP/CDN
6. Monitor traffic patterns
7. Post-attack analysis

## Best Practices

1. **Have a Plan** - Written incident response procedures
2. **Practice Regularly** - Tabletop exercises and drills
3. **Document Everything** - Detailed logs and evidence
4. **Communicate Clearly** - Keep stakeholders informed
5. **Learn and Improve** - Post-incident reviews

## License

MIT License - See LICENSE file for details
