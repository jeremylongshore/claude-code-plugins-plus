---
name: klingai-style-transfer
description: |
  Apply artistic styles to Kling AI video generation. Use when creating stylized videos,
  matching brand aesthetics, or artistic effects. Trigger with phrases like 'klingai style',
  'kling ai artistic', 'klingai video style', 'stylize klingai video'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Style Transfer

## Overview

This skill demonstrates applying artistic styles, visual effects, and aesthetic modifications to Kling AI video generation for unique creative outputs.

## Prerequisites

- Kling AI API key configured
- Reference images for style (optional)
- Python 3.8+

## Instructions

Follow these steps for style transfer:

1. **Define Style**: Choose or describe target aesthetic
2. **Prepare Reference**: Gather style reference images
3. **Craft Prompt**: Include style descriptors
4. **Generate Video**: Submit with style parameters
5. **Refine Output**: Iterate on style settings

## Style Categories

```
Kling AI Style Options:

ARTISTIC STYLES:
- anime: Japanese animation style
- oil_painting: Classical oil painting
- watercolor: Soft watercolor effect
- sketch: Pencil/charcoal drawing
- pixel_art: Retro pixel graphics
- comic_book: Bold comic style
- impressionist: Impressionist painting
- surrealist: Surrealist art style

CINEMATIC STYLES:
- noir: Black and white film noir
- vintage: Retro film look
- cyberpunk: Neon futuristic
- fantasy: Magical fantasy style
- documentary: Realistic documentary
- horror: Dark horror aesthetic

COLOR GRADING:
- warm: Warm color palette
- cool: Cool blue tones
- vibrant: Saturated colors
- muted: Desaturated palette
- monochrome: Single color tone
```

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

## Style Reference from Image

```python
def style_from_reference(
    style_transfer: KlingAIStyleTransfer,
    content_prompt: str,
    reference_image_path: str,
    style_strength: float = 0.7
) -> Dict:
    """Apply style from a reference image."""
    # Encode reference image
    with open(reference_image_path, "rb") as f:
        reference_b64 = base64.b64encode(f.read()).decode("utf-8")

    style = StyleSettings(
        primary_style=VideoStyle.REALISTIC,  # Let reference determine style
        style_strength=style_strength,
        reference_image=f"data:image/jpeg;base64,{reference_b64}"
    )

    return style_transfer.apply_style(
        prompt=f"{content_prompt}, matching the artistic style of the reference",
        style=style
    )

# Usage
result = style_from_reference(
    style_transfer,
    content_prompt="A city skyline at night",
    reference_image_path="van_gogh_starry_night.jpg",
    style_strength=0.8
)
```

## Brand Style Consistency

```python
@dataclass
class BrandStyle:
    name: str
    primary_colors: List[str]
    secondary_colors: List[str]
    mood: str
    visual_style: VideoStyle
    additional_modifiers: List[str]

class BrandStyleManager:
    """Manage consistent brand styles across videos."""

    def __init__(self, style_transfer: KlingAIStyleTransfer):
        self.style_transfer = style_transfer
        self.brands: Dict[str, BrandStyle] = {}

    def register_brand(self, brand: BrandStyle):
        """Register a brand style."""
        self.brands[brand.name] = brand

    def generate_brand_video(
        self,
        brand_name: str,
        content_prompt: str,
        duration: int = 5
    ) -> Dict:
        """Generate video matching brand style."""
        if brand_name not in self.brands:
            raise ValueError(f"Brand not registered: {brand_name}")

        brand = self.brands[brand_name]

        # Build brand-specific style
        color_palette = ", ".join(brand.primary_colors + brand.secondary_colors)

        style = StyleSettings(
            primary_style=brand.visual_style,
            style_strength=0.7,
            color_palette=color_palette
        )

        # Add brand modifiers to prompt
        branded_prompt = f"{content_prompt}, {brand.mood} mood"
        for modifier in brand.additional_modifiers:
            branded_prompt += f", {modifier}"

        return self.style_transfer.apply_style(branded_prompt, style, duration)

# Usage
manager = BrandStyleManager(style_transfer)

# Register brand
manager.register_brand(BrandStyle(
    name="TechCorp",
    primary_colors=["electric blue", "white"],
    secondary_colors=["silver", "dark gray"],
    mood="professional and innovative",
    visual_style=VideoStyle.CYBERPUNK,
    additional_modifiers=["clean lines", "futuristic", "high-tech"]
))

# Generate branded video
result = manager.generate_brand_video(
    brand_name="TechCorp",
    content_prompt="A product showcase of the latest smartphone",
    duration=5
)
```

## Output

Successful execution produces:
- Stylized video content
- Consistent brand aesthetics
- Artistic transformations
- Style variation comparisons

## Error Handling

Common errors and solutions:
1. **Style Not Applied**: Increase style_strength
2. **Conflicting Styles**: Use single primary style
3. **Color Mismatch**: Adjust color_palette explicitly

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Styles](https://docs.klingai.com/styles)
- [Color Theory](https://www.colormatters.com/color-and-design/basic-color-theory)
- [Visual Style Guide](https://www.canva.com/learn/visual-identity/)
