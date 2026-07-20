---
title: "Passing Is Not Validating: A Green Check With No Teeth"
description: "A JSON Schema validator passed all 19 checks while validating nothing. How a code review proved it, and the teeth check that fixed it."
date: "2026-07-19"
tags: ["testing", "python", "ci-cd", "architecture", "debugging"]
featured: false
---
A validator gate returned green on every check. Nineteen rule checks across four rules, all passing. And most of them were exercising nothing at all.

## The Contract

Intent Solutions built a repository-identity contract to canonically identify GitHub repositories in a registry. The question: what is the single source of truth for a repo's identity when repos get renamed and transferred between owners and orgs?

The design decision was sound. Use the immutable GitHub database ID (the numeric `source_repository_id`), never the mutable `owner/name` pair. Owner changes on transfer. Name changes on rename. Those belong in an `identity_history` list, not the primary key.

The schema enforced this intent.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["source_repository_id"],
  "properties": {
    "source_repository_id": {
      "type": "integer",
      "minimum": 1,
      "description": "The ONLY identity key. A string here is an invalid record by construction."
    },
    "current_owner": {
      "type": "string"
    },
    "current_name": {
      "type": "string"
    },
    "identity_history": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "owner": {"type": "string"},
          "name": {"type": "string"},
          "changed_at": {"type": "string", "format": "date-time"}
        }
      }
    }
  },
  "additionalProperties": false
}
```

A separate validator rule-gate existed to prove the identity rules held in practice. Four rules. Nineteen check statements total. All green.

## The Symptom

The code-review lane weakened the schema as a regression test. It changed `source_repository_id` from `{"type": "integer"}` to `{"type": ["integer", "string"]}`. That should break the whole identity model. A string could now be the identity key. The validation rules should go red.

They stayed green.

That is the proof: a check has no teeth. You sabotage the exact thing it exists to reject, and it does not notice.

## The Bug

The first rule, R1, was supposed to validate rename and transfer survival. This is what it looked like.

```python
def test_r1_rename_transfer_survival():
    # Construct test records
    renamed = {
        "source_repository_id": 12345,
        "current_owner": "new-owner",
        "current_name": "new-name"
    }
    transferred = {
        "source_repository_id": 12345,
        "current_owner": "other-org",
        "current_name": "old-name"
    }
    
    # Arithmetic check (never validates against schema)
    assert renamed["source_repository_id"] == transferred["source_repository_id"]
    assert renamed["current_owner"] != "original-owner"
    
    # GREEN. Tests nothing.
```

It constructed its own data. It did arithmetic on that data. It never called the actual jsonschema validator. It was testing the test, not the system.

This is a tautological test: it builds its own input, asserts something about that input, and never runs the system under test. It cannot fail for the reason it exists, because the thing it guards is never exercised.

## The Fix

The teeth check: deliberately weaken the invariant and assert the rule goes red.

```python
def test_r1_rename_transfer_survival():
    # Valid snapshot 1: rename
    renamed = {
        "source_repository_id": 12345,
        "current_owner": "new-owner",
        "current_name": "new-name"
    }
    
    # Valid snapshot 2: transfer
    transferred = {
        "source_repository_id": 12345,
        "current_owner": "other-org",
        "current_name": "old-name"
    }
    
    # Positive control: both snapshots must pass the real schema
    validator = jsonschema.Draft7Validator(schema)
    validator.validate(renamed)
    validator.validate(transferred)
    assert renamed["source_repository_id"] == transferred["source_repository_id"]
    
    # Teeth check: weaken the schema (allow strings as source_repository_id)
    weakened = copy.deepcopy(schema)
    weakened["properties"]["source_repository_id"]["type"] = ["integer", "string"]
    
    # With the weakened schema, a malformed record using owner as identity should be REJECTED
    invalid_by_string_id = {
        "source_repository_id": "original-owner",  # Wrong: string, not integer
        "current_owner": "new-owner"
    }
    
    # TEETH CHECK: the original validator rejects the string, the weakened one accepts it
    weak_validator = jsonschema.Draft7Validator(weakened)
    weak_validator.validate(invalid_by_string_id)  # Passes with weakened schema
    
    # Original schema must reject it
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(invalid_by_string_id)
```

Now R1 fails when you sabotage the schema. It has teeth.

The other gap: the schema used annotation-only `format` for timestamps instead of validating `pattern`.

```json
{
  "changed_at": {
    "type": "string",
    "format": "date-time"
  }
}
```

JSON Schema draft-07 does not enforce `format` by default. You have to opt in. The fix added explicit regex.

```json
{
  "changed_at": {
    "type": "string",
    "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$"
  }
}
```

The rewrite grew the suite while it was at it. The same four rules now drive twenty-eight valid and twenty-five invalid fixtures through the real validator, up from nineteen hollow checks. Each invalid one now genuinely fails for its specific planted reason, not an accidental different one.

## The Lesson

A test that constructs its own input and does arithmetic on it is testing the test. The system never sees the validator.

The fix is the teeth check. To prove a check has teeth:

1. Construct valid data that passes the real validator.
2. Deliberately break the invariant the check exists to protect (weaken the type, drop the constraint, plant the exact invalid case).
3. Assert the sabotaged case now slips through the weakened version.
4. Assert the original, unbroken validator still rejects it.
5. If step 4 does not go red, the check has no teeth.

This is the same failure mode as a mock that mocks the function under test, or a snapshot test that snapshots the bug. Mutation testing is the industrial version of the same idea.

Green checks are not proof of anything. Proof is: you sabotage the invariant and the check goes red.

## Also Shipped

Bob's Big Brain registrar added a seam firewall so governance scores are branded and retrieval scores cannot cross into them. L4 integration test now gates every PR.

Diagnostic Pro converted to Capacitor iOS and Android mobile apps, and onboarded to VPS auto-deploy with Umami analytics.

Mission Control operator kit built, proven, and wired.

## Related Posts

- [A Green Recovery Drill Can Still Be Lying](/posts/a-green-recovery-drill-can-still-be-lying/)
- [Let the Model Judge, Make the Code Decide](/posts/let-the-model-judge-make-the-code-decide/)
