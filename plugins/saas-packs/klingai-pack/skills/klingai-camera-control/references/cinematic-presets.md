# Cinematic Presets

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
