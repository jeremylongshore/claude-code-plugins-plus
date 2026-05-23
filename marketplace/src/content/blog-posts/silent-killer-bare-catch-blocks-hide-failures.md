---
title: "The Silent Killer in Your Web App: How Bare catch {} Blocks Hide Failures from Everyone"
description: "A real-world case study from a live AI-powered CAD DXF editor: how two bare catch {} blocks swallowed every render failure silently, leaving users staring at a placeholder forever — and the full fix, PR review, and deployment cycle to surface the truth."
date: "2026-02-25"
tags: ["debugging", "javascript", "python", "fastapi", "react", "web-development", "cad", "ai", "error-handling"]
featured: false
---
There's a category of bug that I find genuinely maddening: the kind where the system *works* — no exceptions thrown, no 500 errors logged, CI is green — but the user never sees the output they're supposed to see.

This is the story of exactly that bug in [cad-dxf-agent](https://github.com/jeremylongshore/cad-dxf-agent), a local-first AI-powered DXF editor I've been building. After applying an AI-planned edit, users would see **"Run an edit to see the result"** — the placeholder. Forever. Even though the backend rendered the preview successfully.

The root cause? Two `catch {}` blocks. Empty. Silent. Swallowing every error without a single log line.

## The Setup: What the App Does

cad-dxf-agent lets you upload an existing 2D engineering DXF drawing, describe changes in plain English, and get back a validated edited copy. The LLM never touches raw DXF — it returns structured JSON operations that a deterministic engine applies. The whole pipeline:

```
Upload DXF → Load → Summarize → Plan (LLM) → Validate → Apply → Save-As + Render PNG
```

The web version runs on Firebase Hosting (React + Vite) + Cloud Run (FastAPI). After you apply changes, the frontend fetches a PNG render from `/api/render` and displays it. If the fetch fails for *any* reason — auth token timing, CORS, 404, network hiccup — you should know about it. Instead, we had this in `useSession.js`:

```javascript
try {
  const blob = await getRenderBlob(sessionId, 'edited');
  const url = URL.createObjectURL(blob);
  setPreviewUrls((prev) => ({ ...prev, edited: url }));
} catch {
  // Edited render not available — that's ok
}
```

That comment. *That's ok.* It's not ok. It's a lie we told ourselves during rapid development that survived into production.

## The Investigation

Cloud Run logs confirmed the backend was succeeding — 200 OK on every render request. So the failure was entirely frontend-side. Opening devtools, there was nothing. No errors, no warnings, no network failures visible because the bare `catch {}` ate everything before it could surface.

The same pattern existed for the original preview rendered after upload:

```javascript
} catch {
  // Render not available yet — that's ok
}
```

Two silent black holes. Any of these failure modes would vanish completely:

- Firebase auth token not yet valid (race condition on initial load)
- CORS header missing from a Cloud Run response
- `/api/render` returning 404 because the session expired
- Network timeout
- `getRenderBlob()` throwing on a non-2xx response

The backend side had its own diagnostic gap. When the renderer returned `success=False`, we logged the exception message but threw away `render_result.error` (the specific failure detail from the renderer). And we had no `exc_info=True`, so Cloud Run logs had no stack traces:

```python
except Exception as e:
    logger.warning("Edited render failed (non-fatal): %s", e)
    # render_result.error? Gone. Stack trace? Gone.
```

## The Fix: Surface Everything

The plan was straightforward — three targeted changes, nothing more.

### 1. Frontend: Named catches with console.warn

For the upload preview (non-critical — render may lag behind upload):

```javascript
} catch (renderErr) {
    console.warn('[cad] Original render fetch failed:', renderErr.message);
}
```

For the post-apply preview (critical — user just applied changes and expects to see them):

```javascript
} catch (renderErr) {
    console.warn('[cad] Edited render fetch failed:', renderErr.message);
    setMessages((prev) => [...prev, {
        role: 'system',
        text: 'Preview not available — download the edited DXF to view.',
    }]);
}
```

The `[cad]` prefix makes it instantly greppable in devtools. The user-facing message gives them a path forward instead of a frozen UI.

### 2. Backend: Log the render result error + stack traces

```python
if render_result.success:
    session.edited_render = render_result.output_path
else:
    logger.warning("Edited render returned failure: %s", render_result.error)
    session.edited_render = None  # critical, explained below
except Exception as e:
    logger.warning("Edited render failed (non-fatal): %s", e, exc_info=True)
    session.edited_render = None
```

The `exc_info=True` gives full stack traces in Cloud Run's structured logging — previously we had a message but no traceback to find the source.

### 3. Backend: Return render_available in the apply response

```python
render_available = session.edited_render is not None and session.edited_render.exists()
return {
    "message": f"Applied {success_count}/{len(results)} operations.",
    "render_available": render_available,
    ...
}
```

The frontend now has a signal to distinguish "render succeeded but fetch failed" from "render never happened."

## The Stale State Bug (Caught in PR Review)

After pushing the PR, Gemini Code Assist flagged a high-priority issue I'd missed:

> *There's a potential issue where a stale `edited_render` path from a previous successful `apply` call could persist if the current render fails. This would cause `render_available` to be `True` incorrectly.*

This was a real bug. The flow:

1. User applies edit A → render succeeds → `session.edited_render = /path/to/edited.png`
2. User applies edit B → render fails → `session.edited_render` **still points to edit A's PNG**
3. `render_available` returns `True`, frontend fetches the old image, user sees stale preview

The fix: explicitly null out `session.edited_render` in both failure paths before computing `render_available`. That's why both the `else` branch and the `except` block set `session.edited_render = None`.

This is the kind of catch that makes structured PR review worth it — I had the logic right for the happy path but missed the state mutation on failure.

## The Deployment Journey (And A Wrong Turn)

After merging PR #38, I tried to manually trigger the Cloud Build deployment:

```bash
gcloud builds submit --config web/backend/cloudbuild.yaml .
```

This immediately failed:

```
ERROR: invalid image name "...web-backend:": could not parse reference
```

The `cloudbuild.yaml` uses `$SHORT_SHA` as the image tag — but that variable is only populated by Cloud Build *triggers* (push-based), not manual `gcloud builds submit` calls. I'd need to pass `--substitutions=SHORT_SHA=$(git rev-parse --short HEAD)` manually.

Except — I didn't need to do any of this. The GitHub Actions Deploy Web workflow runs on every push to `main`. The merge had already triggered it. Both backend (Cloud Run via Docker build in GH Actions) and frontend (Firebase Hosting) deployed automatically within ~5 minutes. CI handles it.

The lesson: know your deployment topology before reaching for manual commands. `gh run watch` is your friend.

## By the Numbers

- **Files changed:** 2 (`useSession.js`, `main.py`)
- **Net lines:** +18 / -6
- **Tests:** 75/75 web tests pass before and after
- **PR reviews:** Gemini Code Assist (1 valid high-priority finding, addressed), CodeRabbit (summary only)
- **Deploy time:** ~5 minutes end-to-end (GH Actions handles both frontend and backend)
- **User impact:** Render failures now visible in devtools within milliseconds; fallback message gives user next steps

## What This App Does That Nothing Else Does

While we were here, I did a competitive scan. The AI CAD space is crowded — [Zoo/Zookeeper](https://zoo.dev/text-to-cad), [Adam AI](https://adam.new/), [DraftAid](https://draftaid.io/), CADGPT — but almost all of them generate 3D models from scratch. The specific gap cad-dxf-agent fills:

**Upload an existing 2D engineering DXF → describe changes in plain English → get a validated, edited copy back with the original untouched.**

Nobody else is doing this for 2D DXF. The AEC/construction/engineering market runs on DXF files. The "text-to-3D-from-scratch" trend is well-covered. "Natural language editing of existing 2D drawings" is not.

## The Takeaway

Bare `catch {}` blocks are time bombs. During rapid development they feel harmless — "we'll handle this properly later." But "later" is when you're debugging a production issue where users see a placeholder forever and your logs show nothing.

The fix is usually tiny. Two named catches, a `console.warn`, a `setMessages` call. The hard part is knowing where they are — and the only way to find them is to question every place where you silently swallow an error and call it "non-fatal."

Make failures loud, even when they're non-blocking. Your future self debugging at 11pm will thank you.

---

*Related posts:*

- [Session Cookie Auth, Forgot-Password Timeouts, and Killing Flaky E2E Tests](/posts/session-cookies-forgot-password-flaky-e2e-tests/) — another deep-dive into Firebase auth edge cases and debugging invisible failures
- [Waygate MCP v2.1.0: From Forensic Analysis to Production Enterprise Server](/posts/waygate-mcp-v2-1-0-forensic-analysis-to-production-enterprise-server-with-taskwarrior/) — systematic resolution of 19 critical issues through forensic analysis
