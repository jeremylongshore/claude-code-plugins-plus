---
name: responding-to-security-incidents
description: |
  Guide security incident response, investigation, and remediation processes.
  Use when you need to handle security breaches, classify incidents, develop response playbooks, gather forensic evidence, or coordinate remediation efforts.
  Trigger with phrases like "security incident response", "ransomware attack response", "data breach investigation", "incident playbook", or "security forensics".
  
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(log-analysis:*, forensics:*, network-trace:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Prerequisites

Before using this skill, ensure:
- Access to system and application logs in {baseDir}/logs/
- Network traffic captures or SIEM data available
- Incident response team contact information
- Backup systems operational and accessible
- Write permissions for incident documentation in {baseDir}/incidents/
- Communication channels established for stakeholder updates

## Instructions

### 1. Incident Detection and Triage

Classify the security incident:
- Incident type (ransomware, data breach, DDoS, insider threat, phishing)
- Severity level (Critical, High, Medium, Low)
- Scope assessment (affected systems, data, users)
- Initial timestamp and detection method
- Potential business impact

### 2. Immediate Containment Actions

Prevent further damage:
- Isolate affected systems from network
- Disable compromised user accounts
- Block malicious IP addresses at firewall
- Preserve system state for forensics
- Activate incident response team
- Document all containment actions with timestamps

### 3. Evidence Collection Phase

Gather forensic data systematically:

**System Evidence**:
- Memory dumps from affected systems
- Disk images for forensic analysis
- Running process listings
- Network connection states
- Registry modifications (Windows)

**Log Evidence**:
- Authentication logs (successful/failed logins)
- Application logs with error patterns
- Network traffic logs (firewall, IDS/IPS)
- Database access logs
- Web server access/error logs

**Network Evidence**:
- Packet captures (PCAP files)
- DNS query logs
- Proxy server logs
- Network flow data (NetFlow)

### 4. Investigation and Analysis

Reconstruct the attack timeline:
- Identify initial access vector (how attackers got in)
- Map lateral movement within network
- Determine data exfiltration attempts
- Identify persistence mechanisms
- Assess privilege escalation methods
- Document indicators of compromise (IOCs)

### 5. Eradication Phase

Remove threat from environment:
- Remove malware and backdoors
- Close exploited vulnerabilities
- Reset compromised credentials
- Apply security patches
- Update firewall rules
- Verify threat elimination

### 6. Recovery and Restoration

Restore normal operations:
- Restore systems from clean backups
- Rebuild compromised systems from scratch
- Verify system integrity
- Monitor for reinfection attempts
- Gradually restore services
- Validate business operations

### 7. Post-Incident Documentation

Create comprehensive incident report:
- Executive summary
- Detailed timeline
- Root cause analysis
- Lessons learned
- Remediation recommendations
- Cost impact assessment

## Output

The skill produces:

**Primary Output**: Incident response playbook saved to {baseDir}/incidents/incident-YYYYMMDD-HHMM.md

**Playbook Structure**:
```
# Security Incident Response - [Incident Type]


## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.
Date: YYYY-MM-DD HH:MM
Severity: CRITICAL
Status: Contained

## Executive Summary
- Incident type: Ransomware attack
- Detection time: 2024-01-15 08:30 UTC
- Affected systems: 15 servers, 200 workstations
- Business impact: Production halted
- Current status: Contained, recovery in progress

## Timeline of Events
08:30 - Initial detection via EDR alert
08:35 - IT team confirms ransomware encryption
08:40 - Network isolation initiated
09:00 - Incident response team activated
[Detailed timeline continues]

## Containment Actions Taken
✅ Isolated affected network segments
✅ Disabled compromised accounts
✅ Blocked C2 server IPs
✅ Preserved forensic evidence

## Evidence Collected
- Memory dumps: 15 systems
- Log files: {baseDir}/incidents/evidence/logs/
- Network captures: {baseDir}/incidents/evidence/pcaps/
- Malware samples: Quarantined

## IOCs (Indicators of Compromise)
- IP addresses: 203.0.113.45, 198.51.100.78
- File hashes: SHA256 values listed
- Domain names: malicious-c2.example
- Registry keys: HKLM\Software\[malware]

## Remediation Plan
Priority 1 (Immediate):
- Remove ransomware from all systems
- Reset all domain credentials
- Patch vulnerable RDP service

Priority 2 (24 hours):
- Deploy endpoint protection updates
- Implement network segmentation
- Enable MFA for all accounts

Priority 3 (1 week):
- Security awareness training
- Update incident response procedures
- Conduct tabletop exercise

## Recovery Status
- Clean backups identified: 2024-01-14 backup
- Systems rebuilt: 5/15 servers complete
- Services restored: Email, file servers online
- Estimated full recovery: 48 hours

## Communication Log
- 08:45 - Executive team notified
- 09:30 - Legal counsel engaged
- 10:00 - Cyber insurance contacted
- 12:00 - Customer notification prepared
```

**Secondary Outputs**:
- IOC list for threat intelligence sharing (JSON/STIX format)
- Evidence chain of custody log
- Stakeholder communication templates
- Post-incident review agenda

## Error Handling

**Common Issues and Resolutions**:

1. **Incomplete Log Data**
   - Error: "Critical logs missing from {baseDir}/logs/"
   - Resolution: Work with available data, note gaps in report
   - Action: Improve logging for future incidents

2. **Evidence Contamination**
   - Error: "System state modified before evidence collection"
   - Resolution: Document contamination, collect remaining evidence
   - Best Practice: Immediately isolate before investigation

3. **Ongoing Active Threat**
   - Error: "Attacker still has access during investigation"
   - Resolution: Prioritize containment over investigation
   - Action: Implement emergency containment procedures first

4. **Insufficient Access for Forensics**
   - Error: "Permission denied accessing system memory"
   - Resolution: Escalate to obtain necessary privileges
   - Fallback: Use available logs and network data

5. **Backup Corruption**
   - Error: "Backups also encrypted by ransomware"
   - Resolution: Identify offline/air-gapped backups
   - Contingency: Assess rebuild from scratch vs ransom payment

## Resources

**Incident Response Frameworks**:
- NIST Computer Security Incident Handling Guide: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf
- SANS Incident Handler's Handbook: https://www.sans.org/white-papers/33901/
- CISA Incident Response Guide: https://www.cisa.gov/incident-response

**Forensic Tools**:
- Memory analysis: Volatility Framework
- Disk forensics: Autopsy, FTK Imager
- Network analysis: Wireshark, tcpdump
- Log analysis: ELK Stack, Splunk

**Threat Intelligence**:
- MITRE ATT&CK Framework: https://attack.mitre.org/
- AlienVault OTX: https://otx.alienvault.com/
- VirusTotal: https://www.virustotal.com/

**Communication Templates**:
- Breach notification requirements by jurisdiction
- Customer communication guidelines
- Media response templates
- Regulatory reporting formats (GDPR, HIPAA, etc.)

**Playbook Templates**:
- Ransomware response: {baseDir}/templates/playbook-ransomware.md
- Data breach response: {baseDir}/templates/playbook-breach.md
- DDoS response: {baseDir}/templates/playbook-ddos.md

**Legal and Compliance**:
- Chain of custody documentation
- eDiscovery preparation
- Cyber insurance claim procedures
- Law enforcement coordination