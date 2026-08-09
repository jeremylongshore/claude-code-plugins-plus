# MAST — the 14 failure modes

Source: Cemri et al., **"Why Do Multi-Agent LLM Systems Fail?"** (arXiv:2503.13657, NeurIPS 2025).
The Multi-Agent System Failure Taxonomy (MAST) was derived from over 1,600 annotated traces across
multiple multi-agent frameworks. Mode names and identifiers below follow the paper.

## FC1 — System design issues

Defects in how the system was specified, staffed, or bounded. The fix belongs to the system author, not
to any individual agent's prompt.

| Mode | Name | Signature in a trace |
| --- | --- | --- |
| FM-1.1 | Disobey task specification | Output violates a stated constraint that was present in the agent's input |
| FM-1.2 | Disobey role specification | An agent does another agent's job — a researcher writing prose, a reviewer editing |
| FM-1.3 | Step repetition | The same step re-executed with no new information between attempts |
| FM-1.4 | Loss of conversation history | An agent contradicts or forgets something established earlier in the same run |
| FM-1.5 | Unaware of termination conditions | The run continues past the point where it should have stopped, or never stops |

**FM-1.2 versus FM-2.3** is the distinction most often confused. FM-1.2 is an agent doing the wrong
*job*; FM-2.3 (task derailment) is agents collectively drifting off the *task*. One is a role problem,
the other is a conversation problem, and they route to different fixes.

**FM-1.5** is the mode behind most runaway loops. Note that the fix is a termination condition, not a
rate limit — a limiter makes an unterminated run cheaper, not correct.

## FC2 — Inter-agent misalignment

Defects that live in the conversation between agents. **Neither agent's prompt can fix these**, because
neither agent is individually wrong. This category is why coordination is an architectural layer rather
than an emergent property.

| Mode | Name | Signature in a trace |
| --- | --- | --- |
| FM-2.1 | Conversation reset | Context is discarded mid-run and an agent restarts from nothing |
| FM-2.2 | Fail to ask for clarification | An agent proceeds on an ambiguous input instead of asking |
| FM-2.3 | Task derailment | The exchange drifts to an adjacent task and never returns |
| FM-2.4 | Information withholding | An agent has information a peer needs and does not pass it on |
| FM-2.5 | Ignored other agent's input | A message arrives and has no effect on the recipient's behaviour |
| FM-2.6 | Reasoning-action mismatch | An agent states one plan and then does something else |

**FM-2.4 (information withholding)** is the highest-value mode to learn, because it presents as a defect
in the *receiving* agent. The receiver produces bad output; the cause is the sender's incomplete
handoff. Teams tune the receiver for weeks.

**FM-2.5 (ignored input)** is what a structured handoff with an explicit acknowledgment step is for. In
a trace it looks like a message that arrives and changes nothing downstream.

**FM-2.6 (reasoning-action mismatch)** is the one that survives prompt improvements, because the plan
the agent states is usually correct. The gap is between the stated plan and the executed action.

## FC3 — Task verification

Defects in checking the result. The smallest category and the one most often absent entirely rather than
broken.

| Mode | Name | Signature in a trace |
| --- | --- | --- |
| FM-3.1 | Premature termination | The run ends before the task is complete, often with a confident partial result |
| FM-3.2 | No or incomplete verification | Output is returned unchecked, or checked on the wrong property |
| FM-3.3 | Incorrect verification | A verifier ran and passed something wrong |

**FM-3.2 versus FM-3.3** decides the fix. FM-3.2 means *add* a verifier. FM-3.3 means the verifier
exists and is wrong — a more dangerous state, because the system reports confidence it has not earned.

## Using the taxonomy

- **Name the mode, cite the identifier.** "FM-2.4 information withholding at turn 4" is actionable;
  "coordination problem" is not.
- **Classify the category first.** The category routes the fix to a level. Getting the exact mode wrong
  within the right category still sends the fix to the right place.
- **One primary mode, at the divergence point.** Later modes are usually consequences. Fixing a
  consequence leaves the cause running.
- **It is descriptive, not predictive.** MAST names what went wrong in traces that already failed. It
  does not forecast failure, and it should not be cited as though it does.
