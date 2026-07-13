# Video Concatenation

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
