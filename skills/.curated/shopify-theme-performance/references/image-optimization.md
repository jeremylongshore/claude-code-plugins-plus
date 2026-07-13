Image optimization patterns for Shopify themes using the modern `image_url` filter.

## `image_url` vs `img_url`

| Feature | `img_url` (deprecated) | `image_url` (current) |
|---------|----------------------|----------------------|
| Responsive srcset | Not supported | Full srcset support |
| Exact width control | Predefined sizes only (100x100, 300x300, etc.) | Any width up to 5760px |
| Crop control | `_crop_center` suffix | `crop: 'center'` param |
| Format control | None | Automatic WebP/AVIF via CDN |
| Max resolution | 2048px | 5760px |

## Basic Usage

```liquid
{% comment %} Old way (deprecated) {% endcomment %}
{{ product.featured_image | img_url: '800x' }}

{% comment %} New way {% endcomment %}
{{ product.featured_image | image_url: width: 800 }}
```

## Responsive Image Pattern

```liquid
{% assign image = product.featured_image %}

<img
  src="{{ image | image_url: width: 800 }}"
  srcset="
    {{ image | image_url: width: 200 }} 200w,
    {{ image | image_url: width: 400 }} 400w,
    {{ image | image_url: width: 600 }} 600w,
    {{ image | image_url: width: 800 }} 800w,
    {{ image | image_url: width: 1000 }} 1000w,
    {{ image | image_url: width: 1200 }} 1200w"
  sizes="(max-width: 749px) calc(100vw - 32px),
         (max-width: 1199px) calc(50vw - 48px),
         400px"
  width="{{ image.width }}"
  height="{{ image.height }}"
  loading="lazy"
  alt="{{ image.alt | escape }}">
```

## Image Loading Strategy by Position

```liquid
{% for product in collection.products %}
  {% if forloop.index <= 4 %}
    {% comment %} Above the fold: eager load first 4 product images {% endcomment %}
    {{ product.featured_image | image_url: width: 600 | image_tag:
        loading: 'eager',
        sizes: '(max-width: 749px) 50vw, 25vw',
        widths: '200,400,600' }}
  {% else %}
    {% comment %} Below the fold: lazy load the rest {% endcomment %}
    {{ product.featured_image | image_url: width: 600 | image_tag:
        loading: 'lazy',
        sizes: '(max-width: 749px) 50vw, 25vw',
        widths: '200,400,600' }}
  {% endif %}
{% endfor %}
```

## Using `image_tag` Filter

The `image_tag` filter generates a complete `<img>` element with srcset:

```liquid
{% comment %} Basic image_tag {% endcomment %}
{{ product.featured_image | image_url: width: 800 | image_tag }}

{% comment %} With attributes {% endcomment %}
{{ product.featured_image | image_url: width: 800 | image_tag:
    class: 'product-image',
    loading: 'lazy',
    sizes: '(max-width: 749px) 100vw, 50vw',
    widths: '200,400,600,800,1000,1200' }}

{% comment %} Output:
<img src="//cdn.shopify.com/...800x.jpg"
     srcset="//cdn.shopify.com/...200x.jpg 200w, ...400x.jpg 400w, ..."
     sizes="(max-width: 749px) 100vw, 50vw"
     class="product-image"
     loading="lazy"
     width="800"
     height="600">
{% endcomment %}
```

## Crop and Focal Point

```liquid
{% comment %} Center crop to exact dimensions {% endcomment %}
{{ image | image_url: width: 400, height: 400, crop: 'center' }}

{% comment %} Focal point crop (if set by merchant in admin) {% endcomment %}
{{ image | image_url: width: 400, height: 300, crop: 'center' }}
```

## Placeholder Images

Handle missing images gracefully:

```liquid
{% if product.featured_image %}
  {{ product.featured_image | image_url: width: 600 | image_tag:
      loading: 'lazy',
      alt: product.title }}
{% else %}
  {{ 'product-placeholder.svg' | asset_url | image_tag:
      class: 'placeholder-image',
      alt: product.title }}
{% endif %}
```

## Performance Checklist

- [ ] Hero/LCP image uses `loading: 'eager'` and `fetchpriority: 'high'`
- [ ] All other images use `loading: 'lazy'`
- [ ] Every `<img>` has explicit `width` and `height` attributes
- [ ] `srcset` includes at least 4 size options for responsive delivery
- [ ] `sizes` attribute matches your CSS layout breakpoints
- [ ] No images wider than needed (check with DevTools Network tab)
- [ ] Using `image_url` (not deprecated `img_url`)
