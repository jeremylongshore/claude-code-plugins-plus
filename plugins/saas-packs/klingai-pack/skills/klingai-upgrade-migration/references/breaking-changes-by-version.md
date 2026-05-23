# Breaking Changes By Version

## Breaking Changes by Version

### v1.0.0 → v1.1.0

```python
# No breaking changes
# New features:
# - Added camera_motion parameter
# - Added negative_prompt support
```

### v0.x → v1.0 (Major)

```python
# Breaking: Response structure changed

# Old (v0.x):
response = {
    "id": "job123",
    "state": "complete",  # Changed to "status"
    "result_url": "..."   # Changed to "video_url"
}

# New (v1.0):
response = {
    "job_id": "job123",   # "id" -> "job_id"
    "status": "completed", # "state" -> "status", "complete" -> "completed"
    "video_url": "..."     # "result_url" -> "video_url"
}

# Migration helper:
def migrate_response(old_response: dict) -> dict:
    """Convert v0.x response to v1.0 format."""
    return {
        "job_id": old_response.get("id"),
        "status": "completed" if old_response.get("state") == "complete" else old_response.get("state"),
        "video_url": old_response.get("result_url")
    }
```
