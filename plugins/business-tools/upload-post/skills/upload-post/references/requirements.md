# Media Requirements by Platform

## Photo Requirements

### Instagram
- Formats: JPEG, PNG, GIF
- Aspect ratio: 4:5 to 1.91:1
- Recommended: 1080x1350px (4:5)

### TikTok
- Formats: JPG, JPEG, WEBP only
- Use for photo slideshows with `auto_add_music`

### Facebook
- Formats: JPEG, PNG, GIF, WebP
- Max size: 10MB recommended

### X (Twitter)
- Formats: JPEG, PNG, GIF
- Max size: 5MB (images), 15MB (GIFs)
- Max 4 images per tweet

### LinkedIn
- Formats: JPEG, PNG, GIF
- Recommended: 1200x627px

### Threads
- Formats: JPEG, PNG
- Max size: 8MB
- Aspect ratio: 10:1 to 1:10
- Width: 320px min, 1440px max
- Color space: sRGB (auto-converted)

### Pinterest
- Formats: BMP, JPEG, PNG, TIFF, GIF, WebP
- Max size: 20MB
- Recommended: 1000x1500px (2:3)
- Min: 600x900px, Max: 2000x3000px
- Carousel: up to 5 images, same dimensions

### Reddit
- Formats: JPG, PNG, GIF, WEBP
- Max size: 10MB

### Bluesky
- Formats: JPEG, PNG, GIF, WebP
- Max size: 1MB per image
- Max 4 images per post
- Daily limit: 50 uploads (photos + videos)

## Video Requirements

### TikTok
- Formats: MP4, MOV, WebM
- Duration: 3s to 10min
- Max size: 4GB
- Recommended: 1080x1920 (9:16)
- Codec: H.264

### Instagram
- Formats: MP4, MOV
- Reels: 0-90s, 9:16 aspect
- Feed: up to 60s
- Max size: 4GB
- Codec: H.264, AAC audio

### YouTube
- Formats: MP4, MOV, AVI, WMV, FLV, WebM
- Max size: 256GB
- Max duration: 12 hours
- Recommended: 1920x1080 or 3840x2160

### LinkedIn
- Formats: MP4
- Duration: 3s to 10min
- Max size: 5GB
- Aspect: 1:2.4 to 2.4:1

### Facebook
- Formats: MP4, MOV
- Max size: 10GB
- Max duration: 240min
- Recommended: H.264, AAC

### X (Twitter)
- Formats: MP4, MOV
- Max size: 512MB
- Max duration: 140s (2min 20s)
- Codec: H.264

### Threads
- Formats: MP4, MOV
- Max duration: 5min
- Aspect: 9:16 recommended

### Pinterest
- Formats: MP4, MOV, M4V
- Duration: 4s to 15min
- Max size: 2GB
- Aspect: 1:2 to 1.91:1

### Bluesky
- Formats: MP4
- Max size: 50MB
- Max duration: 60s
- Daily limit: 50 uploads

## Document Requirements (LinkedIn only)

- Formats: PDF, PPT, PPTX, DOC, DOCX
- Max size: 100MB
- Max pages: 300

## FFmpeg Re-encoding

If videos fail platform validation, use the FFmpeg endpoint:

```bash
# Convert to H.264 MP4
ffmpeg -y -i {input} -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k {output}

# Resize to 1080p
ffmpeg -y -i {input} -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" -c:v libx264 -crf 23 {output}

# Convert to 9:16 vertical
ffmpeg -y -i {input} -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" -c:v libx264 -crf 23 {output}
```
