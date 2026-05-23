# Shot Sequence Generator

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
