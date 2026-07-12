# SCIM Identity-Bridge Patterns — Entra Nested Groups and Immutable External Groups

Unity Catalog resolves every permission through **account-level group membership**.
A `GRANT SELECT ON TABLE main.sales.orders TO analysts` grants the *account
group* `analysts`; a user only inherits that privilege if they are a member of
that account group **inside Databricks**. Nothing in UC reads your identity
provider directly — UC reads the account's group graph, and that graph is
populated by the **SCIM bridge** from Entra ID (Azure AD). So the correctness of
every UC grant rests on one silent assumption: *the group membership you see in
Entra is the group membership Databricks actually received.* When the bridge
drops a membership edge, the `GRANT` is still there, the group is still there,
the user is still there — and the access simply does not apply. No error is
raised at grant time or at query time; the user just gets a permission-denied on
a table you "granted" them.

This reference covers the one bridge behavior that breaks this assumption most
often — **the Entra SCIM connector does not flatten nested groups** — plus the
second-order trap it leads teams into (the **IdP-managed "external" group lock**),
and three workarounds with their tradeoffs. The `uc-permission-tracer` subagent
flags the *symptom* ("user is in a group that holds the grant but the grant
doesn't resolve"); this document is the *cause and fix*. Error strings marked
*(representative)* are accurate paraphrases — exact wording drifts across Entra
and Databricks versions; do not quote them as literals.

For UC, provision to the **account-level** SCIM endpoint (account console →
provisioning, the "Azure Databricks SCIM Provisioning Connector" enterprise app
pointed at the account, not a single workspace) and enable identity federation.
UC privileges are account-scoped; a workspace-local group cannot receive a UC
grant, so a workspace-only SCIM target reproduces this whole problem one level down.

---

## The nested-group enumeration limitation

**What the connector does.** When you assign an Entra group to the Databricks
provisioning enterprise app (or scope it in via an assignment filter), the Entra
provisioning service enumerates and provisions the group's **direct user members
only**. It creates the group as a Databricks account group and adds the users who
sit *directly* in it. That is the entire contract.

**What it does not do.** It does **not** flatten nested groups. If an assigned
group `B` contains another group `A` as a member, the *members of `A` are never
provisioned as members of `B` in Databricks*. Entra treats `A` as a member object
it cannot represent (Databricks account groups can nest, but the Entra
provisioning service does not walk the tree to materialize the transitive
membership), so `A`'s users simply do not appear under `B`. This is an
**architectural constraint of the Entra provisioning service**, documented by
Microsoft as "nested groups are not supported for provisioning." It is **not a
configuration toggle** — there is no "flatten nested groups" checkbox, no scoping
option, and no SCIM attribute that turns it on.

**The exact failure.** Model the common case:

```
Entra:  user  alice  ──member-of──▶  group A (data-scientists-ml)
        group A       ──member-of──▶  group B (analysts)          ← assigned to the app
UC:     GRANT SELECT ON TABLE main.sales.orders TO `analysts`;    ← grant on B
```

- Entra provisions group `B` (`analysts`) to Databricks because it is assigned.
- Entra provisions `B`'s **direct** members. `alice` is **not** a direct member
  of `B` — she is a member of `A`, which is a member of `B`.
- Therefore Databricks' account group `analysts` **does not contain `alice`**.
- The UC grant on `analysts` resolves against Databricks' membership, so
  `alice` is denied `main.sales.orders` — even though "she's in analysts" is true
  in Entra.

The tell in the permission tracer: the grant exists on the account group, the
account group exists, and the user exists — but `SHOW GROUPS WITH USER alice`
(or the account SCIM membership) does not list the grant-holding group. Symptom
*(representative)*:

```
[uc-permission-tracer] user alice@corp.com : SELECT on main.sales.orders DENIED.
Grant target `analysts` present; user not a member of `analysts` in the account
group graph. Entra shows alice ∈ data-scientists-ml ∈ analysts (nested) —
transitive membership not provisioned by the SCIM connector.
```

**Provision-on-demand does not fix it.** Entra's "provision on demand" (force a
single user through immediately, bypassing the sync cycle) evaluates the same
direct-assignment logic — it is a timing shortcut for one principal, not a
nested-group flattener. It will still not place `alice` into `B`.

---

## The "external" / IdP-managed group lock

Once the bridge drops a membership, the instinct is to "just add the user to the
group in Databricks." That is where the second trap springs.

**What the flag is.** A Databricks account group that was **created by the SCIM
connector is IdP-managed** ("external"): its membership is owned by the identity
provider, and Databricks treats the IdP as the single writer. In the account
console such a group shows as managed by your IdP; via Terraform it is a group
your config did not create and must not mutate.

**What it locks.** Any attempt to modify that group's membership **from inside
Databricks** — account-console UI, the account SCIM API, or the
`databricks_group_member` Terraform resource — is **rejected**. Adding `alice`
directly to the IdP-managed `analysts` fails; the connector is the only allowed
source of that edge. The rejection typically surfaces as an **InternalError-class
failure** rather than a clean 4xx, e.g. *(representative)*:

```
InternalError: cannot modify members of group `analysts`; membership is managed
by an external identity provider. Update the group in your IdP instead.
```

**When it bites.** It bites precisely at the moment you try to hand-patch the
nested-group gap — you have found the missing `alice`-in-`analysts` edge, you go
to add it, and Databricks refuses because that group belongs to Entra. It also
bites Terraform runs that declare `databricks_group_member` against a
SCIM-provisioned group: the apply either errors or thrashes against the next sync
cycle, which reasserts the IdP's view. The lock is correct behavior (it keeps the
IdP authoritative), but it means the fix must happen *in Entra* or *outside the
IdP-managed group entirely* — never as an in-Databricks membership edit on a
provisioned group.

---

## Workaround A — flatten the group structure in Entra (cleanest)

**How it works.** Restructure the groups in Entra so that **every group assigned
to the Databricks app has only USER members** — no group-in-group. Where you have
`A ⊂ B` and `B` holds the grant, either assign `A` to the app directly and put
the grant on `A`, or add `A`'s users as direct members of `B` (and stop nesting).
Entra then enumerates exactly the users you expect, and the bridge carries the
full membership.

**Tradeoff.** This is the only workaround that **preserves the IdP as the single
source of truth** — Databricks stays a pure mirror, the "external" lock stays a
feature not an obstacle, and there is nothing extra to run or own. The cost is
organizational: you flatten (and keep flat) the parts of your Entra group tree
that feed Databricks, which fights any existing role-hierarchy convention and
requires governance so nobody re-nests an assigned group later. Best when the
Databricks-facing slice of your directory is small enough to keep flat by policy.

---

## Workaround B — bypass the SCIM connector (Terraform + Graph)

**How it works.** Stop relying on the connector to compute membership. Instead,
walk the nested tree yourself with the **Microsoft Graph API** — `GET
/groups/{id}/transitiveMembers` returns the *flattened* membership (nested
included), whereas `/members` returns direct-only — and materialize that
flattened set into Databricks with the **Databricks Terraform provider** (or the
account SCIM API) on a cron. Turn the connector off for these groups so the two
writers do not fight.

Flatten via Graph (filter to users; page through `@odata.nextLink`):

```bash
# Direct members only — what the SCIM connector sees:
GET https://graph.microsoft.com/v1.0/groups/{B_id}/members

# Transitive (flattened, nested included) — what UC actually needs:
curl -s -H "Authorization: Bearer $GRAPH_TOKEN" \
  "https://graph.microsoft.com/v1.0/groups/{B_id}/transitiveMembers/microsoft.graph.user?\$select=id,userPrincipalName"
```

Materialize into a Databricks-native account group (provider pinned at the
**account** host, not a workspace):

```hcl
provider "databricks" {
  host       = "https://accounts.azuredatabricks.net"  # AWS: accounts.cloud.databricks.com
  account_id = var.databricks_account_id
}

# A group WE own (not IdP-managed) so membership writes are allowed:
resource "databricks_group" "analysts_flat" {
  display_name = "analysts"
}

# One row per user returned by transitiveMembers (rendered from the Graph walk):
resource "databricks_group_member" "analysts_flat" {
  for_each  = toset(var.analysts_transitive_upns)  # flattened set from Graph
  group_id  = databricks_group.analysts_flat.id
  member_id = databricks_user.by_upn[each.value].id
}
```

**Tradeoff.** You **lose the IdP-as-source-of-truth invariant** — you now own the
sync. Correctness becomes a function of your cron's freshness (a user removed from
a nested Entra group stays entitled until your next run), your Graph app
registration's `GroupMember.Read.All` / `User.Read.All` permissions, and your
reconciliation logic (deletes as well as adds). You have rebuilt a slice of the
provisioning service, with its failure modes now on your pager. Reserve this for
groups whose nesting you cannot flatten in Entra and whose membership must still
be IdP-derived.

---

## Workaround C — Databricks-native account groups (escape hatch)

**How it works.** For the cases that genuinely need **in-Databricks membership
management** — a break-glass group, a service-team group with no Entra
counterpart, a group whose membership is a Databricks-internal concept — create
the account group **natively in Databricks** and do **not** provision it from
Entra. Because no IdP owns it, the "external" lock never applies: you add and
remove members freely via the account console, account SCIM API, or
`databricks_group_member`.

```hcl
# Native group — Databricks is the writer; no Entra assignment for this group.
resource "databricks_group" "break_glass" {
  display_name = "uc-break-glass"
}
resource "databricks_group_member" "break_glass" {
  group_id  = databricks_group.break_glass.id
  member_id = databricks_service_principal.oncall.id
}
```

**Tradeoff.** It is an **escape hatch, not a default**. These groups are **not
IdP-governed**, so they sit outside your central joiner-mover-leaver process — a
person offboarded in Entra is *not* removed from a native Databricks group, which
is exactly the audit gap SSO/SCIM exists to close. Keep the native set small,
named so it is obviously out-of-band, and reviewed on its own cadence. Never use
native groups to paper over the nested-group problem at scale — that quietly
migrates your whole authorization model out of the IdP.

---

## SCIM sync timing — confirm the change landed before trusting the grant

**Provisioning is not immediate.** The Entra provisioning service runs on an
**incremental cycle of roughly 40 minutes** (Microsoft documents the interval as
"approximately every 40 minutes"; observed windows run ~20–40 min). A membership
change in Entra — or a group you just assigned — is therefore **not visible in
Databricks the instant you make it**. The initial cycle after enabling
provisioning can take longer still. Any automation that grants in UC and
immediately asserts access will race the bridge and produce a false "the grant is
broken" when the membership simply has not synced yet.

**Confirm, don't assume — poll with exponential backoff.** After a membership
change, poll the Databricks **account** group membership until the expected user
appears (or a ceiling is hit), backing off between attempts so you neither
hammer the API nor wait a fixed worst-case 40 minutes:

```python
import time, itertools
from databricks.sdk import AccountClient

a = AccountClient()  # account host + account_id configured

def member_present(group_id: str, user_id: str) -> bool:
    grp = a.groups.get(id=group_id)          # account SCIM Groups.get
    return any(m.value == user_id for m in (grp.members or []))

def wait_for_membership(group_id: str, user_id: str,
                        base=15.0, cap=300.0, deadline_s=2700):
    """Poll until user lands in group. Backoff 15s→30s→...→300s; ~45 min ceiling."""
    start = time.monotonic()
    for attempt in itertools.count():
        if member_present(group_id, user_id):
            return True                        # synced — grant will now resolve
        if time.monotonic() - start > deadline_s:
            raise TimeoutError(
                f"user {user_id} not in group {group_id} after {deadline_s}s — "
                "check Entra provisioning logs / nested-group enumeration")
        time.sleep(min(cap, base * (2 ** attempt)))
```

Gate any "the grant works now" claim — or any downstream smoke test of the
table access — on `wait_for_membership` returning `True`, not on wall-clock hope.
When it times out, that is the real signal: it means either the sync is
genuinely stuck (check the Entra provisioning logs) **or** you have hit the
nested-group limitation above and the user was never eligible to be provisioned
into that group in the first place.

## Sources

- Microsoft — *Tutorial: Configure Azure Databricks SCIM Provisioning Connector
  for automatic user provisioning*, learn.microsoft.com (assignment scoping,
  provisioning connector setup).
- Microsoft — *How Application Provisioning works in Microsoft Entra ID* and
  *Known issues / limitations for provisioning*, learn.microsoft.com — nested
  groups are not provisioned; incremental cycle ≈ 40 minutes; provision-on-demand.
- Microsoft Graph — *List group transitiveMembers* vs *List group members*,
  learn.microsoft.com/graph — `transitiveMembers` returns flattened membership.
- Databricks — *Sync users and groups from Microsoft Entra ID (Azure AD)* and
  *Set up SCIM provisioning to Databricks using Microsoft Entra ID*,
  docs.databricks.com (account-level provisioning for Unity Catalog).
- Databricks — *Manage groups* / *Identity federation*, docs.databricks.com —
  account groups, IdP-managed (external) groups, and why membership of
  IdP-managed groups cannot be edited in Databricks.
- Databricks Terraform provider — `databricks_group`, `databricks_group_member`,
  `databricks_user` (account-level, `accounts.*databricks.*` host),
  registry.terraform.io/providers/databricks/databricks.
- community.databricks.com — threads on Entra nested groups not syncing to the
  account, "cannot modify externally-managed group members," and SCIM sync-delay
  troubleshooting.
