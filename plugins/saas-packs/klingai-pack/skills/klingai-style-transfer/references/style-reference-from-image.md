# Style Reference From Image

## Style Reference from Image

```python
def style_from_reference(
    style_transfer: KlingAIStyleTransfer,
    content_prompt: str,
    reference_image_path: str,
    style_strength: float = 0.7
) -> Dict:
    """Apply style from a reference image."""
    # Encode reference image
    with open(reference_image_path, "rb") as f:
        reference_b64 = base64.b64encode(f.read()).decode("utf-8")

    style = StyleSettings(
        primary_style=VideoStyle.REALISTIC,  # Let reference determine style
        style_strength=style_strength,
        reference_image=f"data:image/jpeg;base64,{reference_b64}"
    )

    return style_transfer.apply_style(
        prompt=f"{content_prompt}, matching the artistic style of the reference",
        style=style
    )

# Usage
result = style_from_reference(
    style_transfer,
    content_prompt="A city skyline at night",
    reference_image_path="van_gogh_starry_night.jpg",
    style_strength=0.8
)
```
