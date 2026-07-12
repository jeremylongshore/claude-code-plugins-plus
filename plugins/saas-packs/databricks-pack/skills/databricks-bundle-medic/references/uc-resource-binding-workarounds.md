# Bringing existing UC catalogs and external locations under Asset-Bundle management

`databricks bundle bind` is the command that lets a Databricks Asset Bundle (DAB)
_adopt_ a resource that already exists in the workspace instead of trying to
create a second copy of it. You declare the resource in `databricks.yml`, run
bind against the live resource's ID, and from then on the bundle's deploy loop
treats that object as bundle-managed. That adoption path exists for the resource
types DAB reached first — jobs and pipelines — but **not** for the two Unity
Catalog control-plane objects most governance teams most want under GitOps:
**catalogs and external locations**. A team that already has UC catalogs and
external locations (built by Terraform, the UI, or an earlier script) therefore
cannot cleanly pull them under DAB. This reference explains the gap, ranks the
three real workarounds by how much they can hurt you, and states the lifecycle
rule: every workaround here is scaffolding around an upstream bug
([databricks/cli#4842](https://github.com/databricks/cli/issues/4842)) and comes
out the moment that bug ships a fix.

## Why `bundle bind` exists

A DAB deploy is declarative: the bundle owns a set of resources and reconciles
the workspace to match. The problem is _brownfield_ adoption. If a catalog named
`analytics_prod` already exists and you add a matching resource block to
`databricks.yml`, deploy does not silently take it over — DAB has no record that
the bundle owns it, so it attempts to **create** `analytics_prod`, the name is
already taken, and the deploy fails on a conflict. `bundle bind` is the sanctioned
escape hatch: it writes the linkage between the bundle resource key and the
existing workspace resource ID into the bundle's deployment state, so the next
deploy _updates_ the resource in place rather than creating a duplicate. It is the
DAB-native equivalent of `terraform import`, and under the hood on the default
engine it _is_ a Terraform import against the bundle's managed state.

The command is the `deployment bind` subcommand _(verify: the exact
sub-path — some CLI versions and docs surface it as the shorthand
`databricks bundle bind`; #4842 and community threads use the shorthand)_:

```bash
databricks bundle deployment bind <resource-key> <existing-resource-id> \
  --target <target> --profile <profile>
# undo the linkage (does NOT delete the workspace resource):
databricks bundle deployment unbind <resource-key> --target <target>
```

`<resource-key>` is the key under `resources.<type>.<key>` in `databricks.yml`;
`<existing-resource-id>` is the live object's identifier (a numeric job ID, a
pipeline UUID, and — where supported — the resource's name).

## What `bundle bind` supports today vs the UC gap

Bind was scoped to **jobs and pipelines at GA** and has widened since; the exact
set of bindable resource types drifts release to release, so treat any specific
list as version-bound _(verify against your `databricks --version` and the CLI
changelog)_. The load-bearing fact for this skill is the negative one, and it is
stable as of CLI ~v0.295.x: **catalogs and external locations are not bindable.**

- Attempting the bind returns a rejection to the effect of _"does not recognise
  `external_location` (or `catalog`) as a supported resource type"_ _(verify:
  representative wording — the literal string drifts across CLI versions; do not
  match on it in a script)_.
- Whether DAB even accepts a top-level `resources.catalogs` /
  `resources.external_locations` block at all is itself version-dependent
  _(verify)_; where it does, declaring the block and deploying triggers the
  create-conflict described above, because there is no bind to adopt the
  pre-existing object.
- The gap is tracked upstream in
  [databricks/cli#4842](https://github.com/databricks/cli/issues/4842), open with
  no shipped fix as of CLI ~v0.295.x _(verify the version and issue state — see
  "Checking whether the upstream bug has closed")_.

This is immature tooling, not a design stance: UC resource binding was deferred,
not refused. That is exactly why the workarounds below are written to be thrown
away.

## The three workarounds, ranked by risk

### 1. Import-based script — least-bad (`scripts/import-uc-resource-to-bundle.py`)

This skill ships `scripts/import-uc-resource-to-bundle.py` precisely so nobody
has to hand-roll the next two options. It uses the **sanctioned** Terraform
`import` mechanism against the Terraform config DAB generates under the hood,
rather than editing state by hand. On the default (Terraform) engine, a DAB deploy
materialises provider config into a generated Terraform working directory and
keeps state remotely in the workspace; the script locates that generated config,
runs an import for the existing UC object, then hands back to `bundle deploy` to
reconcile:

```bash
# what the script automates, conceptually:
terraform import databricks_external_location.<key> <external-location-name>
terraform import databricks_catalog.<key>           <catalog-name>
```

`databricks_external_location` and `databricks_catalog` are the real
terraform-provider-databricks resource types; each imports by its **name** as the
ID. The script wraps this with a **backup-first guardrail** (snapshot the bundle's
remote `terraform.tfstate` before touching it), targets DAB's generated Terraform
directory _(verify the path — DAB's internal layout, e.g.
`.databricks/bundle/<target>/terraform/`, is undocumented and moves between
releases)_, and records which resources it patched so it can deprecate cleanly
when native bind lands. Reversal is real: `terraform state rm
databricks_external_location.<key>` drops the object from state without deleting
the live resource.

- **Why it is still only "least-bad":** it reaches into DAB's private Terraform
  surface, which carries no compatibility promise. It also does **not** apply on
  the `direct` deployment engine (`DATABRICKS_BUNDLE_ENGINE=direct`), which has no
  Terraform state to import into — a team that adopted the direct engine to dodge
  the state-corruption class (see the D5 pain entry) has no Terraform import path
  and is pushed toward option 3.

### 2. Hand-editing `terraform.tfstate` — hostile, do not automate

The rawest option: download the bundle's remote `terraform.tfstate`, hand-author
a `resources[]` entry (correct `type`, `name`, and an `instances[].attributes`
block carrying the object's real `id`), and re-upload it. This is what option 1
does _for_ you through a supported command, minus every guardrail.

- **The state file has no public schema.** You are editing an internal Terraform
  artifact by inference. One wrong field, a stale `serial`/`lineage`, or a
  malformed attributes block and **every future deploy of that bundle fails** —
  not just the bind, the whole pipeline.
- It is undocumented on purpose; Databricks does not describe the state format,
  so there is nothing authoritative to check your edit against.
- Never do this in CI, and never without a byte-exact backup of the prior state.
  Corruption is only reversible if you kept that backup.

### 3. Destroy and recreate — only on empty resources

Delete the existing catalog / external location and let DAB create it fresh from
the declared block:

```bash
databricks bundle destroy --target <target> --profile <profile>
# then declare the resource in databricks.yml and:
databricks bundle deploy --target <target> --profile <profile>
```

- **This is impossible the instant dependent objects exist.** A UC **managed**
  table lives _inside_ its catalog/schema — destroy the catalog and the managed
  tables (and their data) die with it. An **external location** with dependent
  external tables or volumes cannot be dropped until those dependents are removed
  first, and even then you risk orphaning the underlying storage governance.
- It is therefore valid **only** for an empty catalog / external location with
  zero dependent tables, volumes, or schemas — effectively a resource you could
  have created greenfield anyway.
- There is no undo: destroyed data does not come back. Treat any suggestion to
  destroy a populated UC resource to satisfy tooling as an incident, not a fix.

## Workaround comparison

| Workaround | Risk | When valid | Reversible? |
| --- | --- | --- | --- |
| Import-based script (`terraform import` via DAB's generated config) | **Medium** — touches DAB's internal, unsupported Terraform state; breaks on the `direct` engine | Any existing catalog / external location you want adopted, when you can back up state first | **Yes** — `terraform state rm <addr>` + restore the state backup |
| Hand-edit `terraform.tfstate` | **High** — undocumented JSON; one bad field bricks every future deploy of the bundle | Absolute last resort when the import path won't run; never in CI | **Only** if a byte-exact backup exists; corruption is otherwise unrecoverable |
| Destroy + recreate via DAB | **Catastrophic if misapplied** — deletes the resource and, for catalogs, every managed table under it | **Only** an empty catalog / external location with zero dependent tables/volumes/schemas | **No** — destroyed data is gone |

Default order of preference: try option 1, fall back to option 2 only with a
verified state backup and never in automation, and reach for option 3 exclusively
when the resource is provably empty.

## The self-deprecation contract — remove when #4842 closes

Everything in this reference is a **temporary bridge over an upstream bug**, and it
is written to be deleted:

- These workarounds exist **only** until
  [databricks/cli#4842](https://github.com/databricks/cli/issues/4842) ships
  native bind support for catalogs and external locations. They are not a
  permanent pattern to standardise on.
- `scripts/import-uc-resource-to-bundle.py` is intentionally **self-deprecating**:
  it tracks the support gap it exists to fill so that, once the CLI recognises
  `external_location` / `catalog` as bindable, the script can be retired without
  leaving orphaned state edits behind. The clean end-state is a plain
  `databricks bundle deployment bind <key> <id>` and no script at all.
- When the fix lands, the correct action is to **remove** the script and archive
  this reference (or reduce it to a one-line pointer at the native command) — not
  to keep the Terraform-import hack alive next to a working feature. A workaround
  that outlives its bug becomes a foot-gun: it will keep poking DAB's private
  Terraform surface long after there is a supported path.

## Checking whether the upstream bug has closed

Before using any workaround here, confirm it is still needed. Two checks:

- **Know your CLI version**, because the fix ships in a specific release:

  ```bash
  databricks --version
  ```

- **Check the issue and changelog.** The single source of truth is the upstream
  issue plus the CLI release notes:

  ```bash
  gh issue view 4842 --repo databricks/cli          # look for state: CLOSED + a linked release
  gh release list --repo databricks/cli --limit 10  # scan for a "bundle bind" / external_location entry
  ```

  Or open [databricks/cli#4842](https://github.com/databricks/cli/issues/4842)
  and the CLI `CHANGELOG.md` and grep for `bind` alongside `external_location` /
  `catalog`.

- **Confirm empirically** on your installed version — the definitive test is
  whether bind still rejects the resource type:

  ```bash
  databricks bundle deployment bind <key> <existing-external-location-id> \
    --target <target> --profile <profile>
  ```

  If it no longer errors with an "unsupported resource type" message and instead
  records the linkage, native support has landed — stop using the workarounds and
  begin the deprecation described above.

## Version-accuracy anchors

Tag-tracked items whose exact spelling / version / number should be re-verified
against a live environment before you script on them:

- The bind subcommand path — `databricks bundle deployment bind` vs the shorthand
  `databricks bundle bind` _(verify)_.
- The `unbind` counterpart spelling and flags _(verify)_.
- Whether `resources.catalogs` / `resources.external_locations` are accepted
  blocks in `databricks.yml` at your CLI version _(verify)_.
- CLI version where the gap still holds — stated here as ~**v0.295.x** _(verify)_.
- Issue number **databricks/cli#4842** and its open/closed state _(verify)_.
- The rejection message wording for an unsupported resource type _(verify —
  representative, drifts across versions; never string-match on it)_.
- DAB's internal generated-Terraform directory path and the remote
  `terraform.tfstate` location _(verify — undocumented, moves between releases)_.
- The `direct` engine flag `DATABRICKS_BUNDLE_ENGINE=direct` and its
  no-Terraform-state behaviour _(verify against your version)_.
- Confirmed-stable, no tag needed: the Terraform resource types
  `databricks_external_location` and `databricks_catalog`, and that each imports
  by name.

## Sources

- Databricks — _Databricks CLI bundle commands_ (`bundle deploy`, `bundle
  destroy`, `bundle deployment bind` / `unbind`), docs.databricks.com bundle
  command reference.
- Databricks — _Databricks Asset Bundle resources_: the `resources.*` schema and
  which resource types a bundle can declare, docs.databricks.com bundles/resources.
- databricks/cli GitHub — issue **#4842** tracking `bundle bind` support for UC
  catalogs and external locations (open as of CLI ~v0.295.x).
- terraform-provider-databricks — `databricks_external_location` and
  `databricks_catalog` resource docs (import-by-name semantics for the
  import-based workaround).
- Databricks — _direct deployment engine_ (`DATABRICKS_BUNDLE_ENGINE=direct`) and
  its stateless-vs-Terraform tradeoffs (cross-reference: the D5 bundle-state pain
  entry in this pack's ops research).
- Internal — `004-RL-RSRC-databricks-uc-bundles-ops-research.md` § D4 (the pain
  catalog entry this reference operationalises).
