---
name: firebase-vertex-ai
description: |
  Firebase platform expert with Vertex AI Gemini integration for Authentication, Firestore, Storage, Functions, Hosting, and AI-powered features. Use when asked to "setup firebase", "deploy to firebase", or "integrate vertex ai with firebase". Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Firebase Vertex AI

Operate Firebase projects end-to-end (Auth, Firestore, Functions, Hosting) and integrate Gemini/Vertex AI safely for AI-powered features.

## Overview

Use this skill to design, implement, and deploy Firebase applications that call Vertex AI/Gemini from Cloud Functions (or other GCP services) with secure secrets handling, least-privilege IAM, and production-ready observability.

## Prerequisites

- Node.js runtime and Firebase CLI access for the target project
- A Firebase project (billing enabled for Functions/Vertex AI as needed)
- Vertex AI API enabled and permissions to call Gemini/Vertex AI from your backend
- Secrets managed via env vars or Secret Manager (never in client code)

## Instructions

1. Initialize Firebase (or validate an existing repo): Hosting/Functions/Firestore as required.
2. Implement backend integration:
   - add a Cloud Function/HTTP endpoint that calls Gemini/Vertex AI
   - validate inputs and return structured responses
3. Configure data and security:
   - Firestore rules + indexes
   - Storage rules (if applicable)
   - Auth providers and authorization checks
4. Deploy and verify:
   - deploy Functions/Hosting
   - run smoke tests against deployed endpoints
5. Add ops guardrails:
   - logging/metrics
   - alerting for error spikes
   - basic cost controls (budgets/quotas) where appropriate

## Output

- A deployable Firebase project structure (configs + Functions/Hosting as needed)
- Secure backend code that calls Gemini/Vertex AI (with secrets handled correctly)
- Firestore/Storage rules and index guidance
- A verification checklist (local + deployed) and CI-ready commands

## Error Handling

- Auth failures: identify the principal and missing permission/role; fix with least privilege.
- Billing/API issues: detect which API or quota is blocking and provide remediation steps.
- Firestore rule/index problems: provide minimal repro queries and rule fixes.
- Vertex AI call failures: surface model/region mismatches and add retries/backoff for transient errors.

## Examples

**Example: Gemini-backed chat API on Firebase**
- Request: “Deploy Hosting + a Function that powers a Gemini chat endpoint.”
- Result: `/api/chat` function, Secret Manager wiring, and smoke tests.

**Example: Firestore-powered RAG**
- Request: “Build a RAG flow that embeds docs and answers with citations.”
- Result: ingestion plan, embedding + index strategy, and evaluation prompts.

## Resources

- Full detailed guide (kept for reference): `{baseDir}/references/SKILL.full.md`
- Firebase docs: https://firebase.google.com/docs
- Cloud Functions for Firebase: https://firebase.google.com/docs/functions
- Vertex AI docs: https://cloud.google.com/vertex-ai/docs
