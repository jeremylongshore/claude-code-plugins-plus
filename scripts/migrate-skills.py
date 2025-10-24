#!/usr/bin/env python3
"""
Migrate Agent Skills from non-compliant to Anthropic-compliant structure.

Uses skill-name-mappings.json to perform the migration:
FROM: skills/skill-adapter/SKILL.md
TO:   skills/{descriptive-name}/SKILL.md
"""

import json
import shutil
import sys
from pathlib import Path

def load_mappings():
    """Load the skill name mappings"""
    mappings_file = Path('skill-name-mappings.json')
    if not mappings_file.exists():
        print("❌ Error: skill-name-mappings.json not found")
        print("   Run analyze-skill-names-gemini.py first")
        sys.exit(1)

    with open(mappings_file) as f:
        return json.load(f)

def migrate_plugin(plugin_path: str, mapping: dict, dry_run: bool = True):
    """Migrate a single plugin's skill structure"""
    plugin_dir = Path('plugins') / plugin_path
    old_dir = plugin_dir / 'skills' / 'skill-adapter'
    new_dir = plugin_dir / 'skills' / mapping['new_skill_name']

    if not old_dir.exists():
        return False, "Old directory not found"

    if new_dir.exists():
        return False, f"New directory already exists: {new_dir}"

    if dry_run:
        return True, "Would migrate"

    # Perform actual migration
    try:
        # Move the entire skill-adapter directory to new name
        shutil.move(str(old_dir), str(new_dir))
        return True, "Migrated successfully"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Migrate Agent Skills to Anthropic-compliant structure')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Preview changes without executing (default: True)')
    parser.add_argument('--execute', action='store_true',
                        help='Execute the migration (overrides --dry-run)')
    args = parser.parse_args()

    dry_run = not args.execute

    print("=" * 60)
    print("Agent Skills Migration to Anthropic-Compliant Structure")
    print("=" * 60)
    print()

    if dry_run:
        print("⚠️  DRY RUN MODE - No actual changes will be made")
        print("   Use --execute to perform migration")
    else:
        print("🚀 EXECUTE MODE - Changes will be made!")
        confirm = input("\nAre you sure you want to proceed? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Migration cancelled")
            sys.exit(0)

    print()

    # Load mappings
    mappings = load_mappings()
    print(f"📋 Loaded {len(mappings)} plugin mappings\n")

    # Perform migration
    success_count = 0
    error_count = 0
    errors = []

    for i, (plugin_path, mapping) in enumerate(mappings.items(), 1):
        print(f"[{i}/{len(mappings)}] {plugin_path}")
        print(f"  → {mapping['new_skill_name']}... ", end='', flush=True)

        success, message = migrate_plugin(plugin_path, mapping, dry_run)

        if success:
            print(f"✅ {message}")
            success_count += 1
        else:
            print(f"❌ {message}")
            error_count += 1
            errors.append((plugin_path, message))

    # Summary
    print()
    print("=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Total plugins: {len(mappings)}")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Errors: {error_count}")

    if errors:
        print(f"\n⚠️  Errors encountered:")
        for path, error in errors:
            print(f"   - {path}: {error}")

    if dry_run:
        print(f"\n💡 This was a DRY RUN. To execute migration, run:")
        print(f"   python3 scripts/migrate-skills.py --execute")
    else:
        print(f"\n✨ Migration complete!")
        print(f"\nNext steps:")
        print(f"1. Verify migrations: git status")
        print(f"2. Test plugin loading")
        print(f"3. Update generator scripts")
        print(f"4. Commit changes")

if __name__ == '__main__':
    main()
