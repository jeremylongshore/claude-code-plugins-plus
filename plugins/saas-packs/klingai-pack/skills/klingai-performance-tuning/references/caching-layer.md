# Caching Layer

## Caching Layer

```python
import hashlib
import json
from pathlib import Path

class VideoCache:
    """Cache generated videos to avoid regeneration."""

    def __init__(self, cache_dir: str = ".video_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        if self.index_file.exists():
            return json.loads(self.index_file.read_text())
        return {}

    def _save_index(self):
        self.index_file.write_text(json.dumps(self.index, indent=2))

    def _cache_key(self, prompt: str, model: str, duration: int) -> str:
        """Generate cache key from parameters."""
        data = f"{prompt}:{model}:{duration}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def get(self, prompt: str, model: str, duration: int) -> Optional[Dict]:
        """Get cached result if exists."""
        key = self._cache_key(prompt, model, duration)
        if key in self.index:
            entry = self.index[key]
            print(f"Cache hit: {key}")
            return entry
        return None

    def set(self, prompt: str, model: str, duration: int, result: Dict):
        """Cache a generation result."""
        key = self._cache_key(prompt, model, duration)
        self.index[key] = {
            "prompt": prompt,
            "model": model,
            "duration": duration,
            "video_url": result.get("video_url"),
            "job_id": result.get("job_id"),
            "cached_at": datetime.utcnow().isoformat()
        }
        self._save_index()
        print(f"Cached: {key}")

# Cached client wrapper
class CachedKlingAIClient:
    def __init__(self, api_key: str, cache: VideoCache):
        self.api_key = api_key
        self.cache = cache
        self.base_url = "https://api.klingai.com/v1"

    def generate(self, prompt: str, model: str = "kling-v1.5", duration: int = 5) -> Dict:
        # Check cache first
        cached = self.cache.get(prompt, model, duration)
        if cached:
            return cached

        # Generate new
        # ... generation code ...
        result = {"job_id": "...", "video_url": "..."}

        # Cache result
        self.cache.set(prompt, model, duration, result)

        return result
```
