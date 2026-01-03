---
name: klingai-camera-control
description: |
  Control camera movements in Kling AI video generation. Use when creating cinematic effects,
  dynamic shots, or specific camera movements. Trigger with phrases like 'klingai camera',
  'kling ai camera motion', 'klingai cinematic', 'klingai pan zoom'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Camera Control

## Overview

This skill demonstrates advanced camera control in Kling AI including pan, tilt, zoom, dolly, and complex camera movements for cinematic video generation.

## Prerequisites

- Kling AI API key configured
- Understanding of cinematography basics
- Python 3.8+

## Instructions

Follow these steps for camera control:

1. **Plan Shot**: Design camera movement
2. **Select Motion**: Choose camera motion type
3. **Configure Parameters**: Set motion intensity
4. **Generate Video**: Submit with camera settings
5. **Review Output**: Evaluate camera movement

## Camera Motion Types

```
Kling AI Camera Motions:

BASIC MOVEMENTS:
- zoom_in: Camera moves closer to subject
- zoom_out: Camera moves away from subject
- pan_left: Horizontal movement left
- pan_right: Horizontal movement right
- tilt_up: Vertical movement up
- tilt_down: Vertical movement down

ADVANCED MOVEMENTS:
- dolly_in: Camera physically moves forward
- dolly_out: Camera physically moves backward
- truck_left: Camera moves horizontally left
- truck_right: Camera moves horizontally right
- orbit_left: Circular motion around subject (left)
- orbit_right: Circular motion around subject (right)
- crane_up: Camera rises vertically
- crane_down: Camera lowers vertically

CINEMATIC PRESETS:
- establishing: Wide to close zoom
- reveal: Pan to reveal subject
- follow: Track moving subject
- dramatic_zoom: Rapid zoom effect
```

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

## Cinematic Presets

```python
class CinematicPresets:
    """Pre-configured camera movements for common cinematic effects."""

    @staticmethod
    def establishing_shot() -> CameraSettings:
        """Wide establishing shot that zooms in."""
        return CameraSettings(
            motion=CameraMotion.ZOOM_IN,
            intensity=0.4,
            start_position="wide",
            end_position="medium",
            ease_in=True,
            ease_out=True
        )

    @staticmethod
    def dramatic_reveal() -> CameraSettings:
        """Pan to reveal the subject dramatically."""
        return CameraSettings(
            motion=CameraMotion.PAN_RIGHT,
            intensity=0.7,
            ease_in=False,
            ease_out=True
        )

    @staticmethod
    def vertigo_effect() -> CameraSettings:
        """Dolly zoom (Hitchcock) effect."""
        return CameraSettings(
            motion=CameraMotion.DOLLY_OUT,
            intensity=0.8,
            # Combined with zoom in the prompt
        )

    @staticmethod
    def hero_entrance() -> CameraSettings:
        """Low angle crane up for hero shots."""
        return CameraSettings(
            motion=CameraMotion.CRANE_UP,
            intensity=0.5,
            start_position="low",
            end_position="eye_level"
        )

    @staticmethod
    def orbit_product() -> CameraSettings:
        """360-degree orbit for product showcase."""
        return CameraSettings(
            motion=CameraMotion.ORBIT_RIGHT,
            intensity=0.6,
        )

    @staticmethod
    def peaceful_static() -> CameraSettings:
        """Static shot for calm scenes."""
        return CameraSettings(
            motion=CameraMotion.STATIC,
            intensity=0.0
        )

# Usage
presets = CinematicPresets()

# Establishing shot
result = camera_control.generate_with_camera(
    prompt="A bustling city skyline at dusk",
    camera=presets.establishing_shot(),
    duration=5
)

# Dramatic reveal
result = camera_control.generate_with_camera(
    prompt="A hidden treasure chest in a dark cave",
    camera=presets.dramatic_reveal(),
    duration=5
)
```

## Shot Sequence Generator

```python
def generate_story_sequence(
    camera_control: KlingAICameraControl,
    story: str,
    style: str = "cinematic"
) -> List[Dict]:
    """Generate a complete story with varied camera work."""

    # Define shot sequence
    shots = [
        {
            "action": "Opening wide shot",
            "motion": "zoom_in",
            "intensity": 0.3,
            "duration": 5
        },
        {
            "action": "Character introduction",
            "motion": "pan_right",
            "intensity": 0.5,
            "duration": 5
        },
        {
            "action": "Action sequence",
            "motion": "dolly_in",
            "intensity": 0.7,
            "duration": 5
        },
        {
            "action": "Dramatic moment",
            "motion": "crane_up",
            "intensity": 0.6,
            "duration": 5
        },
        {
            "action": "Closing shot",
            "motion": "zoom_out",
            "intensity": 0.4,
            "duration": 5
        }
    ]

    return camera_control.generate_cinematic_sequence(
        scene_description=f"{style} style: {story}",
        shots=shots
    )

# Usage
sequence = generate_story_sequence(
    camera_control,
    story="A lone warrior approaches an ancient temple",
    style="epic fantasy"
)
```

## Camera Motion Combinations

```python
def combine_camera_motions(
    primary: CameraMotion,
    secondary: CameraMotion,
    primary_weight: float = 0.7
) -> str:
    """Create combined camera motion description for prompts."""
    combinations = {
        (CameraMotion.ZOOM_IN, CameraMotion.PAN_LEFT): "zoom in while panning left",
        (CameraMotion.ZOOM_OUT, CameraMotion.CRANE_UP): "pull back and rise up",
        (CameraMotion.DOLLY_IN, CameraMotion.TILT_UP): "move forward and look up",
        (CameraMotion.ORBIT_LEFT, CameraMotion.ZOOM_IN): "orbit around while closing in",
    }

    key = (primary, secondary)
    if key in combinations:
        return combinations[key]

    return f"{primary.value} with subtle {secondary.value}"

# Use in prompt engineering
camera_description = combine_camera_motions(
    CameraMotion.ZOOM_IN,
    CameraMotion.PAN_LEFT
)

prompt = f"A mystical forest clearing, camera {camera_description}"
```

## Output

Successful execution produces:
- Videos with controlled camera motion
- Cinematic shot sequences
- Professional camera movements
- Consistent visual storytelling

## Error Handling

Common errors and solutions:
1. **Motion Conflict**: Simplify to single motion
2. **Intensity Too High**: Reduce for smoother result
3. **Unnatural Movement**: Add easing options

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Camera Control](https://docs.klingai.com/camera)
- [Cinematography Basics](https://www.masterclass.com/articles/cinematography-techniques)
- [Camera Movement Guide](https://www.studiobinder.com/blog/camera-movement-types/)
