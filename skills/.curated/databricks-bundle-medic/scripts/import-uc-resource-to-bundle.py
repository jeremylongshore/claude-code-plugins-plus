#!/usr/bin/env python3
"""import-uc-resource-to-bundle.py — bring an EXISTING Unity Catalog resource under
Databricks Asset Bundle (DAB) management when `databricks bundle bind` cannot
(databricks-bundle-medic, pain D4).

╔══════════════════════════════════════════════════════════════════════════════╗
║ SELF-DEPRECATING WORKAROUND — REMOVE WHEN databricks/cli#4842 CLOSES.         ║
║ `databricks bundle bind` does not yet support UC catalogs or external         ║
║ locations. When #4842 ships bind support, delete this script in the same      ║
║ release that bumps the databricks CLI dependency, and switch callers to       ║
║ `databricks bundle deployment bind`. Check: is #4842 closed for your CLI?     ║
║   databricks --version   →   github.com/databricks/cli/issues/4842            ║
╚══════════════════════════════════════════════════════════════════════════════╝

The gap: a team with an existing UC catalog / external location cannot bring it under
DAB without either hand-editing terraform.tfstate (hostile, undocumented) or
destroy-and-recreate (impossible if dependent tables exist). The safe middle path is a
Terraform `import` block: declare the resource in the bundle, tell Terraform the
resource ALREADY exists (by id), and let the next deploy adopt it instead of recreating.

This script GENERATES that plan — the `resources:` YAML to add to databricks.yml plus
the matching `import {}` block — deterministically. It does NOT run the deploy or edit
state; the engineer reviews and applies. Emitting a plan (not mutating state) is the
whole point: the hand-edit path is what makes D4 dangerous.

Usage:
  import-uc-resource-to-bundle.py --type catalog --name analytics --resource-key analytics_cat
  import-uc-resource-to-bundle.py --type external_location --name raw_zone \
      --resource-key raw_zone_loc [--json]
Exit: 0 ok · 2 bad usage.
"""

import argparse
import json
import sys

# UC resource types this D4 workaround covers — exactly the ones `bundle bind` cannot,
# mapped to their Terraform resource type and the id Terraform imports them by.
SUPPORTED = {
    "catalog": {
        "tf_type": "databricks_catalog",
        "id_hint": "the catalog name (e.g. `analytics`)",
        "dab_kind": "catalogs",
    },
    "external_location": {
        "tf_type": "databricks_external_location",
        "id_hint": "the external-location name (e.g. `raw_zone`)",
        "dab_kind": "external_locations",
    },
}


def build_import_plan(resource_type, name, resource_key):
    """Return {yaml_block, import_block, import_command, warnings, self_deprecation}.
    Pure — no CLI, no state mutation. The id Terraform imports by is the resource NAME
    for both UC catalogs and external locations."""
    if resource_type not in SUPPORTED:
        raise ValueError(f"unsupported --type {resource_type!r}; use one of {sorted(SUPPORTED)}")
    spec = SUPPORTED[resource_type]
    tf_type = spec["tf_type"]

    yaml_block = (
        f"resources:\n"
        f"  {spec['dab_kind']}:\n"
        f"    {resource_key}:\n"
        f"      name: {name}\n"
        f"      # ... fill remaining required fields from `databricks {resource_type}s get {name}`\n"
    )
    # Terraform 1.5+ import block — declarative, reviewable, no state hand-edit.
    import_block = f'import {{\n  to = {tf_type}.{resource_key}\n  id = "{name}"\n}}\n'
    import_command = f'terraform import {tf_type}.{resource_key} "{name}"'
    warnings = [
        "Verify the resource id: for a UC catalog and external location Terraform "
        f"imports by NAME ({spec['id_hint']}) — confirm with the provider docs for your version.",
        "Run the import against the bundle's OWN terraform working dir "
        "(.databricks/bundle/<target>/terraform), or add the import{} block and let the "
        "next `databricks bundle deploy` adopt it — do NOT edit terraform.tfstate by hand.",
        "Take a state backup first (the bundle-deploy-guard hook caches one on deploy).",
    ]
    return {
        "resource_type": resource_type,
        "tf_type": tf_type,
        "yaml_block": yaml_block,
        "import_block": import_block,
        "import_command": import_command,
        "warnings": warnings,
        "self_deprecation": "This workaround is obsolete once databricks/cli#4842 ships "
        "`bundle bind` support for UC catalogs/external locations — remove it then.",
    }


def main():
    ap = argparse.ArgumentParser(description="Generate a DAB import plan for a UC resource (D4 workaround)")
    ap.add_argument("--type", required=True, choices=sorted(SUPPORTED))
    ap.add_argument("--name", required=True, help="the existing UC resource's name")
    ap.add_argument("--resource-key", required=True, help="the key to give it in databricks.yml")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    plan = build_import_plan(args.type, args.name, args.resource_key)
    if args.json:
        print(json.dumps(plan, indent=2))
        return 0

    print(f"# D4 workaround — import an existing {args.type} into the bundle (databricks/cli#4842)")
    print("\n## 1. Add to databricks.yml\n")
    print(plan["yaml_block"])
    print("## 2a. Declarative import block (Terraform 1.5+), OR\n")
    print(plan["import_block"])
    print("## 2b. Imperative import command\n")
    print(f"    {plan['import_command']}\n")
    print("## Warnings")
    for w in plan["warnings"]:
        print(f"  - {w}")
    print(f"\n[self-deprecating] {plan['self_deprecation']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
