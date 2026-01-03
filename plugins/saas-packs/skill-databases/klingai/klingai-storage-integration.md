# klingai-storage-integration

> Integrate Kling AI video output with cloud storage

## Directory Structure

```
klingai-storage-integration/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 s3_uploader.py          # AWS S3 integration
    ├── 🐍 gcs_uploader.py         # Google Cloud Storage integration
    └── 🐍 azure_uploader.py       # Azure Blob Storage integration
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with cloud storage integration guide |
| `s3_uploader.py` | 🐍 Python | Upload videos to AWS S3 |
| `gcs_uploader.py` | 🐍 Python | Upload videos to Google Cloud Storage |
| `azure_uploader.py` | 🐍 Python | Upload videos to Azure Blob Storage |

## Summary

**Category:** cicd
**Target Audience:** Developer storing videos
**Trigger Phrases:** `klingai storage`, `kling ai s3`, `klingai gcs`, `save klingai video`, `klingai cloud storage`

### What This Skill Does

This skill integrates Kling AI video output with cloud storage providers. It covers:

- Video download from Kling AI temporary URLs
- Upload to S3, GCS, or Azure Blob Storage
- Signed URL generation for access
- Metadata tagging and organization
- Lifecycle policies for cost management
- CDN integration for delivery

### Technical Success Criteria

- Videos downloaded and stored with signed URLs
- Proper metadata and organization
- Lifecycle policies configured

### Business Success Criteria

- Permanent video storage with access control
- Cost-effective storage tier selection
- Fast video delivery via CDN

## Related Skills

- `klingai-async-workflows` - Storage step in workflows
- `klingai-ci-integration` - Storage in CI pipelines
- `klingai-cost-controls` - Storage cost management
