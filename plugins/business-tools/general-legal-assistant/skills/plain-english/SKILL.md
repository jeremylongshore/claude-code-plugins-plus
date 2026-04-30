---
name: plain-english
description: 'Translates every clause of a contract into plain language at an 8th-grade

  reading level and flags deliberately confusing language patterns. Use when

  a user says "explain this contract", "what does this mean", or needs a

  non-lawyer to understand an agreement. Trigger with "/plain-english" or

  "translate this contract to plain English".

  '
allowed-tools: Read, Glob, Grep
version: 1.0.0
author: Intent Solutions <jeremy@intentsolutions.io>
license: MIT
tags:
- legal
- contracts
- plain-language
- readability
- translation
- accessibility
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Plain English — Legalese to Plain Language Translator

Translates every material clause in a contract into clear, jargon-free language
that a non-lawyer can understand, while flagging clauses that appear to be
deliberately confusing or that hide significant obligations behind complex
wording.

## Overview

Legal language exists for precision, but it is also routinely weaponized. Dense
legalese discourages the other party from reading carefully, hides unfavorable
terms behind jargon, and creates information asymmetry that favors the drafter.

This skill neutralizes that advantage by producing a clause-by-clause
translation at an 8th-grade reading level (Flesch-Kincaid grade 8 or below),
accompanied by flags that highlight where the original language is not just
complex but strategically confusing.

The goal is not to replace legal review but to ensure the signer actually
understands what they are agreeing to before deciding whether to consult an
attorney.

## Prerequisites

- A contract must be provided as a file path or pasted text.
- No special knowledge from the user is required — the entire point of this
  skill is to make the contract accessible to anyone.

## Instructions

1. **Read the full contract.** Use the Read tool if a file path is provided.

2. **Identify all material clauses.** Break the contract into individual
   sections and clauses. Skip boilerplate headers, signature blocks, and
   formatting-only content.

3. **Translate each clause to plain English.** For every material clause:
   - Rewrite in short, direct sentences (target: 8th-grade reading level).
   - Replace legal jargon with everyday equivalents:
     - "indemnify and hold harmless" -> "pay for any losses and protect from lawsuits"
     - "notwithstanding anything to the contrary" -> "even if other parts of this contract say differently"
     - "shall not be construed to" -> "does not mean"
     - "in the event of" -> "if"
     - "prior to" -> "before"
     - "pursuant to" -> "under" or "according to"
     - "herein", "hereof", "hereunder" -> "in this contract"
     - "mutatis mutandis" -> "with the necessary changes"
   - Preserve the legal meaning — do not simplify away obligations or rights.
   - State who must do what, by when, and what happens if they do not.

4. **Apply the 5 flag types.** After translating each clause, check whether any
   of these flags apply:

   | Flag | Icon | When to Apply |
   |------|------|---------------|
   | **DELIBERATELY CONFUSING** | :no_entry: | Language is unnecessarily complex in ways that obscure meaning; simpler alternatives exist and the drafter chose not to use them |
   | **WATCH OUT** | :warning: | Clause creates a significant obligation, cost, or restriction that a casual reader would likely miss |
   | **SURPRISINGLY BROAD** | :mag: | Scope is wider than what a reasonable person would expect from the section heading or context |
   | **HIDDEN OBLIGATION** | :lock: | An obligation is embedded inside a clause that appears to be about something else (e.g., a payment term hidden in a definitions section) |
   | **CONTRADICTS EXPECTATIONS** | :boom: | The clause says the opposite of what most people would assume based on the section title or common practice |

5. **Score overall readability.** After translating all clauses, calculate:
   - Estimated Flesch-Kincaid grade level of the original document
   - Number of jargon terms replaced
   - Number of flags raised (broken down by type)
   - Percentage of clauses flagged

6. **Generate the quick-reference summary.** Create a one-page "What You Are
   Actually Agreeing To" summary covering:
   - What you must do (your obligations)
   - What you must not do (your restrictions)
   - What they must do (their obligations)
   - What happens if things go wrong (liability, termination, disputes)
   - What you give up (waivers, assignments, releases)
   - How long this lasts and how to get out

## Output

**Filename:** `PLAIN-ENGLISH-{contract-name-or-type}.md`

```
# Plain English Translation
## Quick Reference: What You Are Actually Agreeing To
### Your Obligations
### Your Restrictions
### Their Obligations
### If Things Go Wrong
### What You Give Up
### Duration and Exit
## Readability Statistics
| Metric | Value |
## Clause-by-Clause Translation
### Section 1: [title]
**Original:** [quoted legalese]
**Plain English:** [translation]
**Flags:** [any applicable flags]
### Section 2: [title]
...
## Flag Summary
## Disclaimer
```

## Error Handling

| Failure Mode | Cause | Resolution |
|--------------|-------|------------|
| Untranslatable jargon | Highly specialized legal term with no plain equivalent | Provide the best approximation with a parenthetical noting the term is specialized |
| Ambiguous clause | Language is genuinely ambiguous even to legal professionals | Note that the clause has multiple possible interpretations and explain each |
| Missing context | Clause references external documents or schedules not provided | Note the dependency and translate what is available |
| Foreign language terms | Latin or other non-English legal phrases | Translate to English with the original term in parentheses |
| Extremely long contract | Document exceeds practical analysis limits | Prioritize flagged clauses and high-risk sections; note sections skipped |

## Examples

**Example 1 — SaaS Terms of Service clause:**

**Original:**
> Notwithstanding anything to the contrary herein, Company shall not be liable
> for any indirect, incidental, special, consequential, or punitive damages,
> including without limitation loss of profits, data, business opportunities,
> or goodwill, arising out of or in connection with this Agreement, whether
> based on warranty, contract, tort, or any other legal theory, even if Company
> has been advised of the possibility of such damages.

**Plain English:**
> Even if other parts of this contract seem to say differently: if something
> goes wrong because of this company's product or service, they will not pay
> for any losses beyond direct, immediate damage. They will not cover lost
> profits, lost data, missed business opportunities, or harm to your
> reputation — even if they knew these losses were possible.

**Flags:**
- :warning: **WATCH OUT** — This means if their software deletes your data,
  they owe you nothing for the data itself or the business impact. Only direct
  damages (like a refund of fees paid) would apply.
- :mag: **SURPRISINGLY BROAD** — "arising out of or in connection with" is
  broader than "caused by." This covers situations where their product was only
  tangentially related to the harm.

**Example 2 — Hidden obligation in definitions:**

**Original (from Definitions section):**
> "Services" shall mean the software platform and any configurations,
> customizations, or integrations developed by Client using the platform tools.

**Plain English:**
> "Services" means not just the software itself, but also anything you build
> using their tools. By defining your work as part of their "Services," other
> clauses about Services (like ownership, licensing, and liability) now apply
> to your custom work too.

**Flags:**
- :lock: **HIDDEN OBLIGATION** — This definition makes your custom work subject
  to the vendor's terms about "Services" throughout the contract.
- :boom: **CONTRADICTS EXPECTATIONS** — Most people would expect "Services" to
  mean what the vendor provides, not what the customer builds.

## Resources

- [Plain Language Action and Information Network (PLAIN)](https://www.plainlanguage.gov/)
  — U.S. federal government plain language guidelines and resources.
- [Federal Plain Writing Act of 2010](https://www.govinfo.gov/content/pkg/PLAW-111publ274/pdf/PLAW-111publ274.pdf)
  — Legal basis for plain language requirements in government communications.
- [Flesch-Kincaid Readability Standards](https://readable.com/readability/flesch-reading-ease-flesch-kincaid-grade-level/)
  — Readability scoring methodology reference.
- [CommonPaper Plain Language Contracts](https://commonpaper.com/) — Examples
  of contracts written in accessible language (CC BY 4.0).
- [Consumer Financial Protection Bureau — Plain Language Requirements](https://www.consumerfinance.gov/)
  — CFPB guidance on clear disclosure language.

---

**Legal Disclaimer:** This skill provides AI-generated plain-language
translations for informational and educational purposes only. Translations are
approximations — they aim for clarity but may not capture every legal nuance of
the original text. This does not constitute legal advice, create an
attorney-client relationship, or substitute for consultation with a qualified
attorney. The original contract language, not this translation, is what governs
the legal relationship between the parties.
