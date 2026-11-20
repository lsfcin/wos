---
name: prepare
description: >
  Turn a raw task into an optimized agent prompt: interviews for intent, classifies the task, recommends model and effort.
---

# /prepare

## Protocol

### Step 1 — Interview (Intention)

Analyze the user's raw prompt for **ambiguity intents**
If the prompt is ambiguous or high-stakes, interview the user **before** classifying.

Ask at most **3 short, contextualized questions** based on the user's prompt.

Stop the interview once the intent is clear. Do **not** ask about implementation details (the Claude will handle that).

### Step 3 — Classification & Recommendation

With clarified intent, classify the task:
- **Task type**: coding, research, writing, debugging, etc.
- **Complexity**: single-file vs multi-file, architectural, security, etc.
- **Ambiguity**: well-defined vs open-ended

Produce the final structured response:
- `optimized_prompt`: rewritten, specific, contextualized prompt (incorporating the interview answers) and asking for a plan
- `level`: recommended model level (`low`/`medium`/`high`/`max`)
- `effort`: recommended effort level (`low`/`medium`/`high`/`max`)
- `rationale`: one-sentence justification
- `interview`: leave opened the space for interviews if the agent needs 

### Flow routing
If the task is a multi-file coding feature (new behavior, not a trivial fix), recommend running it through `/craft` (the craft flow, `core/flows/craft/craft.md`) instead of a single optimized prompt — it handles clarify/plan/TDD/ship with per-task model routing.

### Level guide
- `low` / e.g., `haiku`: trivial fixes, one-liners, simple searches
- `medium` / e.g., `sonnet`: standard coding, debug, refactor
- `high` / e.g., `opus`: complex architecture, multi-file, deep reasoning
- `max` / e.g., `fable`: mission-critical, high-stakes, highly ambiguous

### Effort guide
- `low`: fast, terse, single-step, minimal tool use
- `medium`: balanced, some exploration, default
- `high`: thorough, multi-step, tests, edge cases
- `max`: exhaustive, full analysis, alternatives