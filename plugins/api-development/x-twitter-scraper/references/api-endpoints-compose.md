# Xquik REST API Endpoints: Compose

### Compose Tweet

```
POST /compose
```

Compose, refine, and score tweets with Xquik style signals. Three-step workflow.

**Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `step` | string | Yes | `compose`, `refine`, or `score` |
| `topic` | string | No | Tweet topic (compose, refine) |
| `goal` | string | No | `engagement`, `followers`, `authority`, `conversation` |
| `styleUsername` | string | No | Cached style username for voice matching (compose) |
| `tone` | string | No | Desired tone (refine) |
| `additionalContext` | string | No | Extra context or URLs (refine) |
| `callToAction` | string | No | Desired CTA (refine) |
| `mediaType` | string | No | `photo`, `video`, `none` (refine) |
| `draft` | string | No | Tweet text to evaluate (score) |
| `hasLink` | boolean | No | Link attached (score) |
| `hasMedia` | boolean | No | Media attached (score) |

**Response (step=compose):** Returns `contentRules`, `scorerWeights`, `followUpQuestions`, `algorithmInsights`, `engagementMultipliers`, `topPenalties`.

**Response (step=refine):** Returns `compositionGuidance`, `examplePatterns`.

**Response (step=score):** Returns `totalChecks`, `passedCount`, `topSuggestion`, `checklist[]` with `factor`, `passed`, `suggestion`.

---
