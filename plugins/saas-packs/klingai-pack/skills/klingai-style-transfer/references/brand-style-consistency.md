# Brand Style Consistency

## Brand Style Consistency

```python
@dataclass
class BrandStyle:
    name: str
    primary_colors: List[str]
    secondary_colors: List[str]
    mood: str
    visual_style: VideoStyle
    additional_modifiers: List[str]

class BrandStyleManager:
    """Manage consistent brand styles across videos."""

    def __init__(self, style_transfer: KlingAIStyleTransfer):
        self.style_transfer = style_transfer
        self.brands: Dict[str, BrandStyle] = {}

    def register_brand(self, brand: BrandStyle):
        """Register a brand style."""
        self.brands[brand.name] = brand

    def generate_brand_video(
        self,
        brand_name: str,
        content_prompt: str,
        duration: int = 5
    ) -> Dict:
        """Generate video matching brand style."""
        if brand_name not in self.brands:
            raise ValueError(f"Brand not registered: {brand_name}")

        brand = self.brands[brand_name]

        # Build brand-specific style
        color_palette = ", ".join(brand.primary_colors + brand.secondary_colors)

        style = StyleSettings(
            primary_style=brand.visual_style,
            style_strength=0.7,
            color_palette=color_palette
        )

        # Add brand modifiers to prompt
        branded_prompt = f"{content_prompt}, {brand.mood} mood"
        for modifier in brand.additional_modifiers:
            branded_prompt += f", {modifier}"

        return self.style_transfer.apply_style(branded_prompt, style, duration)

# Usage
manager = BrandStyleManager(style_transfer)

# Register brand
manager.register_brand(BrandStyle(
    name="TechCorp",
    primary_colors=["electric blue", "white"],
    secondary_colors=["silver", "dark gray"],
    mood="professional and innovative",
    visual_style=VideoStyle.CYBERPUNK,
    additional_modifiers=["clean lines", "futuristic", "high-tech"]
))

# Generate branded video
result = manager.generate_brand_video(
    brand_name="TechCorp",
    content_prompt="A product showcase of the latest smartphone",
    duration=5
)
```
