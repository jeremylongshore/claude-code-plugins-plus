---
title: "Engine to Product: Three Interfaces, One Codebase"
description: "Building CLI, REST API, and frontend wizard interfaces on top of a comparison engine. The jump from library to usable product in cad-dxf-agent."
date: "2026-02-28"
tags: ["ai-agents", "python", "fastapi", "architecture", "full-stack", "cad"]
featured: false
---
You built the engine. Four layers of deterministic comparison, 1,875 tests, confidence scoring, alignment ladder. Great. Nobody can use it.

A library isn't a product. The comparison engine in [cad-dxf-agent](https://github.com/jeremylongshore/cad-dxf-agent) could compare two DXF files with sub-thousandth precision — but only if you imported it in a Python script, instantiated the right classes, and knew the method signatures. That's fine for me. It's useless for the machinist reviewing revision changes.

This week was about wiring three interfaces onto one engine: a CLI for power users, a REST API for integrations, and a frontend wizard for everyone else. Four PRs, 76 new tests.

## The Problem That Forced Manual Alignment

The automatic alignment ladder (identity → anchor → feature) handles most drawings. But some files have huge coordinate offsets — one sheet drafted at origin, the revision drafted 10,000 inches away — and no shared anchor blocks to triangulate from.

The ladder tries all three strategies and fails gracefully. But "we can't align these" isn't an acceptable answer when the user *knows* which points correspond.

PR #52 added `--control-points` — user supplies 2-3 point pairs, and the system computes the transform directly:

```python
# 1 point pair = pure translation
# 2+ point pairs = Kabsch SVD for full rigid transform (rotation + translation)

def align_with_control_points(
    pairs: list[tuple[Point2D, Point2D]],
) -> AlignmentResult:
    if len(pairs) == 1:
        src, tgt = pairs[0]
        return AlignmentResult(
            translation=tgt - src,
            rotation=np.eye(2),
            confidence=1.0,
            method="manual_translation",
        )

    # 2+ pairs: Kabsch algorithm
    src_pts = np.array([p[0] for p in pairs])
    tgt_pts = np.array([p[1] for p in pairs])
    rotation, translation = kabsch_align(src_pts, tgt_pts)
    residual = compute_rms_residual(src_pts, tgt_pts, rotation, translation)

    return AlignmentResult(
        translation=translation,
        rotation=rotation,
        confidence=max(0, 1.0 - residual),
        method="manual_rigid",
    )
```

Manual path takes priority over the automatic ladder. If you supply control points, the ladder doesn't even run. 10 new tests covering single-point translation, multi-point rigid transform, and degenerate inputs.

## Integration Tests Through the Real User Path

PR #53 filled a gap that was bothering me. The alignment ladder had unit tests for each step in isolation — anchor matching, feature extraction, Kabsch math. But nobody was testing through `ComparisonEngine`, the class users actually call.

7 integration tests covering the real paths:

- Identical pair → identity alignment (no transform needed)
- Offset pair → anchor or feature alignment kicks in
- Rotated pair → rigid transform with rotation matrix
- Manual control points → bypass the ladder entirely
- Impossible alignment → confidence 0.0 with guidance message

The impossible-alignment test matters most. When the system can't align two files, it should say so clearly — not return a garbage transform with 0.12 confidence that silently corrupts downstream matching.

## The API: Six Granular Endpoints

This is where the product lives. PR #54 added the revision pipeline as REST endpoints — not one monolithic `/compare` endpoint, but six steps the client controls:

```
POST /api/revision/upload    — upload revision DXF to existing session
POST /api/revision/align     — run alignment (auto or manual control points)
POST /api/revision/diff      — compare & generate revision ops
POST /api/revision/approve   — approve/reject individual ops by op_id
POST /api/revision/apply     — apply approved ops, export bundle
GET  /api/revision/download  — download bundle as zip
```

Each endpoint advances session state by exactly one step. The client can't call `/diff` before `/align`. Can't call `/apply` before `/approve`. State machine enforced server-side.

The session object grew to track the pipeline:

```python
class SessionState:
    # ... existing fields ...
    revision_path: Path | None
    alignment_result: AlignmentResult | None
    revision_ops: list[RevisionOp] | None
    approval_set: dict[str, Literal["approve", "reject"]]
    apply_result: ApplyResult | None
    bundle_dir: Path | None
```

Why granular endpoints instead of one big POST? Because the user needs to *review* between steps. Upload → align → see the diff → approve some ops, reject others → apply only what's approved → download. Each step is a decision point.

## What Gemini Caught in Review

This is the kind of thing that justifies AI code review. In the approval endpoint, I had:

```python
approval_set: dict[str, Literal["approve", "reject"]]
```

Gemini flagged it: `Literal["approve", "reject"]` as a type hint is fine for static analysis, but FastAPI deserializes request bodies at runtime. A client sending `"approv"` (typo) would pass through without validation because `Literal` isn't enforced at the Pydantic level unless you explicitly configure it.

The fix was adding a Pydantic validator:

```python
class ApprovalRequest(BaseModel):
    op_id: str
    decision: str

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: str) -> str:
        if v not in ("approve", "reject"):
            raise ValueError(f"decision must be 'approve' or 'reject', got '{v}'")
        return v
```

It also caught dead `_control_points` code — a parameter that was being accepted but never passed through to the alignment function. Two real bugs, caught before merge.

## The Frontend: Wizard Step 4

The React frontend wraps these endpoints in a step-by-step wizard. The interesting piece is step 4 — applying approved changes and downloading the bundle.

`api.js` got two new functions:

```javascript
export async function revisionApply(sessionId) {
  return post(`/api/revision/apply`, { session_id: sessionId });
}

export function revisionDownloadUrl(sessionId) {
  return `${API_BASE}/api/revision/download?session_id=${sessionId}`;
}
```

`useSession.js` tracks the new state: `revisionOps`, `revisionApplyResult`, `bundleReady`. The `PreviewPanel` shows an apply button gated on whether any ops have been approved, with badge counts showing approved/rejected/pending.

Nothing fancy. That's the point. The frontend is thin because the API does the work.

## Three Interfaces, One Engine

The CLI (`cad-revision`) has 6 subcommands that mirror the API: `upload`, `align`, `diff`, `approve`, `apply`, `download`. Same session state, same pipeline, same validation.

The REST API exposes that pipeline over HTTP with session management.

The frontend wizard wraps the API in a guided flow.

All three call the same `ComparisonEngine` and `RevisionApplier` underneath. The engine doesn't know or care which interface is driving it. That's the whole architecture: a thick core with thin shells.

## The Numbers

| Metric | Value |
|--------|-------|
| PRs merged | 4 (#52–#54 + frontend) |
| New tests | 76 (10 + 7 + 21 + 38) |
| API endpoints added | 6 |
| CLI subcommands | 6 |
| Gemini review catches | 2 real bugs |

The test count for PR #54 alone — 21 tests including a full end-to-end pipeline integration — is higher than many projects have total. That's what happens when each endpoint has state preconditions that need to be verified.

## Meanwhile: searchcarriers Gets Serious

Parallel track: searchcarriers (freight broker MCP servers) got 80 behavioral integration tests across all 5 handlers — carrier-intel, risk-engine, ops-reporter, watchdog, api-bridge. Uses `respx` to intercept HTTP at the transport layer so tests hit real handler logic without live API calls.

The ops-reporter work exposed a classic integration bug: the real API returns `snake_case` fields, but the handlers expected `camelCase`. A field normalization layer fixes the mismatch at the boundary. Also shipped curated CSV exports (~22 columns instead of the 143-column raw dump) and PDF reports via Jinja2 + WeasyPrint.

45 new tests there, bringing searchcarriers to 197 total.

## The Lesson

Making something usable takes as much engineering as making it work. The comparison engine was four PRs of dense algorithm work. The product layer — CLI, API, frontend, tests, docs — was another four PRs of equal density.

The difference: the engine PRs were fun. The product PRs were discipline. Validation, state management, error messages, approval workflows, bundle packaging, download endpoints. None of it is glamorous. All of it is necessary.

A library that only you can use is a prototype. A product that a machinist can point-and-click through is software.

---

*Related posts:*

- [Building a Deterministic DXF Comparison Engine in One Day](/blog/deterministic-dxf-comparison-engine-one-day-build/) — the engine this post builds on: E1-E4 layers, 1,875 tests
- [The Silent Killer: How Bare catch {} Blocks Hide Failures](/blog/silent-killer-bare-catch-blocks-hide-failures/) — debugging invisible frontend failures in the same codebase
- [Python Class Identity Mismatch: The CI Bug That Broke 9 PRs](/blog/python-class-identity-mismatch-ci-debugging-guide/) — another case where identity semantics caused subtle breakage
