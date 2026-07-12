# DAB Deployment Engines — Terraform vs Direct, and the tfstate EOF Trap

A Databricks Asset Bundle (DAB) does not deploy resources by talking to the
workspace directly — by default it drives a **Terraform** engine bundled inside
the `databricks` CLI. That engine keeps a `terraform.tfstate` file, and on
current CLI builds a bug in how the CLI _reads that state back_ bricks a bundle
on the **second** deploy: every redeploy after the first fails with an
`unexpected EOF` on `terraform.tfstate`. The only reliable escape is to stop
using the Terraform engine and switch to the preview **direct** engine via the
environment variable `DATABRICKS_BUNDLE_ENGINE=direct`.

This reference explains what the two engines actually do differently, exactly
why the Terraform engine hits the EOF (open bug `databricks/cli#4986`), how to
migrate a live bundle to the direct engine, and what the "preview" label on the
direct engine means for a production pipeline — because switching engines trades
one class of bug for another, it is not a clean fix.

Read the engine you are on first. If you have never set `DATABRICKS_BUNDLE_ENGINE`
you are on the Terraform engine and exposed to #4986. The direct engine is opt-in
and, as of this writing, still labeled preview.

---

## The two deployment engines

**Terraform engine (the default).** When you run `databricks bundle deploy` with
no engine override, the CLI:

- Translates `databricks.yml` (jobs, pipelines/DLT, model-serving endpoints,
  clusters, and the resource types the bundled provider supports) into a
  Terraform configuration.
- Invokes a **bundled Terraform binary + the `databricks` Terraform provider**
  (both shipped inside the CLI — you do not install Terraform yourself).
- Reads the **prior state** to compute a plan, applies the diff against the
  workspace REST APIs, then writes the new state back.
- Stores that state as a **workspace file** — `terraform.tfstate` living under
  the bundle's workspace root path (a `/Workspace/...`-style path, _not_ an S3
  bucket the way ordinary Terraform remote state would be). Typical size on a
  real bundle is 530–590 KB.

The state read on step three is the failure point (next section).

**Direct engine (`DATABRICKS_BUNDLE_ENGINE=direct`).** The direct engine removes
Terraform from the loop entirely:

- No bundled Terraform binary, no `databricks` Terraform provider, and **no
  `terraform.tfstate`** blob to download.
- The CLI reconciles bundle resources by calling the Databricks REST APIs
  directly and tracking a lighter-weight deployment state of its own.
- Because it never performs a `workspace-files` streaming read of
  `terraform.tfstate`, the #4986 EOF class **cannot fire** on this engine.

Set it as an environment variable for the CLI process:

```bash
# Opt out of the Terraform engine for this deploy (and every deploy in the shell)
export DATABRICKS_BUNDLE_ENGINE=direct
databricks bundle deploy --profile <profile>
```

The default (Terraform) engine is what you get when the variable is unset; there
is no need to set it to a value to "turn Terraform on."

---

## Why the Terraform engine hits the EOF

The break lives in the CLI's **`workspace-files` streaming-read path**, not in
Terraform or in the state file itself.

- **First deploy succeeds** because there is no prior state to read — the CLI
  computes the plan from an empty baseline, applies it, and _writes_
  `terraform.tfstate` at the end. Writing is not affected.
- **Every deploy after the first fails** because the CLI must now _download_ the
  existing `terraform.tfstate` from the workspace to compute the next plan. The
  streaming reader terminates early and the deploy aborts before any resource is
  touched.
- The state file is **not** corrupt: it is valid JSON, and you can pull it down
  intact out-of-band with `databricks workspace export` and parse it by hand. The
  fault is purely in how the CLI streams the read, which is why the "file is
  fine but the CLI won't read it" symptom is so confusing.

Tracked upstream as **`databricks/cli#4986`** — open at time of writing. It has
been reproduced on both macOS and Linux across CLI **v0.288.0 through v0.296.0**,
so it is not OS- or single-version-specific. It effectively bricks the bundle:
the promote-to-prod pipeline can never run a second deploy until the engine is
switched or a fixed CLI ships.

The failure signature to match:

```text
Error: reading terraform.tfstate: opening: unexpected EOF
```

If you see that after a bundle deployed cleanly once, you are looking at #4986 —
not a permissions problem, not a malformed `databricks.yml`, and not real state
corruption. Do not spend a sprint editing the bundle; the bundle is fine.

---

## The direct engine as the workaround

The switch is one environment variable, and teams that hit #4986 in CI adopt it
permanently rather than pinning-and-praying on CLI versions:

```bash
# Full workaround: run the deploy under the direct engine
export DATABRICKS_BUNDLE_ENGINE=direct
databricks bundle validate --profile <profile>   # confirm the bundle parses
databricks bundle deploy   --profile <profile>   # deploys without touching tfstate
```

It works because the direct engine's reconciliation never opens
`terraform.tfstate` — the entire streaming-read code path that #4986 lives in is
gone. But the direct engine carries its **own** open issues: reports of a
**cluster restart on every deploy** and **catalog "always recreate" drift**
(resources the engine believes must be recreated on each run). So this is a
lateral move between two immature code paths, not an upgrade to a stable one —
validate that your specific resource types deploy cleanly under it before you
commit a production pipeline to it.

---

## Engine comparison

| Dimension | Terraform engine (default) | Direct engine (`DATABRICKS_BUNDLE_ENGINE=direct`) |
| --- | --- | --- |
| Maturity / status | GA — the long-standing default deployment path. | **Preview** — opt-in, still stabilizing. _(verify GA status against current release notes)_ |
| How deployment state is stored | `terraform.tfstate` workspace file (530–590 KB typical) under the bundle's workspace root path. | Lighter CLI-native deployment state; **no `terraform.tfstate` blob**. |
| Exposure to #4986 (tfstate EOF) | **Yes** — fails on every deploy after the first via the `workspace-files` streaming read. | **No** — never performs the tfstate streaming read. |
| Resource / feature coverage | Broadest — everything the bundled `databricks` Terraform provider supports (jobs, pipelines/DLT, model serving, clusters, and more). | A **subset**, catching up to the Terraform engine; some resource types may not yet be handled. _(verify the current matrix)_ |
| Known open bugs | #4986 (tfstate EOF); related state-path issues #4933 / #4625 / #5179; UC `bundle bind` gap #4842. | Cluster restart on every deploy; catalog "always recreate" drift. _(verify issue IDs)_ |
| When it is safe | When the CLI version in use is not affected by #4986, or before the second deploy of a fresh bundle. | When your bundle's resource types are all covered by the direct engine and you have test-deployed them. |
| Rollback / escape | Switch to the direct engine, or pin to a CLI build predating the regression. | Unset `DATABRICKS_BUNDLE_ENGINE` (or set it back to the default) to return to the Terraform engine. |

## Migrating an existing bundle to the direct engine

Switching engines mid-life on a bundle that already has Terraform state is the
common case (the bundle deployed once, then bricked). Steps:

1. **Back up the current state first.** Pull the existing `terraform.tfstate` out
   of the workspace before you change anything, so you can return to the
   Terraform engine if the direct engine mishandles a resource:

   ```bash
   # Export the known-good state (path is under the bundle's workspace root)
   databricks workspace export <workspace-state-path>/terraform.tfstate \
     --profile <profile> > terraform.tfstate.backup
   ```

2. **Set the engine for the deploying shell / CI job.** In CI, set it as a job
   environment variable so every step inherits it:

   ```bash
   export DATABRICKS_BUNDLE_ENGINE=direct
   ```

3. **Validate before deploying.** `databricks bundle validate` confirms the
   bundle parses under the new engine and surfaces any resource type the direct
   engine does not yet support:

   ```bash
   databricks bundle validate --profile <profile>
   ```

4. **Deploy and watch for the two known direct-engine symptoms** — an unexpected
   cluster restart, or a resource (catalog especially) that the plan wants to
   recreate every run. If a resource shows "always recreate" drift, that is the
   direct-engine bug, not your config.

5. **Keep the engine setting with the bundle, not in a person's shell.** Put the
   `DATABRICKS_BUNDLE_ENGINE=direct` line in the CI workflow env (and document it
   in the repo) so a local `databricks bundle deploy` from a laptop does not
   silently fall back to the Terraform engine and re-brick on #4986.

There is no state migration to perform — the direct engine builds its own
deployment state on the first run; the old `terraform.tfstate` is simply left
unused (keep the backup until you are confident you will not revert).

## The preview-feature caveat

The direct engine is officially a **preview** feature, and preview at Databricks
means exactly what it says for a production pipeline:

- **No stability or backward-compatibility guarantee.** The engine's behavior,
  its state format, and the `DATABRICKS_BUNDLE_ENGINE` surface itself can change
  between CLI releases without the deprecation cadence a GA feature gets.
- **Thinner support posture.** Preview features are typically excluded from the
  same support-SLA and may not be covered for every cloud or workspace tier —
  confirm before you route a revenue-bearing deploy through it. _(verify support
  terms for your contract)_
- **Its own live bugs.** The cluster-restart-on-deploy and catalog-recreate-drift
  issues are open against the direct engine right now; you are accepting those in
  exchange for escaping #4986.

**What to re-check when the direct engine GAs (or when #4986 is fixed):**

- Re-read the release notes for the CLI version that closes **#4986**. If the
  Terraform-engine streaming read is fixed, the forcing reason to be on the
  direct engine is gone — decide deliberately whether to stay or revert.
- Confirm the direct engine's **resource-coverage matrix** now includes every
  type your bundle uses; a GA announcement is the point to verify parity with the
  Terraform engine rather than assume it.
- Re-test the **cluster-restart** and **catalog "always recreate"** behaviors —
  if GA closed them, they stop being a reason to hesitate; if it did not, weigh
  them against a fixed Terraform engine.
- Recheck whether `DATABRICKS_BUNDLE_ENGINE=direct` is still the activation
  mechanism, or whether GA changed the default engine so the variable becomes a
  no-op / is renamed.

Until then: the direct engine is a workaround you adopt with eyes open, keep the
tfstate backup, and keep the engine choice version-controlled with the bundle.

## Version-accuracy anchors

Pin these; they are the details a reviewer uses to tell a plan written from the
issue tracker apart from one written from memory:

- **The bug is `databricks/cli#4986`**, open at time of writing, in the CLI's
  `workspace-files` streaming-read path for `terraform.tfstate`. Reproduced on
  macOS and Linux, **CLI v0.288.0 through v0.296.0**. Confirm it is still open and
  whether a later CLI closes it — _(verify against the issue and current release
  notes)_.
- **The exact error string** is `Error: reading terraform.tfstate: opening:
  unexpected EOF`. The wording of CLI error text can shift release to release —
  _(verify the exact spelling against your CLI version)_.
- **The engine variable is `DATABRICKS_BUNDLE_ENGINE`, value `direct`.** The
  default (Terraform) engine is the unset state. Whether an in-`databricks.yml`
  or `--engine`-flag equivalent exists is version-dependent — _(verify; this doc
  only relies on the environment variable, which is the documented surface)_.
- **The direct engine is preview**, not GA — its GA status, resource-coverage
  matrix, and support terms are the moving targets to re-check — _(verify against
  current release notes)_.
- **The state blob is a workspace file**, ~530–590 KB on a real bundle, stored
  under the bundle's workspace root path — not S3-backed remote state. The exact
  in-workspace path segment is version-dependent — _(verify)_.
- **Related open issues** cited alongside #4986: **#4933**, **#4625**, **#5179**
  (other terraform/state-path breakage) and **#4842** (UC `bundle bind` gap).
  Issue numbers and states drift as they close — _(verify current state)_.

Anything below this granularity (exact patch-release fix version, per-cloud
availability of the direct engine) changes fast — _(verify against the release
notes for your exact CLI version and cloud)_.

## Sources

- Databricks CLI — issue **#4986**, `reading terraform.tfstate: opening:
  unexpected EOF` on redeploy, `workspace-files` streaming-read path,
  github.com/databricks/cli/issues/4986.
- Databricks CLI — related state-path issues **#4933**, **#4625**, **#5179**,
  github.com/databricks/cli/issues/{4933,4625,5179}.
- Databricks CLI — issue **#4842**, `bundle bind` does not support UC resources
  (catalogs, external locations), github.com/databricks/cli/issues/4842.
- Databricks Community — _Databricks Asset Bundles: no deployment state_,
  community.databricks.com `/t5/data-engineering/.../td-p/67918`.
- Databricks — _Databricks CLI bundle commands_ (`bundle deploy`, `bundle
  validate`, `bundle destroy`), docs.databricks.com
  `/dev-tools/cli/bundle-commands`.
- Databricks — _Databricks Asset Bundle resources_ (resource types the bundle
  supports), docs.databricks.com `/dev-tools/bundles/resources`.
- Pain catalog D5 (this pack) — `000-docs/004-RL-RSRC-databricks-uc-bundles-ops-research.md`
  § "D5 — Asset Bundle: `terraform.tfstate` unexpected EOF on every deploy after
  the first", for the reproduced symptom, CLI version range, and workaround.
