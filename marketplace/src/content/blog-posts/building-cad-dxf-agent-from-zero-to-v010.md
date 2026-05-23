---
title: "Shipping a CAD Agent from Zero: DXF Parsing, Edit Engines, and LLM Planner Interfaces"
description: "How I built a local-first desktop application that lets a structural engineer edit 2D DXF drawings with natural language prompts — from DXF parser to LLM planner interface to v0.1.0 release."
date: "2026-02-14"
tags: ["ai-agents", "cad", "dxf", "architecture", "typescript", "llm-integration"]
featured: false
---
## The Problem

A structural engineer named Tony needs to edit CAD drawings. His workflow: open a DXF file, move some entities, update text labels, add block references, save to a new file. He does this hundreds of times. The edits are mechanical and repetitive.

The goal: let Tony type "move the column east by 2 feet" and have the software do it. Local-first, no cloud dependency for the core workflow, and never modify the original file.

## Architecture: Prompt to DXF

The pipeline is five steps: `User Prompt → LLM Planner → ChangeSet (JSON) → Validator → EditEngine → Save-As DXF`

The LLM never touches raw DXF. It receives a structured context about the drawing (entities, layers, blocks) and returns a structured changeset (a list of operations). The validator checks every operation against safety rules. The edit engine applies validated operations to an in-memory copy. The original file is never modified.

### The Planner Provider Interface

The most important architectural decision was abstracting the LLM behind a provider interface:

```python
class PlannerProvider(ABC):
    @abstractmethod
    def plan(self, prompt: str, drawing_context: dict) -> ChangeSet:
        """Generate a structured changeset from a user prompt and drawing context."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging and display."""
        ...

    @property
    def requires_api_key(self) -> bool:
        return True
```

Four implementations exist:

- **MockProvider** — Offline keyword matching. No API key needed. Fully functional for testing and CI.
- **GeminiProvider** — Vertex AI Gemini 2.5 Flash. Production LLM backend.
- **AgentProvider** — Tool-use agent following the Google ADK pattern.
- **ProxyAgentProvider** — Cloud Run proxy so end users skip GCP credential setup.

The `CAD_LLM_PROVIDER` environment variable selects the backend. Default is mock mode. This means:

- The full pipeline works offline. Tony can test the UI without an API key.
- CI runs the entire test suite in mock mode. No secrets needed for pull request checks.
- Adding a new LLM provider (OpenAI, Anthropic) means implementing one class with two methods.
- Live API tests run only on main branch pushes with Workload Identity Federation — no stored secrets.

## DXF Parsing: What the Schema Looks Like

DXF files are Autodesk's exchange format for 2D drawings. The `ezdxf` library handles the low-level parsing. The agent works with a normalized `DrawingContext`:

```python
@dataclass
class EntityRef:
    handle: str           # Unique DXF entity ID
    entity_type: str      # LINE, LWPOLYLINE, TEXT, MTEXT, INSERT, CIRCLE, ARC, etc.
    layer: str            # Layer name
    space: str            # "model" or layout name
    insert_point: tuple   # (x, y) coordinates
    text_content: str     # For TEXT/MTEXT entities
    block_name: str       # For INSERT (block reference) entities
    attributes: dict      # Extended data
```

The reader extracts entities from both model space and all named layouts (paper spaces), builds an entity index by handle, and maps layers to `LayerRule` objects with protected flags. Unsupported entity types (SPLINE, MLEADER) get recorded but don't crash the parser.

The context sent to the LLM planner includes entities, layers, available blocks, and layout information — everything the planner needs to generate valid operations without seeing raw DXF markup.

## Operations and the Validator

Four operation types cover Tony's editing needs:

- **MOVE_ENTITY**: Translate by dx/dy
- **EDIT_TEXT**: Update text content
- **DELETE_ENTITY**: Remove from drawing
- **ADD_BLOCK**: Insert a block reference with scale and rotation

Every operation goes through the validator before the edit engine touches anything:

```python
class Validator:
    def validate(self, changeset: ChangeSet, context: DrawingContext) -> ValidationResult:
        # Protected layer enforcement (TITLE, TITLEBLOCK, SEAL, REVISION)
        # Entity existence checks by handle
        # Parameter validation (move requires numeric dx/dy)
        # NaN/Inf detection for coordinates
        # Move distance warnings (configurable max)
```

The validator returns `blockers` (prevent execution) and `warnings` (informational). Protected layers are non-negotiable — the LLM cannot modify title blocks, seals, or revision tables regardless of what the user asks for.

## Revision Notes: Deterministic, Never LLM-Generated

When operations are applied, the system generates revision notes from the operation metadata:

```python
# Examples of deterministic notes:
# "REV 8 - Moved entity east 2'-0\""
# "REV 8 - Updated text to 'New Label'; Deleted entity"
# "REV 5 - Inserted block DOOR"
```

These notes are inserted as MTEXT on a configurable `AI_REV_NOTES` layer. They never contain freeform LLM text. The note content is computed from what the edit engine actually did — not from what the LLM said it would do. This distinction matters: if the LLM hallucinates an operation that the validator blocks, no misleading revision note gets created.

## The Desktop Shell

The PySide6 desktop application gives Tony a workflow that matches how he already works:

1. **Open DXF** — load the file, see entity count and layer info
2. **Type a prompt** — natural language describing the edit
3. **Plan & Preview** — the planner returns operations, the validator checks them
4. **Review** — per-operation approve/reject checkboxes. Tony can selectively reject operations before they apply.
5. **Apply & Save As** — writes to a new DXF file with revision notes

Undo/redo (Ctrl+Z / Ctrl+Y) works through an `EditHistory` stack. The UI shows layout tabs for model space and paper spaces. Export supports DXF, PNG, and PDF.

The key UX insight: Tony doesn't want to blindly trust the AI. The per-operation checkboxes let him review what the planner proposed and reject anything that looks wrong before it touches the drawing.

## CI/CD from Day One

The project had GitHub Actions CI before it had a working UI. Three workflows:

**ci.yml** — Lint (ruff), typecheck (mypy strict), test (pytest on Ubuntu + Windows, Python 3.11 & 3.12), and live API tests on main pushes only with Workload Identity Federation for GCP auth.

**build-windows.yml** — Tag-triggered releases. Runs unit tests, builds with PyInstaller, verifies bundle size (>10MB sanity check), smoke tests the executable in headless mode (`QT_QPA_PLATFORM=offscreen`), builds an Inno Setup installer, uploads to GitHub release.

**security.yml** — Bandit code scanning and pip-audit dependency scanning.

Pre-commit hooks enforce ruff formatting, YAML validation, and private key detection. The `.pre-commit-config.yaml` also blocks direct commits to main.

Coverage threshold: 65% minimum. 222 tests at release — unit tests, integration tests with a `ScriptedAgentProvider`, smoke tests through mock planner, and golden trajectory tests that verify correct agent behavior per prompt type.

## Three Critical MVP Bugs

Real-world structural DXFs broke three assumptions:

1. **Dimension entities** with missing insert points or definition points. The parser assumed every dimension had coordinates. Fix: graceful fallback when attributes are missing.

2. **HATCH entities** with complex boundary paths. Computing centroids for hatch entities needed a fallback when the standard centroid algorithm failed on degenerate paths.

3. **MLEADER entities** with nested text contexts. Extracting text from multileader entities required traversing a context hierarchy that the initial parser didn't handle.

All three bugs were found by loading Tony's actual production DXF files — files with thousands of entities, dozens of layers, and entity types that don't appear in textbook examples. The mock provider catches logic bugs. Real files catch assumption bugs.

## Takeaways

The planner provider interface was the first thing I built, and it paid off immediately. Every subsequent feature — the validator, the edit engine, the UI, the tests — worked against the interface, not against a specific LLM. When I switched from mock to Gemini, zero application code changed.

If I'd built the planner tightly coupled to Gemini, I'd have needed API keys just to run tests. Instead, CI runs the entire suite in mock mode. No secrets, no flaky network calls, no rate limit surprises.

The validator turned out to be more important than the planner itself. LLMs occasionally propose nonsensical operations — moving entities to NaN coordinates, editing text on protected layers. The validator catches all of it before the edit engine touches the drawing.

And the three MVP bugs found by loading Tony's real structural DXFs? None of them would have surfaced with synthetic test fixtures. Dimension entities with missing attributes, hatch entities with degenerate boundary paths, multileader text extraction — these are things you only discover when you test with production files.
