# Style Transfer Implementation

## Style Transfer Implementation

```python
import requests
import os
from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum
import base64

class VideoStyle(Enum):
    # Artistic
    ANIME = "anime"
    OIL_PAINTING = "oil_painting"
    WATERCOLOR = "watercolor"
    SKETCH = "sketch"
    PIXEL_ART = "pixel_art"
    COMIC_BOOK = "comic_book"

    # Cinematic
    NOIR = "noir"
    VINTAGE = "vintage"
    CYBERPUNK = "cyberpunk"
    FANTASY = "fantasy"

    # Color
    WARM = "warm"
    COOL = "cool"
    VIBRANT = "vibrant"
    MUTED = "muted"

    # Default
    REALISTIC = "realistic"

@dataclass
class StyleSettings:
    primary_style: VideoStyle
    style_strength: float = 0.7  # 0.0 to 1.0
    secondary_style: Optional[VideoStyle] = None
    color_palette: Optional[str] = None
    reference_image: Optional[str] = None  # Base64 or URL

class KlingAIStyleTransfer:
    """Apply artistic styles to video generation."""

    # Style prompt modifiers
    STYLE_PROMPTS = {
        VideoStyle.ANIME: "in anime style, vibrant colors, clean lines, expressive",
        VideoStyle.OIL_PAINTING: "oil painting style, visible brushstrokes, rich textures",
        VideoStyle.WATERCOLOR: "watercolor painting, soft edges, flowing colors, delicate",
        VideoStyle.SKETCH: "pencil sketch style, detailed line work, shading",
        VideoStyle.PIXEL_ART: "pixel art style, 16-bit aesthetic, blocky pixels",
        VideoStyle.COMIC_BOOK: "comic book style, bold outlines, halftone dots",
        VideoStyle.NOIR: "film noir style, high contrast, black and white, dramatic shadows",
        VideoStyle.VINTAGE: "vintage film look, film grain, muted colors, nostalgic",
        VideoStyle.CYBERPUNK: "cyberpunk aesthetic, neon lights, futuristic, dark atmosphere",
        VideoStyle.FANTASY: "fantasy style, magical, ethereal lighting, mystical",
        VideoStyle.WARM: "warm color grading, golden tones, sunset palette",
        VideoStyle.COOL: "cool color grading, blue tones, twilight palette",
        VideoStyle.VIBRANT: "vibrant saturated colors, high contrast, bold",
        VideoStyle.MUTED: "muted desaturated colors, soft contrast, understated",
        VideoStyle.REALISTIC: "photorealistic, natural lighting, detailed",
    }

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ["KLINGAI_API_KEY"]
        self.base_url = "https://api.klingai.com/v1"

    def apply_style(
        self,
        prompt: str,
        style: StyleSettings,
        duration: int = 5,
        model: str = "kling-v1.5"
    ) -> Dict:
        """Generate video with applied style."""
        # Build styled prompt
        styled_prompt = self._build_styled_prompt(prompt, style)

        request_body = {
            "prompt": styled_prompt,
            "duration": duration,
            "model": model,
        }

        # Add style parameters if API supports
        if style.style_strength != 0.7:
            request_body["style_strength"] = style.style_strength

        # Add reference image if provided
        if style.reference_image:
            request_body["style_reference"] = style.reference_image

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

    def _build_styled_prompt(self, prompt: str, style: StyleSettings) -> str:
        """Build prompt with style modifiers."""
        parts = [prompt]

        # Add primary style
        if style.primary_style in self.STYLE_PROMPTS:
            parts.append(self.STYLE_PROMPTS[style.primary_style])

        # Add secondary style (lower weight)
        if style.secondary_style and style.secondary_style in self.STYLE_PROMPTS:
            parts.append(f"with hints of {self.STYLE_PROMPTS[style.secondary_style]}")

        # Add color palette
        if style.color_palette:
            parts.append(f"color palette: {style.color_palette}")

        return ", ".join(parts)

    def generate_style_variations(
        self,
        prompt: str,
        styles: List[VideoStyle],
        duration: int = 5
    ) -> List[Dict]:
        """Generate same prompt in multiple styles."""
        results = []

        for style in styles:
            settings = StyleSettings(primary_style=style)
            result = self.apply_style(prompt, settings, duration)

            results.append({
                "style": style.value,
                "job_id": result["job_id"],
                "prompt": self._build_styled_prompt(prompt, settings)
            })

            print(f"Generated {style.value} style: {result['job_id']}")

        return results

# Usage
style_transfer = KlingAIStyleTransfer()

# Single style
style = StyleSettings(
    primary_style=VideoStyle.ANIME,
    style_strength=0.8
)

result = style_transfer.apply_style(
    prompt="A samurai standing on a hill at sunset",
    style=style,
    duration=5
)

# Multiple styles
variations = style_transfer.generate_style_variations(
    prompt="A peaceful garden with a koi pond",
    styles=[VideoStyle.ANIME, VideoStyle.WATERCOLOR, VideoStyle.REALISTIC]
)
```
