# Firebase Vertex AI: Error Reference

## Firebase CLI Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Error: Failed to authenticate` | Firebase CLI not logged in or token expired | Run `firebase login --reauth` |
| `Error: No project active` | No project selected in `.firebaserc` | Run `firebase use <project-id>` or `firebase use --add` |
| `Error: HTTP Error: 403, The caller does not have permission` | Service account missing IAM roles | Grant `roles/firebase.admin` and `roles/cloudfunctions.developer` to the deploying principal |
| `Error: The default Firebase app does not exist` | `admin.initializeApp()` not called before SDK use | Add `admin.initializeApp()` at top of `index.ts` before any admin SDK calls |
| `Error: Could not find or access firebase.json` | Command run outside project root | `cd` to directory containing `firebase.json` |

## Authentication Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `auth/configuration-not-found` | Auth provider not enabled in Firebase Console | Enable the provider under Authentication > Sign-in method |
| `auth/invalid-custom-token` | Custom token signed with wrong service account or expired | Verify the service account matches the Firebase project; tokens expire after 1 hour |
| `auth/id-token-expired` | Client ID token older than 1 hour | Call `getIdToken(true)` to force refresh on the client |
| `auth/insufficient-permission` | Admin SDK called without proper service account | Set `GOOGLE_APPLICATION_CREDENTIALS` or deploy to a Firebase-managed environment |
| `auth/user-not-found` | UID referenced in custom claims or Firestore does not exist | Verify user exists with `admin.auth().getUser(uid)` before writing claims |
| `UNAUTHENTICATED` (callable function) | Client did not send auth token with callable request | Ensure Firebase Auth is initialized on client and user is signed in before calling |

## Cloud Functions Deployment Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Error: Build failed` | TypeScript compilation errors in `functions/src/` | Run `cd functions && npm run build` locally to see errors |
| `Error: Function failed on loading user code` | Missing dependency or broken import at runtime | Check `functions/package.json` includes all imports; run `npm ci` in `functions/` |
| `Error: Quota exceeded for quota group 'default'` | Too many function deployments in short period | Wait 1-2 minutes; deploy with `--only functions:functionName` to limit scope |
| `Error: Memory limit exceeded` | Function uses more than configured memory (default 256MB) | Increase memory in function options: `{ memory: "512MiB" }` |
| `Error: Function execution took X ms, finished with status: timeout` | Function exceeded timeout (default 60s, max 540s) | Increase timeout: `{ timeoutSeconds: 300 }`; optimize slow operations |
| `Error: Secret "X" was not found` | Secret referenced in `defineSecret()` not created | Run `firebase functions:secrets:set SECRET_NAME` before deploying |
| `Error: Cannot deploy functions with experiments` | Using v2 features not yet GA in your CLI version | Update Firebase CLI: `npm install -g firebase-tools@latest` |

## Vertex AI API Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `PERMISSION_DENIED: Vertex AI API has not been used in project X` | `aiplatform.googleapis.com` API not enabled | Run `gcloud services enable aiplatform.googleapis.com --project=PROJECT_ID` |
| `PERMISSION_DENIED: Missing IAM permission` | Function's service account lacks Vertex AI roles | Grant `roles/aiplatform.user` to the function's runtime service account |
| `NOT_FOUND: Model not found: publishers/google/models/X` | Invalid model name or model not available in region | Verify model name (e.g., `gemini-2.5-flash`); check regional availability |
| `RESOURCE_EXHAUSTED: Quota exceeded` | Vertex AI requests/min or tokens/min quota hit | Implement exponential backoff; request quota increase in GCP Console |
| `INVALID_ARGUMENT: Request payload size exceeds the limit` | Input prompt exceeds model context window | Truncate input; use `gemini-2.5-pro` for larger contexts (1M tokens) |
| `INTERNAL: An internal error has occurred` | Transient Vertex AI service error | Retry with exponential backoff (initial delay 1s, max 3 retries) |
| `DEADLINE_EXCEEDED` | Gemini inference took too long | Use `gemini-2.5-flash` for faster responses; reduce prompt size; increase function timeout |
| `FAILED_PRECONDITION: Billing is not enabled` | GCP project has no billing account | Link a billing account at `console.cloud.google.com/billing` |

## Firestore Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `PERMISSION_DENIED: Missing or insufficient permissions` | Security rules block the operation | Check `firestore.rules`; test with `firebase emulators:exec` |
| `FAILED_PRECONDITION: The query requires an index` | Composite index missing for the query | Click the link in the error message, or add the index to `firestore.indexes.json` and deploy |
| `ALREADY_EXISTS: Document already exists` | Calling `create()` on existing document | Use `set()` with `{ merge: true }` or check existence first |
| `NOT_FOUND: No document to update` | Calling `update()` on non-existent document | Use `set()` instead, or verify document exists before update |
| `ABORTED: Transaction was aborted` | Write contention on the same document | Retry automatically handled by Admin SDK; redesign to reduce contention on hot documents |
| `DEADLINE_EXCEEDED: Deadline exceeded` | Firestore operation took > 60s | Reduce query scope; add indexes; check network connectivity |
| `RESOURCE_EXHAUSTED: Too many writes` | Exceeding 10,000 writes/second per database | Distribute writes across document keys; use batch commits (max 500 ops) |

## Hosting Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Error: Hosting directory "dist" does not exist` | Build output directory missing or wrong name | Run your build command first; verify `hosting.public` in `firebase.json` matches output dir |
| `Error: Function "api" is not a valid rewrite target` | Function referenced in hosting rewrite not deployed | Deploy functions first: `firebase deploy --only functions` then `--only hosting` |
| `HTTP 404 on SPA routes` | Missing catch-all rewrite for client-side routing | Add `{ "source": "**", "destination": "/index.html" }` as last rewrite |

## Billing and Quota Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `BILLING_DISABLED` | Project on Spark (free) plan attempting paid operations | Upgrade to Blaze plan at `console.firebase.google.com` |
| `Cloud Functions requires Blaze plan` | Functions not available on Spark plan | Upgrade to Blaze plan; set budget alerts to avoid surprises |
| Unexpected high bill | Unoptimized Firestore reads or runaway function invocations | Set budget alerts: `gcloud billing budgets create`; review usage in Firebase Console > Usage & billing |
| `Quota exceeded for quota metric 'Generate Content requests'` | Vertex AI free tier or quota limit reached | Request quota increase in IAM & Admin > Quotas; implement client-side rate limiting |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
