How to use Shopify's Liquid profiler to identify slow theme code and optimize server-side render times.

## Activating the Profiler

Append `?profile=true` to any storefront URL:

```
https://your-store.myshopify.com/?profile=true
https://your-store.myshopify.com/products/my-product?profile=true
https://your-store.myshopify.com/collections/all?profile=true
```

The profiler output appears as an HTML comment at the bottom of the page source (View Source, scroll to bottom) or in a visible table if your theme supports it.

## Reading Profiler Output

The profiler shows a table with these columns:

| Column | Meaning |
|--------|---------|
| **Snippet** | Template or snippet file name |
| **Total Time** | Wall-clock time including children |
| **Self Time** | Time in this file only (excluding includes/renders) |
| **Count** | Number of times this snippet was rendered |

**Focus on Self Time** — high Total Time with low Self Time means the slowness is in a child snippet. Drill into the children.

## Common Slow Patterns

### Nested For Loops

```liquid
{% comment %} BAD: O(n*m) complexity {% endcomment %}
{% for product in collection.products %}
  {% for variant in product.variants %}
    {% for option in variant.options %}
      {{ option }}
    {% endfor %}
  {% endfor %}
{% endfor %}

{% comment %} BETTER: limit depth, paginate outer loop {% endcomment %}
{% paginate collection.products by 12 %}
  {% for product in collection.products %}
    {{ product.variants.first.title }}
  {% endfor %}
{% endpaginate %}
```

### Excessive `include` Tags

The `include` tag creates a new variable scope for each call, which is expensive:

```liquid
{% comment %} BAD: include copies parent scope every time {% endcomment %}
{% for product in collection.products %}
  {% include 'product-card' %}
{% endfor %}

{% comment %} GOOD: render has isolated scope, much faster {% endcomment %}
{% for product in collection.products %}
  {% render 'product-card', product: product %}
{% endfor %}
```

The `render` tag is 20-40% faster than `include` because it does not copy the parent scope.

### Unfiltered Collection Access

```liquid
{% comment %} BAD: loads ALL products in a collection {% endcomment %}
{% for product in collections['all'].products %}
  {{ product.title }}
{% endfor %}

{% comment %} GOOD: paginate to control how many load {% endcomment %}
{% paginate collections['sale'].products by 24 %}
  {% for product in collections['sale'].products %}
    {{ product.title }}
  {% endfor %}
{% endpaginate %}
```

### Heavy Metafield Access in Loops

```liquid
{% comment %} BAD: metafield access in a loop is slow {% endcomment %}
{% for product in collection.products %}
  {{ product.metafields.custom.care_instructions.value }}
  {{ product.metafields.custom.material.value }}
  {{ product.metafields.custom.origin_country.value }}
{% endfor %}

{% comment %} BETTER: assign outside loop if possible, or limit metafield access {% endcomment %}
{% for product in collection.products %}
  {% assign care = product.metafields.custom.care_instructions %}
  {% if care %}{{ care.value }}{% endif %}
{% endfor %}
```

## Performance Targets

| Metric | Target | Measured Where |
|--------|--------|---------------|
| Total Liquid render time | < 200ms | Profiler Total Time (root) |
| Single snippet Self Time | < 50ms | Profiler Self Time |
| Snippet render count | < 100 per page | Profiler Count column |
| Template depth | < 4 levels | Manual inspection |
