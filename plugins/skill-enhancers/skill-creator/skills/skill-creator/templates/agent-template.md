---
name: {{AGENT_NAME}}
description: "{{AGENT_SPECIALTY_20_200_CHARS}}"
# Optional fields (include as needed):
# model: sonnet                          # sonnet|haiku|opus|inherit
# effort: medium                         # low|medium|high
# maxTurns: 15                           # Max agentic loop iterations
# disallowedTools: "Write,Edit"          # Denylist (opposite of skills' allowed-tools)
# skills: [{{SKILL_1}}, {{SKILL_2}}]    # Skills to preload
# memory: project                        # user|project|local
# background: false                      # Run in background
# isolation: worktree                    # Isolated git worktree
---

# {{AGENT_TITLE}}

{{ONE_LINE_ROLE_STATEMENT}}

## Role

{{DETAILED_ROLE_DESCRIPTION_2_3_SENTENCES. What domain does this agent specialize in?
What unique perspective or methodology does it bring? What is it NOT responsible for?}}

## Inputs

You receive these parameters in your prompt:

- **{{INPUT_1}}**: {{DESCRIPTION}}
- **{{INPUT_2}}**: {{DESCRIPTION}}
- **{{INPUT_3}}**: {{DESCRIPTION}}

## Process

### Step 1: {{STEP_TITLE}}

{{DETAILED_INSTRUCTIONS_FOR_STEP}}

### Step 2: {{STEP_TITLE}}

{{DETAILED_INSTRUCTIONS_FOR_STEP}}

### Step 3: {{STEP_TITLE}}

{{DETAILED_INSTRUCTIONS_FOR_STEP}}

### Step 4: {{STEP_TITLE}}

{{DETAILED_INSTRUCTIONS_FOR_STEP}}

## Output Format

{{DESCRIBE_STRUCTURED_OUTPUT_FORMAT}}

```json
{
  "{{FIELD_1}}": "{{DESCRIPTION}}",
  "{{FIELD_2}}": [
    {
      "{{SUBFIELD}}": "{{DESCRIPTION}}"
    }
  ],
  "summary": {
    "{{METRIC_1}}": 0,
    "{{METRIC_2}}": 0
  }
}
```

## Guidelines

- **{{GUIDELINE_1}}**: {{EXPLANATION}}
- **{{GUIDELINE_2}}**: {{EXPLANATION}}
- **{{GUIDELINE_3}}**: {{EXPLANATION}}
- **{{GUIDELINE_4}}**: {{EXPLANATION}}

## When Activated

You activate when:

- {{ACTIVATION_CONDITION_1}}
- {{ACTIVATION_CONDITION_2}}
- {{ACTIVATION_CONDITION_3}}

## Communication Style

- {{STYLE_TRAIT_1}}
- {{STYLE_TRAIT_2}}
- {{STYLE_TRAIT_3}}

## Success Criteria

Good output includes:

- {{QUALITY_MARKER_1}}
- {{QUALITY_MARKER_2}}
- {{QUALITY_MARKER_3}}

Poor output is:

- {{ANTI_PATTERN_1}}
- {{ANTI_PATTERN_2}}
- {{ANTI_PATTERN_3}}
