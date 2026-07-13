# Log Retention & Archival

## Log Retention & Archival

### Retention Policy

```python
class LogRetentionManager:
    """Manage log retention and archival."""

    def __init__(
        self,
        log_dir: str,
        retention_days: int = 90,
        archive_after_days: int = 30
    ):
        self.log_dir = Path(log_dir)
        self.retention_days = retention_days
        self.archive_after_days = archive_after_days

    def get_log_date(self, filename: str) -> date:
        """Extract date from log filename."""
        date_str = filename.replace("audit_", "").replace(".jsonl", "")
        return datetime.strptime(date_str, "%Y-%m-%d").date()

    def run_retention(self):
        """Apply retention policy."""
        today = date.today()
        archived = []
        deleted = []

        for log_file in self.log_dir.glob("audit_*.jsonl"):
            log_date = self.get_log_date(log_file.stem)
            age_days = (today - log_date).days

            if age_days > self.retention_days:
                # Delete old logs
                log_file.unlink()
                deleted.append(log_file.name)

            elif age_days > self.archive_after_days:
                # Archive to compressed format
                self._archive_log(log_file)
                archived.append(log_file.name)

        return {"archived": archived, "deleted": deleted}

    def _archive_log(self, log_file: Path):
        """Compress and archive log file."""
        import gzip
        import shutil

        archive_dir = self.log_dir / "archive"
        archive_dir.mkdir(exist_ok=True)

        archive_path = archive_dir / (log_file.name + ".gz")
        with open(log_file, 'rb') as f_in:
            with gzip.open(archive_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        log_file.unlink()

retention_manager = LogRetentionManager(
    "audit_logs",
    retention_days=90,
    archive_after_days=30
)
```
