---
stepsCompleted: [1]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'Jira Service Management Desk Setup and Configuration'
research_goals: 'Initial setup and configuration best practices, automation rules and workflow design, integration with Atlassian tools and third-party systems, ITSM practices (incident/problem/change management), customer/employee-facing portal design'
user_name: 'Root'
date: '2026-04-13'
web_research_enabled: true
source_verification: true
---

# Research Report: Technical

**Date:** 2026-04-13
**Author:** Root
**Research Type:** Technical

---

## Research Overview

[Research overview and methodology will be appended here]

---

## Technical Research Scope Confirmation

**Research Topic:** Jira Service Management Desk Setup and Configuration
**Research Goals:** Initial setup and configuration best practices, automation rules and workflow design, integration with Atlassian tools and third-party systems, ITSM practices (incident/problem/change management), customer/employee-facing portal design

**Technical Research Scope:**

- Architecture Analysis - design patterns, frameworks, system architecture
- Implementation Approaches - development methodologies, coding patterns
- Technology Stack - languages, frameworks, tools, platforms
- Integration Patterns - APIs, protocols, interoperability
- Performance Considerations - scalability, optimization, patterns

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-04-13

---

## Technology Stack Analysis

### Deployment Architecture: Cloud vs Data Center

Jira Service Management offers two primary deployment models, each with distinct architectural implications:

**Cloud (SaaS)** — Atlassian-managed infrastructure with automatic updates, built-in scalability, and native integrations (Opsgenie, Statuspage included). Minimum 3 agent licenses. Best for teams wanting low operational overhead.
_Key advantage: Native incident management via Opsgenie included in standard license._

**Data Center (Self-Managed)** — Self-hosted on your infrastructure with active-active clustering for high availability. Supports horizontal scaling by adding nodes. Deployable on physical hardware, VMs, Kubernetes (via Helm charts — Atlassian recommended), or public cloud (AWS/Azure). Minimum 50 agent licenses.
_Key advantage: Full infrastructure control, deeper customization, compliance flexibility._

_Source: [Atlassian Cloud vs Data Center Comparison](https://www.atlassian.com/migration/assess/compare-cloud-data-center/jira-service-management)_
_Source: [JSM Data Center Architecture](https://confluence.atlassian.com/spaces/SECURITY/pages/1409093042/Jira+Service+Management+Data+Center+architecture+and+infrastructure+options)_

### Extension & Customization Technologies

**Atlassian Forge (Primary Platform — 2026):**
Forge is now Atlassian's sole development platform for Cloud app extensions. As of September 2025, only Forge apps can be submitted to the Atlassian Marketplace; Connect apps are no longer accepted. Forge apps run in Atlassian's managed infrastructure with sandboxed execution. JSM-specific UI modules include: `queuePage`, `portalRequestDetail`, `portalRequestDetailPanel`, `organizationPanel`, `portalHeader`, `portalFooter`, `portalSubheader`, and `portalProfile`. As of April 2026, Forge usage on up to 5 sandboxes per production site is exempt from billing.
_Languages: JavaScript/TypeScript (Node.js runtime)_

**ScriptRunner (Groovy-based Customization):**
ScriptRunner remains a critical extension tool for both Cloud and Data Center, providing Behaviors (dynamic field modification), Listeners (event-driven automation), Validators/Conditions (workflow logic), and REST endpoint creation. The 2026 release introduced Script Manager for Cloud — manage .groovy scripts directly from the UI without FTP or server admin access.

**REST APIs:**
Full REST API coverage for service desk operations — request types, queues, SLAs, customers, organizations, and approvals. Supports both Jira platform APIs and JSM-specific endpoints.

_Source: [Forge for JSM](https://www.atlassian.com/blog/developer/get-started-with-forge-for-jira-service-management)_
_Source: [Connect vs Forge](https://community.atlassian.com/forums/Jira-articles/Connect-vs-Forge-What-s-Really-Going-On/ba-p/3192390)_
_Source: [ScriptRunner for Jira](https://www.scriptrunnerhq.com/atlassian-apps/jira/scriptrunner-for-jira)_

### Database and Storage Technologies

**Cloud:** Fully managed by Atlassian — no database administration required.

**Data Center:**
- **Supported databases:** PostgreSQL (recommended), MySQL, Oracle, Microsoft SQL Server
- **PostgreSQL best practices:** Create with Unicode collation; for PostgreSQL 15+, create a user-private schema for the Jira DB user; tune `shared_buffers = 512MB` and `wal_buffers = 16MB` for large datasets
- **Clustering support:** PGpool-II supported since Jira 9.10 for PostgreSQL database clustering
- **File storage:** Shared filesystem required for clustered deployments (attachments, avatars, indexes)

_Source: [Supported Platforms](https://confluence.atlassian.com/adminjiraserver/supported-platforms-938846830.html)_
_Source: [PostgreSQL Connection Guide](https://confluence.atlassian.com/adminjiraserver/connecting-jira-applications-to-postgresql-938846851.html)_

### Automation Framework

JSM includes a built-in no-code automation engine with three core components:

- **Triggers:** Event listeners (issue created, field changed, SLA breached, comment added, etc.)
- **Conditions:** Scope narrowing (issue type, priority, status, JQL-based, user conditions)
- **Actions:** Task execution (transition issue, send notification, assign agent, create sub-task, webhook call, update fields)

Advanced capabilities include multi-step approval workflows, SLA-driven escalation chains, cross-project automation with DevOps teams, and scheduled rule execution. Best practice: fix workflows before automating — automation accelerates processes but cannot fix inefficient ones.

_Source: [JSM Automation Guide](https://www.atlassian.com/software/jira/service-management/product-guide/tips-and-tricks/automation)_
_Source: [Automation Templates](https://www.atlassian.com/software/jira/automation-template-library/jira-service-management)_
_Source: [Advanced Automation Rules](https://www.getint.io/blog/advanced-jira-automation-rules)_

### Development Tools and Platforms

- **Forge CLI:** Command-line tooling for building, testing, and deploying Forge apps
- **Atlassian Developer Console:** Web-based app management, environment configuration, and analytics
- **Jira REST API Explorer:** Interactive API documentation and testing
- **ScriptRunner Console:** In-app Groovy scripting environment with built-in REST client
- **Atlassian Marketplace:** App distribution (Forge-only for new apps as of 2025)
- **Jira Cloud Developer Sandbox:** Free development environments for testing

_Source: [Forge Developer Platform](https://developer.atlassian.com/cloud/jira/platform/forge/)_
_Source: [JSM Developer Documentation](https://developer.atlassian.com/cloud/jira/service-desk/)_

### Technology Adoption Trends

- **Cloud migration accelerating:** Atlassian is steering customers toward Cloud with feature parity improvements and Data Center price increases. Cloud now includes native Opsgenie and Statuspage.
- **Forge overtaking Connect:** Connect framework deprecated for new Marketplace submissions. All new extensibility delivered exclusively on Forge.
- **AI and virtual agents:** JSM Cloud increasingly integrating AI-powered features for request classification, auto-responses, and knowledge base suggestions.
- **Kubernetes for Data Center:** Helm chart deployments are now the Atlassian-recommended approach for self-managed installations, replacing traditional VM-based setups.

_Source: [Ultimate JSM Guide 2026](https://clonepartner.com/blog/ultimate-guide-jira-service-management-2026)_
_Source: [JSM Everything You Need to Know 2026](https://softgile.com/en/en-jira-service-management-everything-you-need-to-know-at-2026/)_

---

<!-- Content will be appended sequentially through research workflow steps -->
