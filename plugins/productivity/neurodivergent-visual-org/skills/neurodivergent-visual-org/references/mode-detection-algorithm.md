# Mode Detection Algorithm

#### Step 1: Check for explicit base mode request
```python
base_mode = None
accessibility_mode = None

# Detect base mode
if "neurotypical mode" in user_message.lower():
    base_mode = "neurotypical"
elif "adhd mode" or "neurodivergent mode" in user_message.lower():
    base_mode = "neurodivergent"
```

#### Step 2: Check for explicit accessibility mode request
```python
# Detect colorblind-safe mode
colorblind_keywords = ["colorblind", "color blind", "colorblind-safe",
                      "colour blind", "accessible colors", "pattern-based",
                      "cvd", "color vision deficiency"]
if any(keyword in user_message.lower() for keyword in colorblind_keywords):
    accessibility_mode = "colorblind-safe"

# Detect monochrome mode (takes precedence over colorblind-safe)
monochrome_keywords = ["monochrome", "black and white", "b&w", "grayscale",
                      "greyscale", "print-friendly", "printing", "e-ink",
                      "black & white", "photocopier"]
if any(keyword in user_message.lower() for keyword in monochrome_keywords):
    accessibility_mode = "monochrome"
```

#### Step 3: Check configuration file
```python
if config_file_exists():
    config = load_user_preference()

    # Apply base mode if not explicitly set
    if base_mode is None:
        base_mode = config.get("default_mode", "neurodivergent")

    # Apply accessibility mode if not explicitly set
    if accessibility_mode is None:
        accessibility_mode = config.get("colorblind_safe", False) and "colorblind-safe"
        if not accessibility_mode:
            accessibility_mode = config.get("monochrome", False) and "monochrome"
```

#### Step 4: Auto-detect base mode from language
```python
distress_signals = ["overwhelmed", "paralyzed", "stuck", "can't decide",
                   "don't know where to start", "too much"]
neurodivergent_mentions = ["adhd", "autism", "executive dysfunction",
                          "time blindness", "decision paralysis"]
energy_mentions = ["spoons", "burned out", "exhausted", "no energy"]

if base_mode is None:
    if any(signal in user_message.lower() for signal in
           distress_signals + neurodivergent_mentions + energy_mentions):
        base_mode = "neurodivergent"
```

#### Step 5: Default to neurodivergent base mode (inclusive)
```python
if base_mode is None:
    base_mode = "neurodivergent"  # Backward compatible with v2.0
```

#### Step 6: Apply modes
```python
# accessibility_mode can be None, "colorblind-safe", or "monochrome"
# base_mode will always be "neurodivergent" or "neurotypical"
apply_modes(base_mode=base_mode, accessibility_mode=accessibility_mode)
```
