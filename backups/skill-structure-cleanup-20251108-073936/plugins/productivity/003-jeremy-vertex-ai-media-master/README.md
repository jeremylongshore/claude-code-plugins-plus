# Vertex AI Media Master - Jeremy's Multimodal AI Powerhouse

**Comprehensive Google Vertex AI multimodal mastery for video processing, audio generation, image creation, and marketing automation.**

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](plugin.json)
[![Category](https://img.shields.io/badge/category-productivity-green)](https://github.com/jeremylongshore/claude-code-plugins)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-Vertex_AI-4285F4?logo=google-cloud)](https://cloud.google.com/vertex-ai)

## 🎯 Purpose

This plugin makes Claude Code an expert in Google Vertex AI's multimodal capabilities, with automatic activation for video, audio, image, and text processing workflows focused on marketing applications.

## ✨ Key Features

### 🎥 Video Processing (Gemini 2.0/2.5)
- Process videos up to **6 hours** at low resolution
- 2M context window for massive content
- Multi-video analysis in single requests
- Audio track transcription and analysis
- Marketing insights extraction

### 🎵 Audio Generation (Lyria Model)
- Background music composition
- Voiceover generation
- Speech-to-text transcription
- Audio ads and radio spots
- Multilingual voiceovers

### 🖼️ Image Generation (Imagen 4)
- Highest quality text-to-image
- Interleaved image generation with Gemini 2.5 Flash Image
- Personalized ad images (Adios approach)
- Product visualization
- Campaign asset generation

### 📢 Marketing Automation
- **ViGenAiR**: Convert long videos to short formats automatically
- **Adios**: Generate personalized ad images
- Multi-channel campaign creation
- Content pipeline automation
- Product catalog enrichment

## 🚀 Installation

```bash
# Install the plugin
/plugin install 003-jeremy-vertex-ai-media-master@claude-code-plugins-plus
```

## 📋 Components

### Agent Skills (1)
- **vertex-media-master** - Auto-activates for all Vertex AI multimodal operations

### Slash Commands (1)
- `/vertex-campaign` - Generate complete multimodal marketing campaigns

## 💡 Usage Examples

### Generate Marketing Campaign
```bash
/vertex-campaign

Product: Premium wireless earbuds
Audience: Fitness enthusiasts, 25-40
Goal: Product launch
Budget: $30K
```

**Generates:**
- 15+ product images
- Video scripts (multiple lengths)
- Background music
- Email sequences
- Social media content
- Blog posts
- Ad copy

### Process Long-Form Video
```
"Analyze this 4-hour webinar video and extract key highlights for social media clips"
```

**Auto-activates skill and:**
- Processes full video (up to 6 hours)
- Extracts key moments
- Generates short-form clips
- Creates captions
- Suggests distribution strategy

### Generate Personalized Ads
```
"Create 50 variations of this product ad, personalized for different audience segments"
```

**Auto-generates:**
- Demographic-specific imagery
- Localized copy
- Platform-optimized formats
- A/B test variations

## 🔧 Technical Implementation

### Prerequisites
```bash
# Google Cloud setup
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Install SDK
pip install google-cloud-aiplatform[vision,audio] google-generativeai
```

### API Integration
```python
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel

# Initialize
aiplatform.init(project="your-project", location="us-central1")

# Gemini 2.5 Pro for video
model = GenerativeModel("gemini-2.5-pro")
response = model.generate_content([
    "Analyze this video for marketing insights",
    video_file  # Up to 6 hours
])
```

## 🎯 Marketing Use Cases

### 1. Campaign Asset Production
- Generate all assets from single brief
- Consistent brand messaging
- Multi-channel distribution
- Cost: ~$5-7 per campaign

### 2. Video Repurposing
- Long-form to short-form conversion
- Platform-specific formatting
- Automatic captioning
- Highlight extraction

### 3. Personalized Content at Scale
- Audience-specific variations
- Localized campaigns
- Dynamic product placement
- Real-time adaptation

### 4. Content Automation Pipeline
- Scheduled asset generation
- Approval workflows
- Multi-language support
- Performance tracking

## 💰 Cost Optimization

**Pricing:**
- Gemini 2.5 Pro: $3.50/1M input tokens
- Imagen 4: $0.04/image
- Lyria audio: Variable by duration

**Best Practices:**
- Use Gemini Flash for faster ops
- Batch image requests
- Cache video embeddings
- Monitor quota usage

## 📊 Success Metrics

**Track:**
- Asset generation speed (target: 5 images/min)
- Content approval rate (target: >80%)
- Personalization scale (target: 1000+ variants)
- Cost per asset (target: <$0.10/image)
- Time savings (target: 90% vs manual)

## 🔗 Integration Points

**Google Cloud Services:**
- Cloud Storage (asset management)
- BigQuery (analytics)
- Cloud Functions (automation)
- Vertex AI Pipelines (workflows)

**Marketing Platforms:**
- Google Ads (PMax)
- Meta Business Suite
- LinkedIn Campaign Manager
- HubSpot/Marketo
- WordPress/Contentful

## 📚 Documentation

**Official Resources:**
- [Vertex AI Multimodal](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/overview)
- [Gemini Models](https://cloud.google.com/vertex-ai/generative-ai/docs/models)
- [Imagen 4](https://cloud.google.com/vertex-ai/generative-ai/docs/image/overview)
- [GenAI for Marketing](https://github.com/GoogleCloudPlatform/genai-for-marketing)

## 🎓 Training Resources

**Learn:**
- Video understanding with Gemini
- Image generation best practices
- Audio production workflows
- Marketing automation patterns
- Cost optimization techniques

## 🔒 Security & Compliance

- Store API keys in Secret Manager
- Use service accounts with minimal permissions
- Enable VPC Service Controls
- Log all API calls
- Comply with data residency requirements

## 🎯 When This Activates

**Trigger phrases:**
- "vertex ai", "gemini multimodal"
- "process video", "analyze video"
- "generate audio", "create images"
- "marketing campaign", "content generation"
- "imagen", "video understanding"

## 📈 Roadmap

**Planned features:**
- Gemini 2.5 Flash Thinking integration
- Real-time streaming capabilities
- Advanced A/B testing automation
- Predictive campaign optimization
- Multi-agent marketing orchestration

---

**Part of [Claude Code Plugins](https://github.com/jeremylongshore/claude-code-plugins)** - 234 production-ready plugins

**Author:** Jeremy Longshore | **License:** MIT | **Version:** 1.0.0
