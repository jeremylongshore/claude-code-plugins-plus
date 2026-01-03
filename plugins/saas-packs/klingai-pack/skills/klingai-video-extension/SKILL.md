---
name: klingai-video-extension
description: |
  Extend video duration using Kling AI continuation features. Use when creating longer videos
  from shorter clips or building seamless sequences. Trigger with phrases like 'klingai extend video',
  'kling ai video continuation', 'klingai longer video', 'extend klingai clip'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Video Extension

## Overview

This skill demonstrates extending video duration using Kling AI's continuation features, including seamless extensions, multi-segment generation, and narrative continuation.

## Prerequisites

- Kling AI API key configured
- Existing video or generation job
- Python 3.8+

## Instructions

Follow these steps for video extension:

1. **Get Base Video**: Have initial video ready
2. **Configure Extension**: Set continuation parameters
3. **Generate Extension**: Submit continuation request
4. **Merge Segments**: Combine video parts
5. **Review Continuity**: Check seamless transitions

## Video Extension Concepts

```
Kling AI Video Extension Options:

Extension Types:
- Forward continuation: Extend from end of video
- Backward continuation: Add content before start
- Bidirectional: Extend both directions

Duration Options:
- Base: 5 or 10 seconds per segment
- Max per extension: 10 seconds
- Total limit: Varies by plan

Continuity Modes:
- Seamless: AI maintains visual continuity
- Prompted: Use text to guide continuation
- Reference: Use last frame as reference
```

## Video Extension Implementation

```python
import requests
import os
import time
from typing import Optional, List, Dict
from dataclasses import dataclass, field

@dataclass
class VideoSegment:
    segment_id: str
    job_id: str
    video_url: Optional[str] = None
    duration: int = 5
    order: int = 0
    status: str = "pending"

@dataclass
class ExtendedVideo:
    base_job_id: str
    segments: List[VideoSegment] = field(default_factory=list)
    total_duration: int = 0

class KlingAIVideoExtender:
    """Extend videos using continuation features."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ["KLINGAI_API_KEY"]
        self.base_url = "https://api.klingai.com/v1"

    def extend_video(
        self,
        source_job_id: str,
        continuation_prompt: str,
        duration: int = 5,
        direction: str = "forward"
    ) -> Dict:
        """Extend an existing video."""
        response = requests.post(
            f"{self.base_url}/videos/extend",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "source_job_id": source_job_id,
                "prompt": continuation_prompt,
                "duration": duration,
                "direction": direction
            }
        )
        response.raise_for_status()
        return response.json()

    def extend_from_frame(
        self,
        frame_image: str,  # Base64 or URL
        continuation_prompt: str,
        duration: int = 5
    ) -> Dict:
        """Extend from a specific frame image."""
        response = requests.post(
            f"{self.base_url}/videos/extend-from-frame",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "frame": frame_image,
                "prompt": continuation_prompt,
                "duration": duration
            }
        )
        response.raise_for_status()
        return response.json()

    def create_extended_video(
        self,
        initial_prompt: str,
        continuation_prompts: List[str],
        segment_duration: int = 5
    ) -> ExtendedVideo:
        """Create a multi-segment extended video."""
        extended = ExtendedVideo(base_job_id="")

        # Generate initial segment
        print("Generating initial segment...")
        initial_response = requests.post(
            f"{self.base_url}/videos/text-to-video",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": initial_prompt,
                "duration": segment_duration
            }
        )
        initial_data = initial_response.json()
        extended.base_job_id = initial_data["job_id"]

        # Wait for initial to complete
        initial_result = self._wait_for_completion(initial_data["job_id"])

        extended.segments.append(VideoSegment(
            segment_id=f"seg_0",
            job_id=initial_data["job_id"],
            video_url=initial_result["video_url"],
            duration=segment_duration,
            order=0,
            status="completed"
        ))
        extended.total_duration = segment_duration

        # Generate continuations
        current_job_id = initial_data["job_id"]

        for i, cont_prompt in enumerate(continuation_prompts, 1):
            print(f"Generating continuation {i}/{len(continuation_prompts)}...")

            ext_response = self.extend_video(
                source_job_id=current_job_id,
                continuation_prompt=cont_prompt,
                duration=segment_duration
            )

            ext_result = self._wait_for_completion(ext_response["job_id"])

            segment = VideoSegment(
                segment_id=f"seg_{i}",
                job_id=ext_response["job_id"],
                video_url=ext_result["video_url"],
                duration=segment_duration,
                order=i,
                status="completed"
            )
            extended.segments.append(segment)
            extended.total_duration += segment_duration

            current_job_id = ext_response["job_id"]

        return extended

    def _wait_for_completion(self, job_id: str, timeout: int = 600) -> Dict:
        """Wait for job to complete."""
        start = time.time()

        while time.time() - start < timeout:
            response = requests.get(
                f"{self.base_url}/videos/{job_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            data = response.json()

            if data["status"] == "completed":
                return data
            elif data["status"] == "failed":
                raise Exception(f"Job failed: {data.get('error')}")

            time.sleep(5)

        raise TimeoutError(f"Job {job_id} timed out")

# Usage
extender = KlingAIVideoExtender()

# Single extension
result = extender.extend_video(
    source_job_id="vid_abc123",
    continuation_prompt="The scene continues with the sun setting lower",
    duration=5
)

# Multi-segment video
extended_video = extender.create_extended_video(
    initial_prompt="A peaceful morning in a forest clearing",
    continuation_prompts=[
        "Birds begin to wake and sing",
        "A deer cautiously enters the clearing",
        "The sun rises higher, illuminating the scene"
    ],
    segment_duration=5
)

print(f"Total duration: {extended_video.total_duration}s")
print(f"Segments: {len(extended_video.segments)}")
```

## Video Concatenation

```python
def concatenate_segments(segments: List[VideoSegment], output_path: str):
    """Concatenate video segments using ffmpeg."""
    import subprocess
    import tempfile

    # Download all segments
    segment_files = []
    for i, segment in enumerate(segments):
        if segment.video_url:
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            response = requests.get(segment.video_url)
            temp_file.write(response.content)
            temp_file.close()
            segment_files.append(temp_file.name)

    # Create concat file
    concat_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    for f in segment_files:
        concat_file.write(f"file '{f}'\n")
    concat_file.close()

    # Run ffmpeg concat
    subprocess.run([
        "ffmpeg", "-f", "concat", "-safe", "0",
        "-i", concat_file.name,
        "-c", "copy",
        output_path
    ], check=True)

    # Cleanup
    import os
    for f in segment_files:
        os.unlink(f)
    os.unlink(concat_file.name)

    print(f"Concatenated video saved to: {output_path}")

# Usage
concatenate_segments(extended_video.segments, "final_video.mp4")
```

## Seamless Loop Creation

```python
def create_seamless_loop(
    extender: KlingAIVideoExtender,
    prompt: str,
    duration: int = 5
) -> Dict:
    """Create a video that loops seamlessly."""
    # Generate initial video
    initial = requests.post(
        f"{extender.base_url}/videos/text-to-video",
        headers={
            "Authorization": f"Bearer {extender.api_key}",
            "Content-Type": "application/json"
        },
        json={
            "prompt": prompt,
            "duration": duration,
            "loop_mode": True  # If API supports
        }
    )

    result = extender._wait_for_completion(initial.json()["job_id"])

    return {
        "video_url": result["video_url"],
        "loop_ready": True,
        "duration": duration
    }

# For manual loop creation
def prepare_for_loop(video_path: str, output_path: str):
    """Prepare video for seamless looping using crossfade."""
    import subprocess

    # Create crossfade at loop point
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-filter_complex",
        "[0:v]split[body][pre];"
        "[pre]trim=duration=0.5,setpts=PTS-STARTPTS[pre_cut];"
        "[body]trim=start=0.5,setpts=PTS-STARTPTS[body_cut];"
        "[body_cut][pre_cut]xfade=transition=fade:duration=0.5[v]",
        "-map", "[v]",
        output_path
    ], check=True)

    print(f"Loop-ready video saved to: {output_path}")
```

## Output

Successful execution produces:
- Extended video sequences
- Seamless segment transitions
- Multi-segment concatenation
- Loop-ready videos

## Error Handling

Common errors and solutions:
1. **Continuity Break**: Adjust continuation prompt
2. **Style Shift**: Reference earlier frames
3. **Duration Limit**: Split into multiple extensions

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Video Extension](https://docs.klingai.com/extend)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [Video Concatenation](https://trac.ffmpeg.org/wiki/Concatenate)
