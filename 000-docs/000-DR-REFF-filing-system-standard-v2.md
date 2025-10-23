# DOCUMENT FILING SYSTEM STANDARD v2.0

**Purpose:** Universal standard for organizing project documentation with category-based classification

---

## FORMAT SPECIFICATION

### Primary Format
```
NNN-CC-ABCD-short-description.ext
```

**Components:**
- **NNN** = Zero-padded sequence number (001-999) - enforces chronology
- **CC** = Two-letter category code (see Category Table)
- **ABCD** = Four-letter document type abbreviation (see Type Tables)
- **short-description** = 1-4 words, kebab-case, lowercase
- **ext** = File extension (.md, .pdf, .txt, etc.)

### Sub-Tasks Format
When a document has multiple related sub-documents:

**Option A - Letter Suffix:**
```
005-PM-TASK-api-endpoints.md
005a-PM-TASK-auth-endpoints.md
005b-PM-TASK-payment-endpoints.md
```

**Option B - Numeric Suffix:**
```
006-PM-RISK-security-audit.md
006-1-PM-RISK-encryption-review.md
006-2-PM-RISK-access-controls.md
```

---

## CATEGORY CODES (2-LETTER)

| Code | Category | Description |
|------|----------|-------------|
| **PP** | Product & Planning | Requirements, roadmaps, business planning |
| **AT** | Architecture & Technical | Technical decisions, system design |
| **DC** | Development & Code | Code documentation, modules, components |
| **TQ** | Testing & Quality | Test plans, QA, bugs, security audits |
| **OD** | Operations & Deployment | DevOps, deployment, infrastructure |
| **LS** | Logs & Status | Status logs, work logs, progress tracking |
| **RA** | Reports & Analysis | Reports, analytics, research findings |
| **MC** | Meetings & Communication | Meeting notes, memos, presentations |
| **PM** | Project Management | Tasks, sprints, backlogs, risks |
| **DR** | Documentation & Reference | Guides, manuals, references, SOPs |
| **UC** | User & Customer | User docs, onboarding, training, feedback |
| **BL** | Business & Legal | Contracts, compliance, policies, legal |
| **RL** | Research & Learning | Research, experiments, POCs, proposals |
| **AA** | After Action & Review | Post-mortems, retrospectives, lessons |
| **WA** | Workflows & Automation | Workflow docs, n8n, automation, webhooks |
| **DD** | Data & Datasets | Data documentation, CSV, SQL, exports |
| **MS** | Miscellaneous | General, drafts, archives, work-in-progress |

---

## DOCUMENT TYPE ABBREVIATIONS (4-LETTER)

### PP - Product & Planning
| Code | Full Name | Usage |
|------|-----------|-------|
| **PROD** | Product Requirements Document | Core product requirements |
| **PLAN** | Plan/Planning Document | Strategic plans, project plans |
| **RMAP** | Roadmap | Product or project roadmaps |
| **BREQ** | Business Requirements Document | Business-level requirements |
| **FREQ** | Functional Requirements Document | Functional specifications |
| **SOWK** | Statement of Work | Project scope and deliverables |
| **KPIS** | Key Performance Indicators | Success metrics definition |
| **OKRS** | Objectives and Key Results | Goal-setting framework |

### AT - Architecture & Technical
| Code | Full Name | Usage |
|------|-----------|-------|
| **ADEC** | Architecture Decision Record | Technical decision documentation |
| **ARCH** | Technical Architecture Document | System architecture specs |
| **DSGN** | Design Document/Specification | Detailed design specs |
| **APIS** | API Documentation | API specifications |
| **SDKS** | SDK Documentation | Software development kit docs |
| **INTG** | Integration Documentation | Integration guides and specs |
| **DIAG** | Diagram/Visual Documentation | Architecture diagrams |

### DC - Development & Code
| Code | Full Name | Usage |
|------|-----------|-------|
| **DEVN** | Development Notes | Developer notes and annotations |
| **CODE** | Code Documentation | Code-level documentation |
| **LIBR** | Library Documentation | Library usage and APIs |
| **MODL** | Module Documentation | Module specifications |
| **COMP** | Component Documentation | Component specs and usage |
| **UTIL** | Helper/Utility Documentation | Utility function documentation |

### TQ - Testing & Quality
| Code | Full Name | Usage |
|------|-----------|-------|
| **TEST** | Test Plan/Strategy | Overall testing strategy |
| **CASE** | Test Case Documentation | Specific test cases |
| **QAPL** | Quality Assurance Plan | QA strategy and process |
| **BUGR** | Bug Report/Analysis | Bug documentation |
| **PERF** | Performance Testing | Performance test results |
| **SECU** | Security Audit/Testing | Security assessments |
| **PENT** | Penetration Test Results | Pentest findings |

### OD - Operations & Deployment
| Code | Full Name | Usage |
|------|-----------|-------|
| **OPNS** | Operations Documentation | Operational procedures |
| **DEPL** | Deployment Guide/Log | Deployment instructions |
| **INFR** | Infrastructure Documentation | Infrastructure specs |
| **CONF** | Configuration Documentation | Config file documentation |
| **ENVR** | Environment Setup | Environment configuration |
| **RELS** | Release Notes | Version release notes |
| **CHNG** | Change Log/Management | Change documentation |
| **INCD** | Incident Report | Incident documentation |
| **POST** | Post-Mortem/Incident Analysis | Incident analysis |
| **CHKL** | Checklist | Process checklists |

### LS - Logs & Status
| Code | Full Name | Usage |
|------|-----------|-------|
| **LOGS** | Status Log/Journal | General status logging |
| **WORK** | Work Log/Session Notes | Daily work logs |
| **PROG** | Progress Report | Progress documentation |
| **STAT** | Status Report/Update | Status updates |
| **CHKP** | Checkpoint/Milestone Log | Milestone tracking |
| **SUMM** | Summary/Executive Summary | High-level summaries |

### RA - Reports & Analysis
| Code | Full Name | Usage |
|------|-----------|-------|
| **REPT** | General Report | Standard reports |
| **ANLY** | Analysis/Research Report | Analytical findings |
| **AUDT** | Audit Report | Audit results |
| **REVW** | Review Document | Review findings |
| **RCAS** | Root Cause Analysis | Problem analysis |
| **DATA** | Data Analysis | Data analysis reports |
| **METR** | Metrics Report | Metrics and KPIs |
| **BNCH** | Benchmark Results | Performance benchmarks |
| **INDX** | Index/Table of Contents | Index files |

### MC - Meetings & Communication
| Code | Full Name | Usage |
|------|-----------|-------|
| **MEET** | Meeting Notes/Minutes | Meeting documentation |
| **AGND** | Agenda | Meeting agendas |
| **ACTN** | Action Items | Action item tracking |
| **SUMM** | Summary/Executive Summary | High-level summaries |
| **MEMO** | Memo/Communication | Internal memos |
| **PRES** | Presentation | Presentation materials |
| **WKSP** | Workshop Notes | Workshop documentation |

### PM - Project Management
| Code | Full Name | Usage |
|------|-----------|-------|
| **TASK** | Task Breakdown/List | Task documentation |
| **BKLG** | Backlog | Product/sprint backlog |
| **SPRT** | Sprint Plan/Notes | Sprint planning docs |
| **RETR** | Retrospective | Sprint retrospectives |
| **STND** | Standup Notes | Daily standup logs |
| **RISK** | Risk Register/Assessment | Risk documentation |
| **ISSU** | Issue Tracker/Log | Issue tracking |
| **PLAN** | Plan/Planning Document | Strategic plans, project plans |

### DR - Documentation & Reference
| Code | Full Name | Usage |
|------|-----------|-------|
| **REFF** | Reference Material/Guide | Reference documentation |
| **GUID** | User Guide/Handbook | User guides |
| **MANL** | Manual | Operation manuals |
| **FAQS** | FAQ Document | Frequently asked questions |
| **GLOS** | Glossary | Term definitions |
| **SOPS** | Standard Operating Procedure | Procedural documentation |
| **TMPL** | Template | Document templates |
| **CHKL** | Checklist | Process checklists |

### UC - User & Customer
| Code | Full Name | Usage |
|------|-----------|-------|
| **USER** | User Documentation | End-user documentation |
| **ONBD** | Onboarding Guide | User onboarding materials |
| **TRNG** | Training Materials | Training documentation |
| **FDBK** | Feedback/User Feedback | User feedback logs |
| **SURV** | Survey Results | Survey data and analysis |
| **INTV** | Interview Notes/Transcripts | Interview documentation |
| **PERS** | Persona Documentation | User personas |

### BL - Business & Legal
| Code | Full Name | Usage |
|------|-----------|-------|
| **CNTR** | Contract/Agreement | Legal contracts |
| **NDAS** | Non-Disclosure Agreement | Confidentiality agreements |
| **LICN** | License Documentation | Licensing information |
| **CMPL** | Compliance Documentation | Compliance records |
| **POLI** | Policy Document | Company policies |
| **TERM** | Terms & Conditions | Terms documentation |
| **PRIV** | Privacy Documentation | Privacy policies |

### RL - Research & Learning
| Code | Full Name | Usage |
|------|-----------|-------|
| **RSRC** | Research Notes | Research documentation |
| **LERN** | Learning/Study Notes | Study materials |
| **EXPR** | Experiment/POC Documentation | Proof of concept docs |
| **PROP** | Proposal | Project proposals |
| **WHIT** | Whitepaper | Technical whitepapers |
| **CSES** | Case Study | Case study documentation |

### AA - After Action & Review
| Code | Full Name | Usage |
|------|-----------|-------|
| **AACR** | After Action Report | After-action reviews |
| **LESN** | Lessons Learned | Lessons documentation |
| **PMRT** | Post-Mortem/Incident Review | Incident post-mortems |

### WA - Workflows & Automation
| Code | Full Name | Usage |
|------|-----------|-------|
| **WFLW** | Workflow Documentation | Workflow specs |
| **N8NS** | n8n Workflow Documentation | n8n-specific workflows |
| **AUTO** | Automation Documentation | Automation scripts/docs |
| **HOOK** | Webhook Documentation | Webhook configuration |

### DD - Data & Datasets
| Code | Full Name | Usage |
|------|-----------|-------|
| **DSET** | Data Documentation | Dataset documentation |
| **CSVS** | CSV Dataset Documentation | CSV file documentation |
| **SQLS** | SQL/Database Documentation | Database documentation |
| **EXPT** | Data Export Documentation | Export specifications |

### MS - Miscellaneous
| Code | Full Name | Usage |
|------|-----------|-------|
| **MISC** | Miscellaneous/General | General documents |
| **DRFT** | Draft/Temporary | Draft documents |
| **ARCH** | Archive Notes | Archived materials |
| **OLDV** | Deprecated/Old Version | Deprecated docs |
| **WIPS** | Work in Progress | Work in progress docs |
| **INDX** | Index/Table of Contents | Index files |

---

**Last Updated:** 2025-10-17
**Status:** ✅ Active Standard
**Location:** `/home/jeremy/000-projects/claude-code-plugins/claudes-docs/`
