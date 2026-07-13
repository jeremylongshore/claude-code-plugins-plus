# OneNote Production Checklist — One-Pager

## The Problem

OneNote integrations that work in development break in production in four predictable ways: (1) SharePoint document libraries exceed the 5,000-item view threshold and silently return incomplete notebook lists, (2) image uploads fail above 4MB with no error — content just disappears, (3) rate limits compound across users during business hours (a 200-user org hits the 10K/10min tenant limit with default polling), and (4) MSAL token caches lose state across container restarts, logging out all users simultaneously. Developers never encounter these failures in testing because they use a single user, small data sets, and long-lived dev environments.

## The Solution

This skill provides a 30+ item production readiness checklist organized into eight categories: authentication resilience, rate limit handling, error code coverage, content validation, SharePoint-specific limits, monitoring, health check endpoints, and a go/no-go decision matrix. Each item includes the specific failure mode it prevents and how to verify it. The checklist distinguishes "must-have" items that block launch from "should-have" items that can ship with a plan.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | DevOps engineers, integration leads, and engineering managers conducting launch reviews |
| **What** | 30+ production readiness checks across auth, rate limits, errors, content, SharePoint, and monitoring |
| **When** | Before production deployment, during launch reviews, after scaling events, and quarterly audits |
| **Where** | CI/CD pipeline validation, staging environment testing, production monitoring dashboards |
| **Why** | Single-user dev testing never reveals multi-user rate limits, SharePoint 5K-item thresholds, container restart token loss, or silent HTML truncation |

## Key Differentiators

- Organized by failure category, not by API feature — maps directly to production incidents
- Go/no-go matrix separates launch-blocking items from post-launch tasks
- Includes runnable verification scripts (bash pre-launch check, Python auth resilience test)
- Health check endpoint implementation with three-state status (healthy/degraded/unhealthy)

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated only) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity |
| Monitoring | Custom health check + request-id logging |
| Validation | XHTML validator + size checks pre-send |
