---
name: record
description: Start, stop, pause, or mark moments in screen recordings with organized file management
---

# Screen Recording Command

Start and stop screen recordings with automatic organization and metadata tracking.

## Usage

```bash
/record start [project-name]    # Start recording
/record stop                    # Stop and save recording
/record pause                   # Pause recording
/record resume                  # Resume paused recording
/record mark [description]      # Mark a good moment while recording
/record status                  # Check current recording status
```

## Purpose

Quick screen recording with:
- One-command start/stop
- Automatic file organization by project
- Timestamp-based naming
- Mark "good takes" while recording
- Metadata for editing later

## Implementation

When user runs `/record start [project-name]`:

1. **Initialize Recording**
   - Detect operating system
   - Use native recording tools:
     - macOS: `screencapture` or QuickTime
     - Linux: `ffmpeg` with X11 capture
     - Windows: PowerShell screen capture
   - Default to 1920x1080, 30fps, H.264

2. **Create Directory Structure**
   ```
   ~/Videos/[project-name]/
   ├── raw/                    # Raw recordings
   ├── markers.json            # Timestamp markers
   └── metadata.json           # Recording metadata
   ```

3. **Generate Filename**
   ```
   Format: YYYY-MM-DD-HH-MM-[project-name].mp4
   Example: 2025-01-15-11-47-redis-caching.mp4
   ```

4. **Create Metadata File**
   ```json
   {
     "project": "redis-caching",
     "startTime": "2025-01-15T11:47:00Z",
     "duration": null,
     "status": "recording",
     "markers": [],
     "resolution": "1920x1080",
     "fps": 30,
     "codec": "h264"
   }
   ```

5. **Display Status**
   ```
   🔴 Screen recording started
   Project: redis-caching
   Recording to: ~/Videos/redis-caching/raw/2025-01-15-11-47-redis-caching.mp4

   Commands:
   - /record stop     : Stop and save recording
   - /record pause    : Pause recording
   - /record mark     : Mark a good moment
   ```

## Marking Moments

When user runs `/record mark [description]`:

1. **Capture Timestamp**
   - Calculate time elapsed since recording start
   - Format as HH:MM:SS

2. **Save Marker**
   ```json
   {
     "markers": [
       {
         "timestamp": "00:14:23",
         "description": "Redis integration working!",
         "time": "2025-01-15T12:01:23Z"
       }
     ]
   }
   ```

3. **Confirm**
   ```
   📍 Marker added at 00:14:23
   "Redis integration working!"
   ```

## Stopping Recording

When user runs `/record stop`:

1. **Stop Capture**
   - Send stop signal to recording process
   - Wait for file finalization

2. **Calculate Duration**
   - Measure total recording time
   - Update metadata

3. **Update Metadata**
   ```json
   {
     "project": "redis-caching",
     "startTime": "2025-01-15T11:47:00Z",
     "endTime": "2025-01-15T12:34:00Z",
     "duration": "00:47:00",
     "status": "completed",
     "markers": [
       {
         "timestamp": "00:14:23",
         "description": "Redis integration working!"
       },
       {
         "timestamp": "00:32:10",
         "description": "Performance test results"
       }
     ],
     "fileSize": "1.2GB",
     "resolution": "1920x1080",
     "fps": 30
   }
   ```

4. **Display Summary**
   ```
   ✅ Recording saved: ~/Videos/redis-caching/raw/2025-01-15-11-47-redis-caching.mp4

   Duration: 47 minutes
   File size: 1.2 GB
   Markers: 2

   Markers:
   00:14:23 - Redis integration working!
   00:32:10 - Performance test results

   Ready for editing with video-editor-ai agent
   ```

## Platform-Specific Recording

### macOS
```bash
# Using ffmpeg (install with: brew install ffmpeg)
ffmpeg -f avfoundation -framerate 30 -video_size 1920x1080 \
  -i "1:0" -c:v libx264 -preset ultrafast \
  ~/Videos/[project]/raw/[filename].mp4
```

### Linux
```bash
# Using ffmpeg with X11
ffmpeg -f x11grab -framerate 30 -video_size 1920x1080 \
  -i :0.0 -c:v libx264 -preset ultrafast \
  ~/Videos/[project]/raw/[filename].mp4
```

### Windows
```powershell
# Using PowerShell and Windows.Graphics.Capture
# Requires Windows 10 1809+
$recording = Start-ScreenRecording -Path "C:\Videos\[project]\raw\[filename].mp4"
```

## Advanced Features

### Audio Recording

```bash
/record start [project-name] --with-audio
```

Captures:
- System audio (application sounds)
- Microphone input (narration)
- Separate audio tracks for mixing

### Region Selection

```bash
/record start [project-name] --region
```

Interactive region selector:
- Click and drag to select screen area
- Record only selected region
- Useful for focused tutorials

### Webcam Overlay

```bash
/record start [project-name] --webcam
```

Composite recording:
- Screen capture (main)
- Webcam feed (picture-in-picture)
- Configurable position and size

## Integration with Other Plugins

This command integrates with:

- **build-logger-agent**: Auto-suggests when to record based on breakthroughs
- **video-editor-ai**: Passes recording + markers for automated editing
- **demo-video-generator**: Coordinates recording for product demos
- **batch-recording-scheduler**: Manages multiple recording sessions

## Examples

### Basic Recording

```bash
User: /record start redis-tutorial
Claude: 🔴 Screen recording started
        Project: redis-tutorial
        Recording to: ~/Videos/redis-tutorial/raw/2025-01-15-11-47-redis-tutorial.mp4
        Press /record stop when done

[User codes for 30 minutes]

User: /record mark "Cache hit working!"
Claude: 📍 Marker added at 00:14:23
        "Cache hit working!"

[User codes for another 20 minutes]

User: /record stop
Claude: ✅ Recording saved
        Duration: 47 minutes
        File size: 1.2 GB
        Markers: 1

        Ready for editing with video-editor-ai
```

### Batch Recording Session

```bash
User: /record start tutorial-1-intro
Claude: 🔴 Recording tutorial-1-intro...

User: /record stop
Claude: ✅ Saved (12 minutes)

User: /record start tutorial-2-implementation
Claude: 🔴 Recording tutorial-2-implementation...

User: /record stop
Claude: ✅ Saved (18 minutes)

User: /record start tutorial-3-testing
Claude: 🔴 Recording tutorial-3-testing...
```

## Error Handling

### Storage Space Check
```
⚠️ Warning: Low disk space (5 GB remaining)
Estimated recording size: ~1.5 GB per hour
Continue? (y/n)
```

### Already Recording
```
❌ Error: Recording already in progress
Current recording: redis-tutorial (14:23 elapsed)
Stop current recording with /record stop
```

### Missing Dependencies
```
❌ Error: ffmpeg not found
Install ffmpeg:
- macOS: brew install ffmpeg
- Linux: sudo apt install ffmpeg
- Windows: choco install ffmpeg
```

## Configuration

Store preferences in `~/.creator-studio/record-config.json`:

```json
{
  "defaultResolution": "1920x1080",
  "defaultFPS": 30,
  "defaultCodec": "h264",
  "audioEnabled": true,
  "audioInputDevice": "default",
  "outputDirectory": "~/Videos",
  "fileFormat": "mp4",
  "compressionPreset": "ultrafast"
}
```

## Best Practices

1. **Always mark good moments** - Easier to find great takes later
2. **Use descriptive project names** - Makes file organization effortless
3. **Check storage before long recordings** - Avoid incomplete recordings
4. **Record in segments** - Easier to edit than one long take
5. **Use consistent resolution** - Simplifies editing and exporting

## Troubleshooting

### Recording is choppy
- Reduce resolution: `--resolution 1280x720`
- Lower framerate: `--fps 24`
- Use faster compression: `--preset ultrafast`

### Audio is out of sync
- Record audio separately
- Use a lower video bitrate
- Sync in post-production with video-editor-ai

### File is too large
- Use a more aggressive compression preset
- Record at lower resolution
- Split into shorter segments

Your goal: Make screen recording effortless with one command, so creators can focus on building while capturing everything for video content.
