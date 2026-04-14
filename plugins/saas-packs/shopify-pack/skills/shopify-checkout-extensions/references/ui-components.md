Available Checkout UI Extension components and their key props.

## Layout Components

### BlockStack
Vertical stack with spacing control.
```tsx
<BlockStack spacing="base" padding="base">
  <Text>Item 1</Text>
  <Text>Item 2</Text>
</BlockStack>
// spacing: "none" | "extraTight" | "tight" | "base" | "loose" | "extraLoose"
// padding: same values, or ["base", "none"] for [block, inline]
```

### InlineStack
Horizontal stack.
```tsx
<InlineStack spacing="base" blockAlignment="center">
  <Icon source="truck" />
  <Text>Free shipping</Text>
</InlineStack>
// blockAlignment: "leading" | "center" | "trailing" | "baseline"
// inlineAlignment: "leading" | "center" | "trailing"
```

### Grid
CSS Grid layout.
```tsx
<Grid columns={["fill", "auto"]} spacing="base">
  <View><Text>Left</Text></View>
  <View><Text>Right</Text></View>
</Grid>
```

### View
Generic container (like a div).
```tsx
<View padding="base" border="base" cornerRadius="base">
  <Text>Boxed content</Text>
</View>
```

### Divider
Horizontal rule.
```tsx
<Divider />
```

## Content Components

### Text
```tsx
<Text size="medium" emphasis="bold" appearance="subdued">
  Styled text
</Text>
// size: "extraSmall" | "small" | "base" | "medium" | "large" | "extraLarge"
// emphasis: "bold" | "italic"
// appearance: "accent" | "subdued" | "info" | "success" | "warning" | "critical" | "decorative"
```

### Heading
```tsx
<Heading level={2}>Section Title</Heading>
// level: 1 | 2 | 3
```

### TextBlock
Multi-line text with paragraph spacing.
```tsx
<TextBlock>Long paragraph text that wraps naturally.</TextBlock>
```

### Image
```tsx
<Image source="https://cdn.shopify.com/..." accessibilityDescription="Product photo" />
// cornerRadius, aspectRatio, fit ("cover" | "contain") available
```

### Icon
```tsx
<Icon source="checkCircle" size="small" appearance="accent" />
// Built-in sources: "arrowLeft", "arrowRight", "cart", "checkCircle", "chevronDown",
// "chevronUp", "close", "critical", "discount", "email", "errorCircle",
// "info", "lock", "marker", "mobile", "note", "pen", "plus", "profile",
// "question", "star", "store", "success", "truck", "warning"
```

### Banner
```tsx
<Banner status="info" title="Optional title">
  Banner content text.
</Banner>
// status: "info" | "success" | "warning" | "critical"
// collapsible: boolean
```

## Form Components

### TextField
```tsx
<TextField
  label="Delivery Note"
  value={note}
  onChange={setNote}
  maxLength={250}
  multiline={3}
  error="Required field"
/>
// type: "text" (default) | "email" | "telephone"
```

### Checkbox
```tsx
<Checkbox checked={agreed} onChange={setAgreed}>
  I agree to the terms
</Checkbox>
```

### Select
```tsx
<Select
  label="Gift wrap style"
  value={style}
  onChange={setStyle}
  options={[
    { value: "none", label: "No wrapping" },
    { value: "basic", label: "Basic ($3)" },
    { value: "premium", label: "Premium ($8)" },
  ]}
/>
```

### ChoiceList
Radio or checkbox group.
```tsx
<ChoiceList
  name="delivery-speed"
  value={[selected]}
  onChange={setSelected}
  variant="group"
>
  <Choice id="standard">Standard (3-5 days)</Choice>
  <Choice id="express">Express (1-2 days)</Choice>
</ChoiceList>
```

### DatePicker
```tsx
<DatePicker
  selected={selectedDate}
  onChange={setSelectedDate}
  disabled={["2025-12-25", "2025-12-26"]}
/>
```

### Button
```tsx
<Button kind="secondary" onPress={handleClick} loading={isLoading}>
  Add gift wrap
</Button>
// kind: "primary" | "secondary" | "plain"
// appearance: "critical" | "monochrome"
```

## Interactive Components

### Pressable
Clickable wrapper (like a button without button styling).
```tsx
<Pressable onPress={() => setExpanded(!expanded)}>
  <InlineStack spacing="tight">
    <Text>Show details</Text>
    <Icon source={expanded ? "chevronUp" : "chevronDown"} />
  </InlineStack>
</Pressable>
```

### Disclosure
Expandable/collapsible section.
```tsx
<Disclosure open={isOpen} onToggle={setIsOpen}>
  <Pressable><Text>Toggle section</Text></Pressable>
  <View padding="base">
    <Text>Hidden content revealed on toggle.</Text>
  </View>
</Disclosure>
```

## Important Constraints

- **No custom CSS**: All styling via component props (spacing, padding, appearance)
- **No raw HTML**: Cannot use `<div>`, `<span>`, or any DOM elements
- **No external fonts/images**: Must use Shopify CDN URLs or extension assets
- **No `fetch`**: Use `useApplyMetafieldsChange` to write data; read via hooks
- **64KB limit**: Every component import adds to bundle size
