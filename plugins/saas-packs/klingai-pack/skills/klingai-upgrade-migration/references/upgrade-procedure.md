# Upgrade Procedure

## Upgrade Procedure

```python
class UpgradeProcedure:
    """Structured upgrade procedure with rollback capability."""

    def __init__(self, backup_dir: str = "./upgrade_backup"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.rollback_steps = []

    def backup_file(self, filepath: str):
        """Backup a file before modification."""
        source = Path(filepath)
        if source.exists():
            dest = self.backup_dir / source.name
            import shutil
            shutil.copy2(source, dest)
            self.rollback_steps.append(("restore_file", str(source), str(dest)))
            print(f"Backed up {filepath}")

    def upgrade_dependency(self, package: str, version: str):
        """Upgrade a Python package."""
        import subprocess

        # Record current version for rollback
        result = subprocess.run(
            ["pip", "show", package],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if line.startswith("Version:"):
                    old_version = line.split(":")[1].strip()
                    self.rollback_steps.append(("downgrade", package, old_version))
                    break

        # Perform upgrade
        subprocess.run(["pip", "install", f"{package}=={version}"], check=True)
        print(f"Upgraded {package} to {version}")

    def rollback(self):
        """Rollback all changes."""
        print("\nRolling back changes...")

        for step in reversed(self.rollback_steps):
            action = step[0]

            if action == "restore_file":
                _, dest, source = step
                import shutil
                shutil.copy2(source, dest)
                print(f"Restored {dest}")

            elif action == "downgrade":
                _, package, version = step
                import subprocess
                subprocess.run(["pip", "install", f"{package}=={version}"])
                print(f"Downgraded {package} to {version}")

        print("Rollback complete")

    def verify_upgrade(self) -> bool:
        """Run verification tests."""
        # Import test module and run
        try:
            # Run basic connectivity test
            response = requests.get(
                "https://api.klingai.com/v1/account",
                headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Verification failed: {e}")
            return False

# Usage
upgrade = UpgradeProcedure()

try:
    upgrade.backup_file("config.json")
    upgrade.upgrade_dependency("klingai-sdk", "1.1.0")

    if not upgrade.verify_upgrade():
        upgrade.rollback()
        print("Upgrade failed - rolled back")
    else:
        print("Upgrade successful!")

except Exception as e:
    print(f"Error during upgrade: {e}")
    upgrade.rollback()
```
