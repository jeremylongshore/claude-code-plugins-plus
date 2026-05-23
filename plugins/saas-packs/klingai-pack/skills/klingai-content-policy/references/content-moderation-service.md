# Content Moderation Service

## Content Moderation Service

```python
import requests
from typing import Optional, Dict

class ContentModerationService:
    """Service for content moderation with external API support."""

    def __init__(
        self,
        klingai_api_key: str,
        moderation_api_key: str = None,
        auto_reject: bool = True
    ):
        self.klingai_api_key = klingai_api_key
        self.moderation_api_key = moderation_api_key
        self.auto_reject = auto_reject
        self.filter = ContentFilter()

    def moderate_prompt(self, prompt: str) -> Dict:
        """Full moderation pipeline for prompts."""
        # Step 1: Local filter
        local_result = self.filter.check_prompt(prompt)

        if not local_result.passed and self.auto_reject:
            return {
                "approved": False,
                "stage": "local_filter",
                "category": local_result.category.value,
                "flags": local_result.flags,
                "message": local_result.message
            }

        # Step 2: External moderation API (optional)
        if self.moderation_api_key:
            external_result = self._check_external_api(prompt)
            if not external_result["safe"]:
                return {
                    "approved": False,
                    "stage": "external_moderation",
                    "category": "blocked",
                    "flags": external_result.get("categories", []),
                    "message": "Content flagged by moderation service."
                }

        return {
            "approved": True,
            "stage": "approved",
            "category": local_result.category.value,
            "flags": local_result.flags,
            "sanitized_prompt": local_result.sanitized_prompt,
            "message": "Content approved for generation."
        }

    def moderate_output(self, video_url: str, thumbnail_url: str = None) -> Dict:
        """Moderate generated video output."""
        # In production, this would analyze the actual video
        # For now, return placeholder

        return {
            "approved": True,
            "confidence": 0.95,
            "flags": [],
            "message": "Output passed moderation."
        }

    def _check_external_api(self, prompt: str) -> Dict:
        """Check prompt with external moderation API."""
        # Example using a hypothetical moderation API
        # In production, use OpenAI Moderation, AWS Comprehend, etc.

        try:
            response = requests.post(
                "https://api.moderation-service.com/v1/check",
                headers={"Authorization": f"Bearer {self.moderation_api_key}"},
                json={"text": prompt},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "safe": data.get("safe", True),
                    "categories": data.get("flagged_categories", [])
                }
        except Exception as e:
            # Fail open or closed based on policy
            print(f"Moderation API error: {e}")

        return {"safe": True, "categories": []}

    def generate_with_moderation(
        self,
        prompt: str,
        duration: int = 5,
        model: str = "kling-v1.5"
    ) -> Dict:
        """Generate video with full moderation pipeline."""
        # Pre-generation moderation
        pre_mod = self.moderate_prompt(prompt)

        if not pre_mod["approved"]:
            return {
                "status": "rejected",
                "stage": "pre_generation",
                "reason": pre_mod["message"],
                "flags": pre_mod["flags"]
            }

        # Use sanitized prompt if available
        final_prompt = pre_mod.get("sanitized_prompt", prompt)

        # Generate video
        response = requests.post(
            "https://api.klingai.com/v1/videos/text-to-video",
            headers={
                "Authorization": f"Bearer {self.klingai_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": final_prompt,
                "duration": duration,
                "model": model
            }
        )

        if response.status_code != 200:
            return {
                "status": "error",
                "stage": "generation",
                "reason": f"API error: {response.status_code}"
            }

        job_data = response.json()

        # Note: Post-generation moderation would happen after video completes

        return {
            "status": "submitted",
            "job_id": job_data["job_id"],
            "prompt_flags": pre_mod.get("flags", []),
            "original_prompt": prompt,
            "final_prompt": final_prompt
        }

# Usage
service = ContentModerationService(
    klingai_api_key=os.environ["KLINGAI_API_KEY"],
    auto_reject=True
)

# Check prompt before generation
result = service.moderate_prompt("A peaceful garden with butterflies")
print(f"Approved: {result['approved']}")

# Generate with moderation
result = service.generate_with_moderation(
    prompt="A beautiful mountain landscape at dawn",
    duration=5
)
```
