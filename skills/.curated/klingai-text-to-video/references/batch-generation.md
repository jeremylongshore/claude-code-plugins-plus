# Batch Generation

## Batch Generation

```python
import asyncio
import aiohttp

async def batch_text_to_video(prompts: list[str], **kwargs) -> list[dict]:
    """Generate multiple videos concurrently."""

    async def generate_one(session, prompt):
        async with session.post(
            "https://api.klingai.com/v1/videos/text2video",
            json={"prompt": prompt, **kwargs}
        ) as response:
            return await response.json()

    headers = {
        "Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [generate_one(session, p) for p in prompts]
        return await asyncio.gather(*tasks)

# Usage
prompts = [
    "A sunset over the ocean",
    "A city skyline at night",
    "A forest in autumn"
]

results = asyncio.run(batch_text_to_video(prompts, duration=5))
```
