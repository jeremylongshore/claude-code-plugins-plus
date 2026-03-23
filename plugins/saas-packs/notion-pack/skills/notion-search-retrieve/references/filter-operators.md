# Notion Database Filter Operators Reference

## Filter Operators by Property Type

| Property Type | Available Operators |
|---------------|-------------------|
| title, rich_text, url, email, phone_number | equals, does_not_equal, contains, does_not_contain, starts_with, ends_with, is_empty, is_not_empty |
| number | equals, does_not_equal, greater_than, less_than, greater_than_or_equal_to, less_than_or_equal_to, is_empty, is_not_empty |
| select, status | equals, does_not_equal, is_empty, is_not_empty |
| multi_select | contains, does_not_contain, is_empty, is_not_empty |
| date | equals, before, after, on_or_before, on_or_after, is_empty, is_not_empty |
| people | contains, does_not_contain, is_empty, is_not_empty |
| checkbox | equals, does_not_equal |
| relation | contains, does_not_contain, is_empty, is_not_empty |
| formula | Depends on formula result type (string, number, boolean, date) |

## Property Value Extraction

| Property Type | Access Pattern |
|---------------|---------------|
| title | `prop.title.map(t => t.plain_text).join('')` |
| rich_text | `prop.rich_text.map(t => t.plain_text).join('')` |
| number | `prop.number` |
| select | `prop.select?.name` |
| multi_select | `prop.multi_select.map(s => s.name)` |
| date | `prop.date?.start`, `prop.date?.end` |
| people | `prop.people.map(p => p.name)` |
| checkbox | `prop.checkbox` |
| url | `prop.url` |
| email | `prop.email` |
| phone_number | `prop.phone_number` |
| formula | `prop.formula` (type-dependent) |
| relation | `prop.relation.map(r => r.id)` |
| rollup | `prop.rollup` (type-dependent) |
| status | `prop.status?.name` |
