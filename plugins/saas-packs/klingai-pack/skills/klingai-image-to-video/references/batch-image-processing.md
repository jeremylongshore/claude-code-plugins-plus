# Batch Image Processing

## Batch Image Processing

```python
async def batch_image_to_video(
    client: KlingAIImageToVideo,
    images: list,
    default_prompt: str,
    **kwargs
) -> list:
    """Process multiple images to videos."""
    import asyncio

    results = []

    for image_path in images:
        params = ImageToVideoParams(
            image_path=image_path,
            prompt=default_prompt,
            **kwargs
        )

        try:
            result = client.generate(params)
            results.append({
                "image": image_path,
                "job_id": result["job_id"],
                "status": "submitted"
            })
            print(f"Submitted: {image_path} -> {result['job_id']}")
        except Exception as e:
            results.append({
                "image": image_path,
                "error": str(e),
                "status": "failed"
            })
            print(f"Failed: {image_path} - {e}")

        # Rate limiting
        await asyncio.sleep(2)

    return results

# Usage
images = ["image1.jpg", "image2.jpg", "image3.jpg"]
results = asyncio.run(batch_image_to_video(
    client,
    images,
    default_prompt="The scene gently comes to life",
    duration=5,
    motion_strength=0.5
))
```
