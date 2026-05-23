## Implementation Guide

1. Identify the target system/service and gather current configuration.
2. Compare settings against baseline hardening guidance.
3. Flag risky defaults, drift, and missing controls with severity.
4. Provide a minimal-change remediation plan and verification steps.

### 1. Configuration Discovery Phase

Locate configuration files to analyze:

- Infrastructure-as-code: Terraform (.tf), CloudFormation (.yaml/.json), Ansible, Kubernetes
- Application configs: application.yml, config.json, web.config, .properties
- Cloud provider configs: AWS, GCP, Azure resource definitions
- Container configs: Dockerfile, docker-compose.yml, Kubernetes manifests
- Web server configs: nginx.conf, httpd.conf, .htaccess

### 2. IaC Misconfiguration Checks

**Cloud Storage**:

- S3 buckets with public read/write access
- Storage accounts without encryption
- Publicly accessible blob containers
- Missing versioning on data stores

**Network Security**:

- Security groups allowing 0.0.0.0/0 on sensitive ports (22, 3389, 3306, 5432)
- Network ACLs with overly permissive rules
- VPCs without flow logs enabled
- Missing network segmentation

**Identity and Access**:

- IAM policies with wildcard (*) permissions
- Service accounts with admin privileges
- Missing MFA enforcement
- Overly broad role assignments
- Hardcoded credentials in code

**Compute Resources**:

- EC2 instances with public IPs unnecessarily
- Unencrypted EBS volumes
- Missing instance metadata service v2
- Outdated AMIs/images

**Database Security**:

- RDS instances publicly accessible
- Databases without encryption at rest
- Missing automated backups
- Weak password policies
- Default ports exposed

### 3. Application Configuration Checks

**Authentication/Authorization**:

- Debug mode enabled in production
- Default credentials present
- Weak session timeout values
- Missing CSRF protection
- Insecure password policies

**API Security**:

- API keys in configuration files
- CORS configured with wildcard (*)
- Missing rate limiting
- Unencrypted API endpoints
- Disabled authentication

**Data Protection**:

- Sensitive data in plain text
- Missing encryption configuration
- Insecure cookie settings (no HttpOnly, Secure flags)
- Logging sensitive information

**Dependencies**:

- Outdated library versions with CVEs
- Unmaintained packages
- Unnecessary dependencies

### 4. System Configuration Checks

**Operating System**:

- Unnecessary services enabled
- Weak SSH configurations
- Missing security updates
- Insecure file permissions
- Disabled firewalls

**Web Servers**:

- Directory listing enabled
- Server tokens exposed
- Missing security headers
- Weak TLS configurations
- Default error pages revealing information

### 5. Severity Classification

Rate findings by severity:

- **Critical**: Immediate exploitation risk (public S3, hardcoded secrets)
- **High**: Significant security impact (weak auth, missing encryption)
- **Medium**: Configuration weaknesses (overly permissive, missing logs)
- **Low**: Best practice violations (information disclosure, outdated configs)

### 6. Generate Findings Report

Document all misconfigurations with:

- Severity and category
- Specific configuration issue
- Security impact explanation
- Remediation steps with code examples
- Compliance implications (CIS, NIST, PCI-DSS)

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
