# Prompt Engineering

## Prompt Engineering

### Anatomy of a Good Prompt

```
[Subject] + [Action] + [Setting] + [Style] + [Quality Modifiers]

Example:
"A golden retriever [subject] running through tall grass [action]
in a sunny meadow [setting], cinematic lighting [style],
8K resolution, photorealistic [quality]"
```

### Prompt Templates

```python
PROMPT_TEMPLATES = {
    "cinematic": "{subject}, {action}, cinematic lighting, film grain, shallow depth of field, professional color grading",

    "nature": "{subject} in {setting}, golden hour lighting, National Geographic style, 8K resolution",

    "product": "{product} rotating slowly, studio lighting, white background, professional product photography",

    "social_media": "{subject}, {action}, trending on social media, vertical format, vibrant colors, engaging",

    "artistic": "{subject}, {style} art style, {mood} atmosphere, artistic interpretation, creative"
}

def generate_prompt(template: str, **kwargs) -> str:
    """Generate prompt from template."""
    return PROMPT_TEMPLATES[template].format(**kwargs)

# Usage
prompt = generate_prompt(
    "cinematic",
    subject="a vintage car",
    action="driving down a coastal highway at sunset"
)
```

### Good vs Bad Prompts

```
GOOD PROMPTS:
✓ "A hummingbird hovering near red flowers, macro photography, slow motion, nature documentary style"
✓ "Timelapse of storm clouds gathering over a cityscape, dramatic lighting, 4K cinematic"
✓ "A chef preparing sushi, close-up hands, professional kitchen, warm lighting"

BAD PROMPTS:
✗ "Video of stuff happening" (too vague)
✗ "A person walking and then running and then jumping and then swimming..." (too complex)
✗ "Make it look good" (no specific direction)
✗ "[Long paragraph with 500 words]" (too long, unfocused)
```
