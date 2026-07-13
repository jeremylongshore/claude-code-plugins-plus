Variant D: Theme App Extension project structure and Liquid block example.

**Best for:** Storefront widgets, product reviews, badges, banners

**When to use:** You only need to add UI elements to the merchant's Online Store.

```
my-theme-extension/
├── extensions/
│   └── my-widget/
│       ├── blocks/
│       │   ├── product-badge.liquid
│       │   ├── announcement-bar.liquid
│       │   └── review-stars.liquid
│       ├── assets/
│       │   ├── widget.css
│       │   └── widget.js
│       ├── locales/
│       │   └── en.default.json
│       └── snippets/
│           └── shared-styles.liquid
├── shopify.app.toml
└── package.json
```

**Key tech:** Liquid templates, JavaScript, CSS

**API used:** None directly -- uses Liquid objects (`product`, `cart`, `customer`)

**No server needed:** Theme app extensions run entirely in the merchant's storefront.

```liquid
{% comment %} blocks/product-badge.liquid {% endcomment %}
{% schema %}
{
  "name": "Sale Badge",
  "target": "section",
  "settings": [
    { "type": "text", "id": "badge_text", "label": "Badge Text", "default": "SALE" },
    { "type": "color", "id": "badge_color", "label": "Color", "default": "#FF0000" }
  ]
}
{% endschema %}

{% if product.compare_at_price > product.price %}
  <span class="sale-badge" style="background: {{ block.settings.badge_color }}">
    {{ block.settings.badge_text }}
  </span>
{% endif %}
```
