# Camera Control Implementation

## Camera Control Implementation

```python
import requests
import os
from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum

class CameraMotion(Enum):
    # Basic
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"

    # Advanced
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    ORBIT_LEFT = "orbit_left"
    ORBIT_RIGHT = "orbit_right"
    CRANE_UP = "crane_up"
    CRANE_DOWN = "crane_down"

    # Static
    STATIC = "static"

@dataclass
class CameraSettings:
    motion: CameraMotion
    intensity: float = 0.5  # 0.0 to 1.0
    start_position: Optional[str] = None  # e.g., "center", "left", "right"
    end_position: Optional[str] = None
    ease_in: bool = True
    ease_out: bool = True

class KlingAICameraControl:
    """Advanced camera control for video generation."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ["KLINGAI_API_KEY"]
        self.base_url = "https://api.klingai.com/v1"

    def generate_with_camera(
        self,
        prompt: str,
        camera: CameraSettings,
        duration: int = 5,
        model: str = "kling-v1.5"
    ) -> Dict:
        """Generate video with specific camera settings."""
        request_body = {
            "prompt": prompt,
            "duration": duration,
            "model": model,
            "camera_motion": camera.motion.value,
            "camera_intensity": camera.intensity,
        }

        if camera.start_position:
            request_body["camera_start"] = camera.start_position
        if camera.end_position:
            request_body["camera_end"] = camera.end_position

        response = requests.post(
            f"{self.base_url}/videos/text-to-video",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=request_body
        )
        response.raise_for_status()
        return response.json()

    def generate_cinematic_sequence(
        self,
        scene_description: str,
        shots: List[Dict],
        transition_duration: float = 0.5
    ) -> List[Dict]:
        """Generate a sequence of shots with different camera movements."""
        results = []

        for i, shot in enumerate(shots):
            prompt = f"{scene_description}. {shot.get('action', '')}"

            camera = CameraSettings(
                motion=CameraMotion(shot.get("motion", "static")),
                intensity=shot.get("intensity", 0.5)
            )

            result = self.generate_with_camera(
                prompt=prompt,
                camera=camera,
                duration=shot.get("duration", 5)
            )

            results.append({
                "shot_number": i + 1,
                "job_id": result["job_id"],
                "motion": camera.motion.value,
                "description": shot.get("action", "")
            })

            print(f"Shot {i+1} submitted: {result['job_id']}")

        return results

# Usage
camera_control = KlingAICameraControl()

# Simple camera motion
camera = CameraSettings(
    motion=CameraMotion.ZOOM_IN,
    intensity=0.6
)

result = camera_control.generate_with_camera(
    prompt="A majestic mountain peak at sunrise",
    camera=camera,
    duration=5
)
```
