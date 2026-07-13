# Seamless Loop Creation

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
