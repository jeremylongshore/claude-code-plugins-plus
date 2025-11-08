---
name: vertex-campaign
description: Generate complete multimodal marketing campaigns using Vertex AI - video, audio, images, copy for all channels
model: sonnet
---

# Generate Multimodal Marketing Campaign with Vertex AI

Create a comprehensive marketing campaign with all assets generated via Google Vertex AI multimodal capabilities.

## What This Does

1. **Campaign Brief Analysis**: Understand product, target audience, goals
2. **Asset Generation**: Create all required media assets
3. **Multi-Channel Content**: Generate content for all marketing channels
4. **Implementation Guide**: Provide deployment instructions

## Campaign Assets Generated

### Visual Assets (Imagen 4)
- Hero image (1920x1080)
- Social media graphics (Instagram, Facebook, LinkedIn)
- Display ad creatives (multiple sizes)
- Product lifestyle images
- A/B test variations

### Video Assets (Gemini 2.5 Pro)
- Video scripts (30s, 60s, 2min versions)
- Storyboard descriptions
- Video editing instructions
- Thumbnail designs

### Audio Assets (Lyria)
- Background music compositions
- Voiceover scripts
- Audio ad scripts
- Podcast episode outlines

### Written Content (Gemini 2.5 Pro)
- Email marketing sequences
- Blog post (SEO optimized)
- Social media captions
- PPC ad copy
- Landing page copy

## Usage

```bash
/vertex-campaign
```

Then provide campaign details:
- Product/service name
- Target audience
- Campaign objectives
- Brand guidelines
- Budget considerations

## Example Workflow

**Input:**
```
Product: Premium noise-canceling headphones
Audience: Remote workers, 25-45, tech-savvy
Goal: Product launch, 10K units in Q1
Budget: $50K
```

**Output:**
1. 15 product images (lifestyle, studio, use-cases)
2. 30s product launch video script
3. Background music track (energetic, professional)
4. Email sequence (5 emails)
5. Social media content (30 posts across platforms)
6. Blog post "Best Headphones for Remote Work 2025"
7. PPC campaigns (Google, Facebook, LinkedIn)

## Technical Implementation

**Step 1: Initialize Vertex AI**
```python
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel
from vertexai.preview.vision_models import ImageGenerationModel

aiplatform.init(project=PROJECT_ID, location="us-central1")
```

**Step 2: Generate Visual Assets**
```python
imagen = ImageGenerationModel.from_pretrained("imagen-4")
hero_image = imagen.generate_images(
    prompt=f"Professional product photography of {product}, studio lighting, clean background",
    number_of_images=1,
    aspect_ratio="16:9"
)
```

**Step 3: Create Video Script**
```python
gemini = GenerativeModel("gemini-2.5-pro")
video_script = gemini.generate_content([
    f"Create a 30-second video script for {product} targeting {audience}. Include scene descriptions, voiceover, music cues."
])
```

**Step 4: Generate Audio**
```python
from vertexai.preview.audio_models import AudioGenerationModel
lyria = AudioGenerationModel.from_pretrained("lyria")
background_music = lyria.generate_audio(
    prompt=f"Background music for {product} video ad, {mood}, 30 seconds",
    duration=30
)
```

**Step 5: Create Multi-Channel Copy**
```python
content = gemini.generate_content([
    f"""Generate marketing content for {product}:
    - 5-email drip campaign
    - 10 Instagram captions
    - 5 LinkedIn posts
    - SEO blog post (1500 words)
    - Google Ads copy (5 variations)"""
])
```

## Cost Estimation

**Per Campaign:**
- Visual Assets: $2-3 (50 images @ $0.04 each)
- Video Scripts: $0.50 (Gemini tokens)
- Audio: $1-2 (Lyria generation)
- Written Content: $1 (Gemini tokens)

**Total: ~$5-7 per complete campaign**

## Best Practices

1. **Brand Consistency**: Provide brand guidelines in prompt
2. **Batch Generation**: Generate multiple variations simultaneously
3. **Quality Control**: Review and iterate on generated assets
4. **Version Control**: Save prompts and outputs for reproducibility
5. **A/B Testing**: Generate 3-5 variations of each asset

## Integration with Marketing Stack

**Export to:**
- Google Ads (PMax campaigns)
- Meta Business Suite (Facebook/Instagram)
- LinkedIn Campaign Manager
- Email marketing platforms (HubSpot, Mailchimp)
- CMS platforms (WordPress, Contentful)

## Performance Tracking

**Monitor:**
- Asset generation time
- Cost per asset
- Approval rates
- Campaign performance metrics
- ROI vs traditional production

---

**This command turns Jeremy into a one-person marketing agency powered by Vertex AI multimodal capabilities.**
