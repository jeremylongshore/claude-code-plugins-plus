# Terraform provider 2.x deployment evidence

Use the live [snowflakedb/snowflake provider documentation](https://registry.terraform.io/providers/snowflakedb/snowflake/latest/docs)
and the provider's locked version when reviewing a plan. The provider has stable
resources supported from the 2.x line, while preview resources/features have a
separate stability contract. Do not copy a version number from this reference as
an evergreen recommendation.

## State and plan gate

Before any apply, preserve:

- provider source and lock-file checksums;
- Terraform and provider versions;
- backend/workspace identity (never paste backend credentials);
- a parseable state receipt and saved plan output;
- `terraform plan -detailed-exitcode` status.

Interpret detailed exit status correctly: `0` means no changes, `2` means a valid
plan with changes, and another non-zero status means the plan failed. A zero-change
plan is a useful adoption receipt only after refresh and provider warnings are
reviewed; it is not proof that the remote account is correct if the wrong account
or role was selected.

If state is truncated or unreadable, stop. Preserve the backend version and use
the backend's documented recovery/locking process. Never hand-edit
`terraform.tfstate` as a grant or object-adoption shortcut.

## Grants, ownership, and import

Grant resources are especially sensitive to object identity, ownership, and
privilege ordering. For an existing role/object grant, first determine whether
the provider resource supports import and what import identity the current
provider version documents. Declare the desired resource, import the existing
remote object into the matching address, refresh, and produce a zero-change plan.

Review each grant for:

1. intended grantee (account role, database role, or share);
2. object scope and future-grants scope;
3. ownership transfer and managed-access implications;
4. whether the plan removes a privilege not present in configuration;
5. whether a provider upgrade changes grant normalization or import validation.

Do not destroy and recreate a live database/schema/grant graph to make Terraform
happy. A dependency graph can make that destructive route impossible or unsafe.
Adoption must be reversible and separately approved.

## Preview resources

If `preview_features_enabled` or a preview resource appears, identify the exact
feature in the current provider docs and release notes, then record a rollback or
forward-fix path. A preview feature is not made production-safe by a green plan.

Useful primary references:

- [Provider overview and support boundary](https://registry.terraform.io/providers/snowflakedb/snowflake/latest/docs)
- [Grant privileges to account role](https://registry.terraform.io/providers/snowflakedb/snowflake/latest/docs/resources/grant_privileges_to_account_role)
- [Grant ownership](https://registry.terraform.io/providers/snowflakedb/snowflake/latest/docs/resources/grant_ownership)
- [Terraform import](https://developer.hashicorp.com/terraform/language/import)
