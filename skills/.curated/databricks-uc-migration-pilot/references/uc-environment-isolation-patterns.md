# UC Environment Isolation Patterns

Unity Catalog gives a Databricks **account exactly one metastore per cloud region**,
and every workspace attaches to the single metastore in its region. So the intuitive
SDLC design — one metastore for dev, one for test, one for prod, all in `us-east-1`,
where promotion is a metadata operation — is **impossible by construction**. You cannot
create a second metastore in a region you already have one in. Teams discover this late,
after the catalog naming convention is already baked into notebooks, views, DLT
pipelines, jobs, dashboards, and every external BI tool's connection string, at which
point it is account-wide and expensive to unwind.

This reference is the four-pattern decision tree for how teams actually get dev/test/prod
isolation under that constraint. Each pattern is rated on three axes:

- **Friction** — setup effort plus the ongoing operational tax (LOW / MEDIUM / HIGH).
- **Isolation** — blast-radius containment and lineage-graph cleanliness. A shared
  metastore means a shared lineage graph and a shared privilege surface; true isolation
  means an accidental `GRANT` or a bad query in dev cannot touch prod (LOW → HIGH).
- **Cost** — the real dollar or dollar-equivalent tax the pattern adds versus a
  single-region single-metastore baseline.

The constraint forces a trade of friction against isolation. Pattern 1 is the default the
platform steers you toward; Patterns 2–4 buy back isolation at rising cost. Pick the
cheapest pattern that satisfies your compliance floor.

---

## Pattern 1 — single-metastore-catalog-per-env · Friction LOW · Isolation LOW · Cost ~$0

**How it works.** All environments share the one regional metastore. Environment is
encoded in the **catalog name**, so dev/test/prod become sibling catalogs under the same
metastore: `bronze_dev`, `bronze_test`, `bronze_prod`. Every catalog reference in SQL,
notebooks, DLT, and jobs is parameterized with a single `env` variable and resolved at
deploy time by a Databricks Asset Bundle (DAB) `target`, which substitutes `${var.env}`.
One codebase, one metastore, N catalogs. This is the pattern Databricks' own UC
best-practices doc steers you toward.

**Naming convention.** `<layer>_<env>.<schema>.<table>` — e.g. `bronze_dev.sales.orders`,
`silver_prod.sales.orders_clean`. The `<env>` suffix is the ONLY thing that changes across
environments; schema and table names stay identical so promotion is a pure catalog swap.

**DAB `databricks.yml` stub** (the entire authoring surface for this pattern):

```yaml
bundle:
  name: sales_pipeline

variables:
  env:
    description: Deployment environment; suffixes every catalog reference.
    default: dev

targets:
  dev:
    mode: development
    default: true
    variables:
      env: dev
    workspace:
      host: https://dbc-xxxx.cloud.databricks.com
  test:
    variables:
      env: test
    workspace:
      host: https://dbc-xxxx.cloud.databricks.com
  prod:
    mode: production
    variables:
      env: prod
    workspace:
      host: https://dbc-xxxx.cloud.databricks.com

resources:
  pipelines:
    sales_etl:
      name: sales_etl_${var.env}
      catalog: bronze_${var.env}          # bronze_dev / bronze_test / bronze_prod
      target: sales                       # schema is env-invariant
```

`databricks bundle deploy -t prod` resolves `${var.env}` → `prod` everywhere. Nothing
else in the pipeline definition changes across environments.

**Cost model.** Effectively **$0 incremental infrastructure** — no duplicate metastore,
no duplicate account, no cross-region data movement. The cost is engineering discipline
plus a permanent lineage tax: because all three catalogs live in one metastore, they
share **one lineage graph**, so `system.access.table_lineage` sees `bronze_dev.sales.orders`
and `bronze_prod.sales.orders` as siblings and cross-environment edges pollute the graph.
BI tools that read the metastore see all environments' catalogs at once (mitigate with
catalog-level `GRANT`s per environment group).

**Operational implications.** Every downstream consumer — Tableau/Power BI connection
strings, ad-hoc SQL, external Delta Sharing recipients — must carry the `_env` suffix, so
a mis-parameterized reference silently reads the wrong environment (a dev job writing to
`_prod` is a one-typo production incident). Privilege isolation is by catalog `GRANT`
only, not by metastore boundary, so an over-broad grant crosses environments. Refactoring
the convention later means renaming every table reference in every asset — hence "decide
before the design freezes."

**Rating.** Friction **LOW** (one variable, one bundle). Isolation **LOW** (shared
metastore = shared lineage + shared privilege surface). Cost **~$0**.

---

## Pattern 2 — multi-region · Friction MEDIUM · Isolation HIGH · Cost HIGH (egress)

**How it works.** Put each environment in a **different region**: dev in `us-west-2`,
prod in `us-east-1`. Because the one-metastore-per-region rule is *per region*, each
environment now gets its own metastore for free — true metastore-level isolation with a
clean, per-environment lineage graph and a hard privilege boundary. This is the
"accidental" way to get separate metastores without a quota exception.

**Naming convention.** Environment lives in the **region/metastore**, not the catalog
name, so catalogs can share names: `bronze.sales.orders` in every environment, with the
region (via the workspace/metastore each target points at) supplying the isolation. The
DAB `target` selects the region by pointing `workspace.host` at that region's workspace.

**Cost model.** The dominant cost is **cross-region data egress**. Any time prod data has
to reach a lower environment (masked prod copies for realistic testing, shared reference
data, DR replication) it crosses a region boundary and bills cloud inter-region transfer
(~$0.02/GB on AWS, comparable on Azure/GCP) on top of duplicated per-region storage.
Databricks' recommended cross-metastore mechanism, **Delta Sharing**, moves the data over
that same egress path — it solves the *sharing* problem but not the *egress-cost*
problem. Compute may also be pricier or scarcer in a non-primary region.

**Operational implications.** Clean lineage and a real blast-radius boundary are the
payoff. The tax is that "promote to prod" is no longer a metadata operation — data and
schema cross regions, latency rises, and any cross-environment read is an egress line item
you can watch grow in `system.billing.usage`. Teams with heavy prod→test data refresh
cycles feel this most.

**Rating.** Friction **MEDIUM** (multi-region workspace + networking setup, but no account
duplication). Isolation **HIGH** (separate metastore + separate lineage graph per env).
Cost **HIGH** where cross-environment data movement is frequent; near-zero if environments
are truly independent.

---

## Pattern 3 — multi-account · Friction HIGH · Isolation HIGHEST · Cost HIGHEST

**How it works.** Give each environment its **own Databricks account**: a dev account, a
test account, a prod account. The one-metastore-per-region limit is *per account*, so each
account gets its own metastore in the same region — full isolation with zero cross-region
egress. This is the strongest boundary UC offers and the one auditors ask for when
environments must be provably separate.

**Naming convention.** Catalog and region can be identical across environments
(`bronze.sales.orders` everywhere); the **account** is the isolation boundary. DAB targets
authenticate to different accounts (different profiles / OAuth service principals).

**Cost model.** Highest, but it is **overhead cost, not egress**: every account-level
concern is duplicated — separate billing invoices and separate account-level
`system.billing.usage`, separate SSO/SCIM identity federation and app registrations,
separate account admins, separate PrivateLink/networking, separate audit-log delivery.
FinOps rollup across environments requires stitching multiple accounts' usage together.

**Operational implications.** Nothing leaks — a compromised or misconfigured dev account
cannot touch prod's metastore, storage credentials, or principals, which is exactly what
regulated workloads (PCI/HIPAA/SOX-adjacent prod isolation) need. The price is
organizational: identities, groups, and secrets must be provisioned three times, and
cross-environment data sharing is again a deliberate Delta Sharing act, not a `GRANT`.

**Rating.** Friction **HIGH** (triple the account-level administration). Isolation
**HIGHEST** (account boundary — the strongest UC offers). Cost **HIGHEST** (duplicated
billing, SSO, principals, networking).

---

## Pattern 4 — soft-quota-bump · Friction LOW (if granted) · Isolation HIGH · Cost ~$0

**How it works.** The one-metastore-per-region limit is a **soft quota**, not a hard
architectural wall. File a request with your Databricks account team to lift it; some
customers are granted **multiple metastores in the same region**, giving separate
dev/test/prod metastores with clean per-environment lineage — the design teams wanted in
the first place — with no region split and no second account. This is an **undocumented
exception**: it is not in the public docs, there is no self-serve API for it, and grant is
at Databricks' discretion.

**Naming convention.** Same as Pattern 3 — environment is the **metastore**, so catalog
names can be identical (`bronze.sales.orders` per environment). Each workspace attaches to
its environment's metastore.

**Cost model.** **~$0 infrastructure if granted** — no egress, no duplicate account, no
naming gymnastics. The real cost is the **dependency and the risk**: you are relying on a
non-contractual, undocumented exception, so do not design a compliance story that *requires*
it until it is confirmed in writing by the account team, and have Pattern 1 as the
fallback if the request is declined.

**Operational implications.** If granted, this is strictly the best outcome — the
isolation of separate metastores at the friction of a single region and account. Because
it is discretionary, treat it as a request to make *early* (during account setup, alongside
your Databricks rep) rather than a design you can assume. Availability skews toward larger
/ enterprise-committed accounts.

**Rating.** Friction **LOW** *conditional on grant* (a support request, then normal
single-region ops). Isolation **HIGH** (separate metastore per env). Cost **~$0** if
granted; the risk is non-availability, not dollars.

---

## Choosing a pattern

Walk these in order — the first matching row wins:

1. **Hard regulatory / contractual isolation** (prod must be provably unreachable from
   lower environments; separate billing/audit boundary mandated) → **Pattern 3
   (multi-account)**. It is the only pattern that isolates at the *account* level; accept
   the administrative cost as the price of the audit story.

2. **Strong isolation wanted, no account-duplication appetite, and you can ask early** →
   **Pattern 4 (soft-quota-bump)** as the primary request, with **Pattern 1** pre-designed
   as the fallback. Never let go-live depend on an ungranted exception.

3. **Lineage cleanliness matters** (you rely on `system.access.*_lineage` for impact
   analysis or compliance, and cross-environment lineage pollution is unacceptable) **and
   cross-environment data movement is rare** → **Pattern 2 (multi-region)**. You get
   per-environment lineage graphs; the egress cost stays low precisely because the
   environments rarely exchange data.

4. **Cost-sensitive, many BI-tool / downstream connections, frequent prod↔lower-env data
   refresh, and no hard isolation mandate** → **Pattern 1 (single-metastore-catalog-per-env)**.
   It is the platform default, costs ~$0 in infrastructure, and its lineage/privilege
   compromise is acceptable when there is no regulatory reason to pay for more.

**The dominant decision variables**, in priority order: (a) **compliance requirement** —
a hard isolation mandate forces Pattern 3 and short-circuits everything below; (b) **cost
sensitivity** — egress (Pattern 2) and duplicated account overhead (Pattern 3) are the
expensive axes, so a tight budget pushes toward Patterns 1/4; (c) **BI-tool and lineage
needs** — many downstream connection strings make Pattern 1's `_env`-suffix tax painful
and make the clean-lineage patterns (2/4, or 3) more attractive. When in doubt, default to
Pattern 1 and file the Pattern 4 request in parallel — the fallback is free and the upside
is the design you originally wanted.

## Sources

- Databricks Community, "Metastore: one per account+region limitation" — https://community.databricks.com/t5/data-governance/metastore-one-per-account-region-limitation/td-p/41097
- Databricks Community, "Unity Catalog: multiple metastore in same region" — https://community.databricks.com/t5/data-governance/unity-catalog-multiple-metastore-in-same-region/td-p/28513
- Unity Catalog best practices (catalog-per-environment guidance) — https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices
- Set up and manage Unity Catalog (one metastore per region) — https://docs.databricks.com/aws/en/data-governance/unity-catalog/get-started
- Databricks Asset Bundles: targets and variable substitution — https://docs.databricks.com/aws/en/dev-tools/bundles/settings
- Delta Sharing (cross-metastore / cross-region sharing model) — https://docs.databricks.com/aws/en/delta-sharing/
- System tables: data lineage (metastore-scoped lineage graph) — https://docs.databricks.com/aws/en/admin/system-tables/lineage
