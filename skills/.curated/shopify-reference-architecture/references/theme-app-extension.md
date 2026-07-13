# Theme App Extension

Complete Liquid block for a product rating widget with configurable settings.

```liquid
{% comment %} extensions/theme-app-extension/blocks/product-rating.liquid {% endcomment %}

{% schema %}
{
  "name": "Product Rating",
  "target": "section",
  "settings": [
    {
      "type": "range",
      "id": "max_stars",
      "label": "Maximum Stars",
      "min": 1,
      "max": 5,
      "default": 5
    },
    {
      "type": "color",
      "id": "star_color",
      "label": "Star Color",
      "default": "#FFD700"
    }
  ]
}
{% endschema %}

<div class="product-rating" style="--star-color: {{ block.settings.star_color }}">
  {% assign rating = product.metafields.custom.rating.value | default: 0 %}
  {% for i in (1..block.settings.max_stars) %}
    <span class="star {% if i <= rating %}filled{% endif %}">&#9733;</span>
  {% endfor %}
  <span class="rating-text">{{ rating }}/{{ block.settings.max_stars }}</span>
</div>

<style>
  .product-rating .star { color: #ccc; font-size: 1.2em; }
  .product-rating .star.filled { color: var(--star-color); }
</style>
```
