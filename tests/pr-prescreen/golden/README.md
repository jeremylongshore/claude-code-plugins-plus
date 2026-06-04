# Prescreen golden grade fixtures

Synthetic per-skill validator-result fixtures spanning the A/B/C/D grade bands.
Each fixture mirrors the JSON shape emitted by
`scripts/validate-skills-schema.py --marketplace --json`.

These are used by `tests/pr-prescreen/test_grade.py` to pin the grade-composition
logic in `scripts/pr-prescreen/grade.py`. They're NOT used for live validator
testing — they're hand-curated to live in specific score bands.

If the score → grade mapping in `grade.py` changes, regenerate the fixtures
and update the tests accordingly. The mapping today:

| Grade | Score band |
| ----- | ---------- |
| A     | 90–100     |
| B     | 80–89      |
| C     | 70–79      |
| D     | 60–69      |
| F     | 0–59       |
