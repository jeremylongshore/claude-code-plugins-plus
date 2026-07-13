# Examples

## Example 1: Analyze a Marketing Video with Gemini 2.5 Pro

Extract structured insights from a competitor video to inform campaign strategy.

**Setup:**

```python
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, Part

aiplatform.init(project="my-project", location="us-central1")
model = GenerativeModel("gemini-2.5-pro")
```

**Video analysis request:**

```python
video_part = Part.from_uri(
    uri="gs://marketing-assets/competitor-ad-q1-2026.mp4",
    mime_type="video/mp4"
)

prompt = """Analyze this marketing video and return a JSON object with:
- scenes: array of {timestamp, description, visual_style, text_overlays}
- calls_to_action: array of CTA text with timestamps
- messaging_themes: top 3 themes with evidence
- production_techniques: camera work, transitions, color grading
- target_audience: inferred demographics and psychographics
- competitive_positioning: what claims are made vs competitors"""

response = model.generate_content([video_part, prompt])
analysis = response.text
```

**Output:**

```json
{
  "scenes": [
    {
      "timestamp": "0:00-0:08",
      "description": "Product hero shot with slow zoom",
      "visual_style": "High contrast, warm tones, shallow depth of field",
      "text_overlays": ["Introducing the Next Generation"]
    },
    {
      "timestamp": "0:08-0:22",
      "description": "Split-screen comparison: old vs new product",
      "visual_style": "Side-by-side, clean white background",
      "text_overlays": ["3x Faster", "50% Smaller"]
    },
    {
      "timestamp": "0:22-0:45",
      "description": "User testimonial montage, 4 speakers",
      "visual_style": "Natural lighting, casual settings",
      "text_overlays": ["Real users, real results"]
    },
    {
      "timestamp": "0:45-0:60",
      "description": "Product lineup with pricing",
      "visual_style": "Dark background, spotlight effect",
      "text_overlays": ["Starting at $29/mo", "Try Free for 14 Days"]
    }
  ],
  "calls_to_action": [
    {"text": "Try Free for 14 Days", "timestamp": "0:52"},
    {"text": "Visit example.com/start", "timestamp": "0:57"}
  ],
  "messaging_themes": [
    "Performance improvement (3x faster)",
    "Social proof via testimonials",
    "Low barrier to entry (free trial + low price)"
  ],
  "target_audience": "Small business owners, 30-50, tech-comfortable but not developers"
}
```

## Example 2: Generate Campaign Hero Images with Imagen 4

Create multiple brand-consistent hero image variations for a product launch.

**Generate hero images:**

```python
from vertexai.preview.vision_models import ImageGenerationModel

imagen = ImageGenerationModel.from_pretrained("imagen-4.0")

# Generate 4 variations
response = imagen.generate_images(
    prompt=(
        "Professional product photography of a modern smart home device "
        "on a clean white desk, warm natural lighting from the left, "
        "shallow depth of field, minimalist aesthetic, 8K quality"
    ),
    number_of_images=4,
    aspect_ratio="16:9",
    safety_filter_level="block_some",
    person_generation="dont_allow"
)

# Save generated images
for i, image in enumerate(response.images):
    image.save(f"output/hero-image-v{i+1}.png")
    print(f"Saved hero-image-v{i+1}.png ({image.size[0]}x{image.size[1]})")
```

**Output:**

```
Saved hero-image-v1.png (1920x1080)
Saved hero-image-v2.png (1920x1080)
Saved hero-image-v3.png (1920x1080)
Saved hero-image-v4.png (1920x1080)
```

**Generate social media crops:**

```python
# Instagram square
response_square = imagen.generate_images(
    prompt=(
        "Same smart home device, centered composition, "
        "warm lighting, clean background"
    ),
    number_of_images=2,
    aspect_ratio="1:1"
)

# Story/Reel vertical
response_vertical = imagen.generate_images(
    prompt=(
        "Smart home device with lifestyle context, person's hand "
        "interacting with device, vertical composition"
    ),
    number_of_images=2,
    aspect_ratio="9:16",
    person_generation="allow_adult"
)
```

## Example 3: Generate Background Music with Lyria

Create a custom background track for a promotional video.

**Music generation:**

```python
from vertexai.preview.audio_models import MusicGenerationModel

lyria = MusicGenerationModel.from_pretrained("lyria-1.0")

response = lyria.generate_music(
    prompt=(
        "Upbeat corporate background music, positive and inspiring, "
        "moderate tempo 120 BPM, acoustic guitar and light percussion, "
        "suitable for a tech product launch video, no vocals"
    ),
    duration_seconds=30,
    sample_rate=44100,
    output_format="wav"
)

response.audio.save("output/background-track.wav")
print(f"Generated {response.duration_seconds}s audio track")
```

**Output metadata:**

```json
{
  "file": "output/background-track.wav",
  "duration": 30.0,
  "sampleRate": 44100,
  "format": "wav",
  "fileSize": "5.3 MB",
  "model": "lyria-1.0",
  "prompt": "Upbeat corporate background music..."
}
```

## Example 4: Multi-Asset Campaign Generation Pipeline

Orchestrate multiple models to produce a complete campaign asset package
from a single product brief.

**Campaign brief:**

```python
brief = """
Product: CloudSync Pro — cloud storage for teams
Target: Small businesses, 5-50 employees
Tone: Professional but approachable
Key message: "Your files, everywhere, instantly"
Assets needed:
  - 4 hero images (16:9)
  - 2 social media images (1:1)
  - 1 background music track (15 seconds)
  - Ad copy in English, Spanish, French
  - Email subject lines (5 variations)
"""
```

**Pipeline execution:**

```python
import asyncio
from pathlib import Path

output_dir = Path("campaign-assets/cloudsync-pro")
output_dir.mkdir(parents=True, exist_ok=True)

# Step 1: Generate images (parallel)
async def generate_images():
    # Hero images
    hero_response = imagen.generate_images(
        prompt="Modern cloud storage app interface on laptop and phone, "
               "team collaboration, clean blue and white design",
        number_of_images=4,
        aspect_ratio="16:9"
    )
    for i, img in enumerate(hero_response.images):
        img.save(output_dir / f"hero-{i+1}.png")

    # Social images
    social_response = imagen.generate_images(
        prompt="Cloud storage icon with team avatars, "
               "minimalist flat design, bright colors",
        number_of_images=2,
        aspect_ratio="1:1"
    )
    for i, img in enumerate(social_response.images):
        img.save(output_dir / f"social-{i+1}.png")

# Step 2: Generate music
async def generate_music():
    music_response = lyria.generate_music(
        prompt="Light upbeat tech background, 15 seconds, "
               "clean electronic, subtle bass, no vocals",
        duration_seconds=15
    )
    music_response.audio.save(output_dir / "bg-track.wav")

# Step 3: Generate copy with Gemini
async def generate_copy():
    model = GenerativeModel("gemini-2.5-pro")
    copy_prompt = f"""Based on this product brief, generate:
1. Ad copy for Facebook, Instagram, LinkedIn (each under 150 chars)
2. Email subject lines (5 variations, under 60 chars each)
3. Translate ad copy to Spanish and French

Brief: {brief}

Return as JSON."""

    response = model.generate_content(copy_prompt)
    with open(output_dir / "campaign-copy.json", "w") as f:
        f.write(response.text)

# Run all in parallel
async def main():
    await asyncio.gather(
        generate_images(),
        generate_music(),
        generate_copy()
    )

asyncio.run(main())
```

**Output directory:**

```
campaign-assets/cloudsync-pro/
├── hero-1.png         (1920x1080)
├── hero-2.png         (1920x1080)
├── hero-3.png         (1920x1080)
├── hero-4.png         (1920x1080)
├── social-1.png       (1080x1080)
├── social-2.png       (1080x1080)
├── bg-track.wav       (15s, 44.1kHz)
└── campaign-copy.json (multi-language ad copy + subject lines)
```

## Example 5: Video Clip Extraction for Short-Form Content

Identify the most engaging segments of a long-form video for repurposing
as short-form content (TikTok, Reels, Shorts).

**Analysis request:**

```python
video = Part.from_uri(
    uri="gs://content-library/product-demo-full.mp4",
    mime_type="video/mp4"
)

prompt = """Analyze this product demo video and identify the 3 most
engaging 15-second segments suitable for TikTok/Instagram Reels.

For each segment, provide:
- start_time and end_time (MM:SS format)
- hook: the attention-grabbing element in the first 2 seconds
- description: what happens in the segment
- suggested_caption: under 100 characters with hashtags
- engagement_score: 1-10 based on visual interest and information density

Return as JSON array sorted by engagement_score descending."""

response = model.generate_content([video, prompt])
```

**Output:**

```json
[
  {
    "start_time": "03:22",
    "end_time": "03:37",
    "hook": "Split-screen before/after transformation",
    "description": "Shows file sync completing in 0.3 seconds vs competitor's 12 seconds",
    "suggested_caption": "This is what real-time sync looks like. #CloudSync #Productivity",
    "engagement_score": 9
  },
  {
    "start_time": "07:45",
    "end_time": "08:00",
    "hook": "Surprise reaction from user",
    "description": "User discovers automatic version history saved their deleted project",
    "suggested_caption": "Version history just saved my entire project. #LifeSaver #CloudSync",
    "engagement_score": 8
  },
  {
    "start_time": "01:10",
    "end_time": "01:25",
    "hook": "Rapid-fire feature montage",
    "description": "5 key features shown in quick succession with smooth transitions",
    "suggested_caption": "5 features you didn't know you needed. #CloudSync #TechTips",
    "engagement_score": 7
  }
]
```

## Example 6: Brand Asset Validation

Use Gemini to verify generated assets conform to brand guidelines.

```python
brand_guidelines = """
Brand colors: Blue (#1E40AF), White (#FFFFFF), Light Gray (#F3F4F6)
Typography: Inter font family
Logo placement: Top-left corner, minimum 48px from edges
Prohibited: Red tones, dark backgrounds, stock photo cliches
Required: Product name visible, clean minimalist aesthetic
"""

# Validate each generated hero image
for i in range(1, 5):
    image_part = Part.from_uri(
        uri=f"gs://campaign-assets/hero-{i}.png",
        mime_type="image/png"
    )

    validation_prompt = f"""Review this marketing image against brand guidelines:

{brand_guidelines}

Score each criterion (pass/fail) and provide overall compliance score (0-100).
Flag any violations with specific descriptions."""

    result = model.generate_content([image_part, validation_prompt])
    print(f"Hero image {i}: {result.text}")
```

**Validation output:**

```
Hero image 1: Score 92/100
  ✓ Color palette matches brand (blue and white dominant)
  ✓ Clean minimalist aesthetic
  ✓ Product name visible
  ✗ Minor: slight warm tone in background (-8 points)
  Recommendation: Adjust white balance to remove warm cast

Hero image 2: Score 98/100
  ✓ All criteria met
  ✗ Minor: logo could be 4px larger for readability (-2 points)
  Recommendation: Increase logo size slightly
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
