<!-- doc-class: record -->

# Document Supersession Record Template

Use this record whenever one governed document replaces all or part of another. Supersession is
one atomic pull request, not a status-only edit: the old document is frozen, the new authority
disposes every affected section, `STANDARDS.md` points to the new owner, and the old document gains
the machine-readable frozen class.

## Copyable record

Copy the block below into the superseding document, replace every angle-bracket placeholder, and
run `node scripts/check-supersession-template.mjs <document>`. The checker ignores this fenced
example and rejects placeholders in a completed record. Keep the structural label
`**Frozen header:**` exact unless the record embeds a title-only
`> **SUPERSEDED–FROZEN (...).**` blockquote. Do not append or continue prose in that blockquote;
the checker intentionally rejects natural-language evidence.

Repository review runs `node scripts/check-supersession-template.mjs --all`, which discovers
tracked Markdown under `000-docs/` and validates every visible completed-record block or malformed
record attempt. Ordinary documents and fenced or commented examples do not enter that cohort. The
gate fails closed if no completed record remains; remove the worked example only in the same change
that files a replacement record.

```markdown
<!-- BEGIN SUPERSESSION RECORD -->

## Supersession record: <old document> to <new document>

- **Atomic PR:** This one pull request carries every checked item below.
- **Frozen document(s):** `<path to each old document>`
- **Superseding document:** `<path to new document>`
- **Frozen header:** `<!-- doc-class: frozen -->` followed by a `SUPERSEDED–FROZEN` banner.
- **STANDARDS.md Canonical documents pointer:** `<table row linking the new document>`

### Section disposition

| Superseded section            | Disposition                                                                    | New authority                    |
| ----------------------------- | ------------------------------------------------------------------------------ | -------------------------------- |
| `<old section or fact class>` | `CARRIED FORWARD`, `REPLACED`, `REVERSED`, or `SUPERSEDED WITHOUT REPLACEMENT` | `<new section or explicit none>` |

### Required checklist

- [ ] The old document starts with `<!-- doc-class: frozen -->`.
- [ ] A `SUPERSEDED–FROZEN` banner names the new authority and known-false rules.
- [ ] Every affected section appears in the disposition table.
- [ ] `STANDARDS.md` § Canonical documents links the new fact owner.
- [ ] All four changes are present in this one pull request.
- [ ] Content below the frozen banner and all frozen section anchors are byte-identical.
<!-- END SUPERSESSION RECORD -->
```

Do not delete or renumber the old document. If the new document does not own a displaced fact,
write `SUPERSEDED WITHOUT REPLACEMENT` and `none`; never invent a replacement pointer.

## Worked example: the five-document 6767 reconciliation

This is a normalized example of the required record shape, not a claim that the historical
ratification and freeze changes landed atomically. It records all five standards that 727 § 0
already supersedes and freezes. Future supersessions must land the four components in one PR.

<!-- BEGIN SUPERSESSION RECORD -->

## Supersession record: 6767-a/c/d/e/h to 727

- **Atomic PR:** A conforming transaction carries every checked item below in one pull request.
- **Frozen document(s):** `000-docs/6767-a-SPEC-DR-STND-claude-code-plugins-standard.md`,
  `000-docs/6767-c-DR-STND-claude-code-extensions-standard.md`,
  `000-docs/6767-d-AT-APIS-claude-code-extensions-schema.md`,
  `000-docs/6767-e-WA-WFLW-extensions-validation-ci-gates.md`, and
  `000-docs/6767-h-SPEC-DR-STND-claude-code-extensions-master.md`.
- **Superseding document:** `000-docs/727-AT-ARCH-master-modernization-blueprint.md`
- **Frozen header:** `<!-- doc-class: frozen -->` followed by the existing
  `SUPERSEDED–FROZEN` banner.
- **STANDARDS.md Canonical documents pointer:** the Platform master standard row links
  `000-docs/727-AT-ARCH-master-modernization-blueprint.md`.

### Section disposition

| Superseded section                    | Disposition                    | New authority                      |
| ------------------------------------- | ------------------------------ | ---------------------------------- |
| 6767-a canonical platform claim       | REPLACED                       | 727 § 0 and § 11                   |
| 6767-c CSV-only tool rule             | REVERSED                       | 727 § 0 and § 5                    |
| 6767-d CSV-only schema rule           | REVERSED                       | 727 § 0 and § 5                    |
| 6767-e CSV-only validation rule       | REVERSED                       | 727 § 0 and § 5                    |
| § 1 plugin and skill anatomy          | CARRIED FORWARD                | 727 § 0, section-level disposition |
| Invariant 1, CSV-only `allowed-tools` | REVERSED                       | 727 § 0 and § 5                    |
| § 2.1, § 3.1, and § 5 required fields | REPLACED                       | 727 § 0 and § 5                    |
| § 4.3 website gates                   | REPLACED                       | 727 § 0 and § 11                   |
| Obsolete tooling references           | SUPERSEDED WITHOUT REPLACEMENT | none                               |

### Required checklist

- [x] The old document starts with `<!-- doc-class: frozen -->`.
- [x] Its `SUPERSEDED–FROZEN` banner names 727 and the known-false rules.
- [x] 727 § 0 disposes all affected 6767-a/c/d/e/h claims and sections.
- [x] `STANDARDS.md` § Canonical documents links 727 as the platform master standard.
- [x] This normalized record binds all four components into one review shape.
- [x] Frozen prose-anchor tests preserve the body and section namespace.
<!-- END SUPERSESSION RECORD -->

## Reviewer checklist

1. Run the checker against the completed record; a missing component must exit non-zero with a
   stable reason code.
2. Run corpus mode and confirm the new record is discovered from the tracked-document inventory.
3. Diff the old document against the base after removing only the newly prepended class marker and
   banner. Content below the banner must be byte-identical.
4. Run `node scripts/check-doc-authority.mjs` and the frozen prose-anchor suite.
5. Verify the complete PR diff contains the frozen header, disposition, canonical pointer, and
   completed record together.
6. Return the PR if any component is deferred to a follow-up.
