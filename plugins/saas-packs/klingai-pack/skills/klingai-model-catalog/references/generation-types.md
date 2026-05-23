# Generation Types

## Generation Types

### Text-to-Video

```python
def text_to_video(prompt: str, model: str = "kling-v1.5"):
    """Generate video from text prompt."""
    response = requests.post(
        "https://api.klingai.com/v1/videos/text2video",
        headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"},
        json={
            "model": model,
            "prompt": prompt,
            "duration": 10,
            "aspect_ratio": "16:9"
        }
    )
    return response.json()
```

### Image-to-Video

```python
def image_to_video(image_url: str, motion_prompt: str, model: str = "kling-v1.5"):
    """Animate an image into video."""
    response = requests.post(
        "https://api.klingai.com/v1/videos/image2video",
        headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"},
        json={
            "model": model,
            "image_url": image_url,
            "motion_prompt": motion_prompt,
            "duration": 5
        }
    )
    return response.json()
```

### Video Extension

```python
def extend_video(video_id: str, additional_seconds: int):
    """Extend an existing video (Pro only)."""
    response = requests.post(
        "https://api.klingai.com/v1/videos/extend",
        headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"},
        json={
            "model": "kling-pro",
            "source_video_id": video_id,
            "extend_duration": additional_seconds
        }
    )
    return response.json()
```
