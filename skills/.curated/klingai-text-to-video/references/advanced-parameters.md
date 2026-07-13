# Advanced Parameters

## Advanced Parameters

```python
def advanced_text_to_video(
    prompt: str,
    duration: int = 10,
    aspect_ratio: str = "16:9",
    model: str = "kling-v1.5",
    resolution: str = "1080p",
    frame_rate: int = 24,
    negative_prompt: str = None,
    seed: int = None,
    camera_motion: dict = None
) -> dict:
    """Generate video with advanced parameters."""

    payload = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "frame_rate": frame_rate
    }

    # Optional parameters
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt

    if seed is not None:
        payload["seed"] = seed

    if camera_motion:
        payload["camera_motion"] = camera_motion

    response = requests.post(
        "https://api.klingai.com/v1/videos/text2video",
        headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"},
        json=payload
    )
    return response.json()

# Usage with advanced parameters
result = advanced_text_to_video(
    prompt="A serene Japanese garden with cherry blossoms falling",
    duration=15,
    aspect_ratio="16:9",
    resolution="4k",
    frame_rate=30,
    negative_prompt="blurry, low quality, distorted",
    seed=42,  # For reproducibility
    camera_motion={
        "type": "slow_zoom",
        "direction": "in",
        "intensity": 0.3
    }
)
```
