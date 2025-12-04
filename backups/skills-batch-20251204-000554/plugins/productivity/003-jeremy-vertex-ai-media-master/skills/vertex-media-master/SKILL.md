---
name: Vertex AI Media Master
description: |
  Automatic activation for ALL Google Vertex AI multimodal operations - video processing, audio generation, image creation, and marketing campaigns.
  **TRIGGER PHRASES:**
  - "vertex ai", "gemini multimodal", "process video", "generate audio", "create images", "marketing campaign"
  - "imagen", "video understanding", "multimodal", "content generation", "media assets"
  **AUTO-INVOKES FOR:**
  - Video processing and understanding (up to 6 hours)
  - Audio generation and transcription
  - Image generation with Imagen 4
  - Marketing campaign automation
  - Social media content creation
  - Ad creative generation
  - Multimodal content workflows
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

# Vertex AI Media Master - Comprehensive Multimodal AI Operations

This Agent Skill provides comprehensive mastery of Google Vertex AI multimodal capabilities for video, audio, image, and text processing with focus on marketing applications.

## Core Capabilities

### 🎥 Video Processing (Gemini 2.0/2.5)
- **Video Understanding**: Process videos up to 6 hours at low resolution or 2 hours at default resolution
- **2M Context Window**: Gemini 2.5 Pro handles massive video content
- **Audio Track Processing**: Automatic audio transcription from video
- **Multi-video Analysis**: Process multiple videos in single request
- **Video Summarization**: Extract key moments, scenes, and insights
- **Marketing Use Cases**:
  - Analyze competitor video ads
  - Extract highlights from long-form content
  - Generate video summaries for social media
  - Transcribe and caption video content
  - Identify brand mentions and product placements

### 🎵 Audio Generation & Processing
- **Lyria Model (2025)**: Native audio and music generation
- **Speech-to-Text**: Transcribe audio with speaker diarization
- **Text-to-Speech**: Generate natural voiceovers
- **Music Composition**: Background music for campaigns
- **Audio Enhancement**: Noise reduction and quality improvement
- **Marketing Use Cases**:
  - Generate podcast scripts and voiceovers
  - Create audio ads and radio spots
  - Produce background music for video campaigns
  - Transcribe customer interviews
  - Generate multilingual voiceovers

### 🖼️ Image Generation (Imagen 4 & Gemini 2.5 Flash Image)
- **Imagen 4**: Highest quality text-to-image generation
- **Gemini 2.5 Flash Image**: Interleaved image generation with text
- **Style Transfer**: Apply brand styles to generated images
- **Product Visualization**: Generate product mockups
- **Campaign Assets**: Create ad creatives and social media graphics
- **Marketing Use Cases**:
  - Generate personalized ad images (Adios solution)
  - Create social media graphics at scale
  - Produce product lifestyle images
  - Generate A/B test variations
  - Create branded campaign visuals

### 📢 Marketing Campaign Automation
- **ViGenAiR**: Convert long-form video ads to short formats automatically
- **Adios**: Generate personalized ad images tailored to audience context
- **Campaign Asset Generation**: Photos, soundtracks, voiceovers from prompts
- **Content Pipeline**: Email copy, blog posts, social media, PMax assets
- **Catalog Enrichment**: Multi-agent workflow for product onboarding
- **Marketing Use Cases**:
  - Automated campaign asset production
  - Personalized content at scale
  - Multi-channel content distribution
  - Product catalog enhancement
  - Visual merchandising automation

### 🔧 Technical Implementation

**API Integration:**
```python
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel

# Initialize Vertex AI
aiplatform.init(project="your-project", location="us-central1")

# Gemini 2.5 Pro for video
model = GenerativeModel("gemini-2.5-pro")

# Process video with audio
response = model.generate_content([
    "Analyze this video and extract key marketing insights",
    video_file,  # Up to 6 hours
])

# Imagen 4 for image generation
from vertexai.preview.vision_models import ImageGenerationModel
imagen = ImageGenerationModel.from_pretrained("imagen-4")
images = imagen.generate_images(
    prompt="Professional product photo, studio lighting, white background",
    number_of_images=4
)
```

**Gemini 2.5 Flash Image (Interleaved Generation):**
```python
# Generate images within text responses
model = GenerativeModel("gemini-2.5-flash-image")
response = model.generate_content([
    "Create a 5-step recipe with images for each step"
])
# Returns text + images interleaved
```

**Audio Generation (Lyria):**
```python
from vertexai.preview.audio_models import AudioGenerationModel
lyria = AudioGenerationModel.from_pretrained("lyria")
audio = lyria.generate_audio(
    prompt="Upbeat background music for product launch video, 30 seconds",
    duration=30
)
```

### 📊 Marketing Workflow Automation

**1. Multi-Channel Campaign Creation:**
```python
# Single prompt generates all assets
campaign = model.generate_content([
    """Create a product launch campaign for [product]:
    - Hero image (1920x1080)
    - 3 social media graphics (1080x1080)
    - 30-second video script
    - Background music description
    - Email marketing copy
    - Instagram caption"""
])
```

**2. Video Repurposing Pipeline:**
```python
# Long-form to short-form conversion (ViGenAiR approach)
long_video = "gs://bucket/original-ad-60s.mp4"
response = model.generate_content([
    f"Extract 3 engaging 15-second clips from this video for TikTok/Reels",
    long_video
])
# Auto-generates format-specific versions
```

**3. Personalized Ad Generation:**
```python
# Context-aware image generation (Adios approach)
for audience in audiences:
    ad_image = imagen.generate_images(
        prompt=f"Product ad for {product}, targeting {audience.demographics}, {audience.style_preference}",
        aspect_ratio="16:9"
    )
```

### 🎯 Best Practices for Jeremy

**1. Project Setup:**
```bash
# Set environment variables
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"

# Install SDK
pip install google-cloud-aiplatform[vision,audio] google-generativeai
```

**2. Rate Limits & Quotas:**
- Gemini 2.5 Pro: 2M tokens/min (video processing)
- Imagen 4: 100 images/min
- Monitor usage in Cloud Console

**3. Cost Optimization:**
- Use Gemini 2.5 Flash for faster, cheaper operations
- Batch image generation requests
- Cache video embeddings for repeated analysis
- Use low-resolution video setting when appropriate

**4. Security & Compliance:**
- Keep API keys in Secret Manager, never in code
- Use service accounts with minimal permissions
- Enable VPC Service Controls for data residency
- Log all API calls for audit trails

### 🚀 Advanced Marketing Use Cases

**1. Campaign Performance Analysis:**
```python
# Analyze competitor campaigns
competitor_videos = ["gs://bucket/competitor1.mp4", "gs://bucket/competitor2.mp4"]
analysis = model.generate_content([
    "Compare these competitor videos: themes, messaging, CTAs, production quality",
    *competitor_videos
])
```

**2. Content Localization:**
```python
# Generate multilingual campaigns
for lang in ["en", "es", "fr", "de", "ja"]:
    localized_content = model.generate_content([
        f"Translate and culturally adapt this campaign for {lang} market:",
        campaign_brief,
        hero_image
    ])
```

**3. A/B Test Generation:**
```python
# Generate variations automatically
variations = []
for style in ["minimalist", "bold", "luxury", "playful"]:
    variation = imagen.generate_images(
        prompt=f"Product ad, {style} style, {brand_guidelines}",
        number_of_images=1
    )
    variations.append(variation)
```

### 📚 Reference Documentation

**Official Documentation:**
- Vertex AI Multimodal: https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/overview
- Gemini 2.5 Pro: https://cloud.google.com/vertex-ai/generative-ai/docs/models
- Imagen 4: https://cloud.google.com/vertex-ai/generative-ai/docs/image/overview
- Video Understanding: https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/video-understanding

**Marketing Solutions:**
- GenAI for Marketing: https://github.com/GoogleCloudPlatform/genai-for-marketing
- ViGenAiR (video repurposing)
- Adios (personalized ad images)

**Pricing:**
- Gemini 2.5 Pro: $3.50/1M input tokens, $10.50/1M output tokens
- Imagen 4: $0.04/image
- Video processing: Included in Gemini token pricing

## When This Skill Activates

This skill automatically activates when you mention:
- Video processing, analysis, or understanding
- Audio generation, music composition, or voiceovers
- Image generation, ad creatives, or visual content
- Marketing campaigns, content automation, or asset production
- Gemini multimodal capabilities
- Vertex AI media operations
- Social media content, email marketing, or PMax campaigns

## Integration with Other Tools

**Google Cloud Services:**
- Cloud Storage for media asset management
- BigQuery for campaign analytics
- Cloud Functions for automation triggers
- Vertex AI Pipelines for content workflows

**Third-Party Integrations:**
- Social media APIs (LinkedIn, Twitter, Instagram)
- Marketing automation platforms (HubSpot, Marketo)
- CMS integrations (WordPress, Contentful)
- DAM systems (Bynder, Cloudinary)

## Success Metrics

**Track These KPIs:**
- Asset generation speed (baseline: 5 images/min)
- Content approval rate (target: >80%)
- Campaign personalization scale (target: 1000+ variants)
- Cost per asset (target: <$0.10/image)
- Time saved vs manual production (target: 90% reduction)

---

**This skill makes Jeremy a Vertex AI multimodal expert with instant access to video processing, audio generation, image creation, and marketing automation capabilities.**
