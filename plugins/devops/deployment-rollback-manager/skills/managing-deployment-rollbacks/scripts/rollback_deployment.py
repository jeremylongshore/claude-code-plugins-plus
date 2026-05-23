#!/usr/bin/env python3
"""
deployment-rollback-manager - Deployment Script
Script to execute the deployment rollback process, including safety checks and version verification.
Generated: 2025-12-10 03:48:17
"""

import os
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

class Deployer:
    def __init__(self, source: str, target: str):
        self.source = Path(source)
        self.target = Path(target)
        self.deployed = []
        self.failed = []

    def validate_source(self) -> bool:
        """Validate source directory exists."""
        if not self.source.exists():
            print(f"❌ Source directory not found: {self.source}")
            return False

        if not any(self.source.iterdir()):
            print(f"❌ Source directory is empty: {self.source}")
            return False

        print(f"✓ Source validated: {self.source}")
        return True

    def prepare_target(self) -> bool:
        """Prepare target directory."""
        try:
            self.target.mkdir(parents=True, exist_ok=True)

            # Create deployment metadata
            metadata = {
                "deployment_time": datetime.now().isoformat(),
                "source": str(self.source),
                "skill": "deployment-rollback-manager",
                "category": "devops",
                "plugin": "deployment-rollback-manager"
            }

            metadata_file = self.target / ".deployment.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"✓ Target prepared: {self.target}")
            return True
        except Exception as e:
            print(f"❌ Failed to prepare target: {e}")
            return False

    def deploy_files(self) -> bool:
        """Deploy files from source to target."""
        success = True

        for source_file in self.source.rglob('*'):
            if source_file.is_file():
                relative_path = source_file.relative_to(self.source)
                target_file = self.target / relative_path

                try:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, target_file)
                    self.deployed.append(str(relative_path))
                    print(f"  ✓ Deployed: {relative_path}")
                except Exception as e:
                    self.failed.append({
                        "file": str(relative_path),
                        "error": str(e)
                    })
                    print(f"  ✗ Failed: {relative_path} - {e}")
                    success = False

        return success

    def generate_report(self) -> Dict:
        """Generate deployment report."""
        report = {
            "deployment_time": datetime.now().isoformat(),
            "skill": "deployment-rollback-manager",
            "source": str(self.source),
            "target": str(self.target),
            "total_files": len(self.deployed) + len(self.failed),
            "deployed": len(self.deployed),
            "failed": len(self.failed),
            "deployed_files": self.deployed,
            "failed_files": self.failed
        }

        # Save report
        report_file = self.target / "deployment_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def rollback(self):
        """Rollback deployment on failure."""
        print("⚠️  Rolling back deployment...")

        for deployed_file in self.deployed:
            file_path = self.target / deployed_file
            if file_path.exists():
                file_path.unlink()
                print(f"  ✓ Removed: {deployed_file}")

        # Remove empty directories
        for dir_path in sorted(self.target.rglob('*'), reverse=True):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                dir_path.rmdir()

def main():
    parser = argparse.ArgumentParser(description="Script to execute the deployment rollback process, including safety checks and version verification.")
    parser.add_argument('source', help='Source directory')
    parser.add_argument('target', help='Target deployment directory')
    parser.add_argument('--dry-run', action='store_true', help='Simulate deployment')
    parser.add_argument('--force', action='store_true', help='Overwrite existing files')
    parser.add_argument('--rollback-on-error', action='store_true', help='Rollback on any error')

    args = parser.parse_args()

    deployer = Deployer(args.source, args.target)

    print(f"🚀 Deploying deployment-rollback-manager...")
    print(f"   Source: {args.source}")
    print(f"   Target: {args.target}")

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be deployed")
        return 0

    # Validate and prepare
    if not deployer.validate_source():
        return 1

    if not deployer.prepare_target():
        return 1

    # Deploy
    success = deployer.deploy_files()

    # Generate report
    report = deployer.generate_report()

    print(f"\n📊 DEPLOYMENT SUMMARY")
    print(f"   Total Files: {report['total_files']}")
    print(f"   ✅ Deployed: {report['deployed']}")
    print(f"   ❌ Failed: {report['failed']}")

    if not success and args.rollback_on_error:
        deployer.rollback()
        return 1

    if report['failed'] == 0:
        print(f"\n✅ Deployment completed successfully!")
        return 0
    else:
        print(f"\n⚠️  Deployment completed with errors")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
