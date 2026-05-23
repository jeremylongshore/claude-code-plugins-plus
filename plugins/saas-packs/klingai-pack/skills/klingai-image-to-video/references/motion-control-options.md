# Motion Control Options

## Motion Control Options

```python
# Motion strength examples
MOTION_PRESETS = {
    "subtle": 0.2,      # Very gentle, barely perceptible motion
    "light": 0.4,       # Light movement, good for portraits
    "moderate": 0.6,    # Standard animation level
    "dynamic": 0.8,     # Strong movement, good for action scenes
    "intense": 1.0      # Maximum motion, can be dramatic
}

# Camera motion options
CAMERA_MOTIONS = {
    "zoom_in": "Slowly zoom into the subject",
    "zoom_out": "Pull back from the subject",
    "pan_left": "Horizontal pan to the left",
    "pan_right": "Horizontal pan to the right",
    "tilt_up": "Vertical tilt upward",
    "tilt_down": "Vertical tilt downward",
    "orbit": "Circular motion around subject",
    "none": "No camera movement, only subject animation"
}

# Example: Generate with specific motion
params = ImageToVideoParams(
    image_path="landscape.jpg",
    prompt="Clouds drift across the sky, water ripples gently",
    duration=10,
    motion_strength=MOTION_PRESETS["moderate"],
    camera_motion="zoom_out"
)
```
