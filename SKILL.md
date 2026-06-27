---
name: skill-memory-bank
description: >
  Compress stale agent memory into durable, governed summaries using a local
  IBM Granite 4.1 model via Ollama, preserving reusable procedures, constraints,
  and decisions while dropping chit-chat and one-off context. Use when agent
  context from prior sessions must be retrieved, compressed, distilled, or
  persisted browser-local across sessions, when memory exceeds the context
  budget, or when measuring with-skill vs without-skill memory retention.
license: Apache-2.0
allowed-tools: Bash(python:*) Read Write
metadata:
  version: 1.0.0
  author: Bret Kerr (ACRA Insight LLC)
  project: ContextJamming
  domain: agent-memory
  event: Red Hat Agent Build Day 2026
  lane: "2"
---

# SkillMemoryBank

Governed compression of agent skill memory. SkillMemoryBank takes the
accumulated memory payload from prior sessions, compresses the stale portions
into a durable template — **PROCEDURES / CONSTRAINTS / DECISIONS** — and returns
a smaller payload that survives the next session's context budget. Compression
runs **locally** (Granite 4.1 via Ollama), so memory never leaves the device:
that is the "governed, browser-local memory persistence" guarantee.

## When to use

- Agent context from prior sessions must be retrieved, compressed, or updated.
- Accumulated memory exceeds the context/retrieval budget and durable facts are
  being lost to truncation.
- You need a reproducible with-skill vs without-skill memory-retention measure.

## Engines (and the baseline/in-event split)

| Engine | What it is | Status |
|--------|-----------|--------|
| `none` | Identity — raw memory, truncated to budget | the without-skill arm |
| `deterministic` | Pure-function heuristic; extracts durable lines, drops chit-chat | **committed baseline (default)** |
| `granite` | Routes the same text through `granite4.1:8b` (Ollama) | **in-event leg** — present, not default |

The baseline is the deterministic heuristic — **no model touches the text.** The
scored Lane 2 delta is moving the compression engine `deterministic → granite`
in-event and re-running the eval. `scripts/granite_call.py` is present and
smoke-tested at baseline but is *not* wired as the default engine (anti-gaming:
the improvement must be in-event).

## Steps

1. **Retrieve** the stale memory block(s) from the prior session.
2. **Compress** through the active engine:
   ```bash
   python scripts/compress.py --engine deterministic < stale_memory.txt
   # in-event:
   python scripts/compress.py --engine granite < stale_memory.txt
   ```
   Output keeps only durable lines under the template; greetings, chit-chat, and
   one-off context are dropped. No facts are invented.
3. **Persist** the compressed summary as the session's memory of record.
4. **Measure** retention before/after on the same fixed input:
   ```bash
   python evals/run.py                 # baseline (deterministic)
   python evals/run.py --engine granite  # in-event leg
   ```
   `run.py` writes `benchmark.json` (pass-rates per arm + compression ratio).

## Output template

```
PROCEDURES:
- <imperative step>
CONSTRAINTS:
- <rule that must always hold>
DECISIONS:
- <choice made and the reason>
```
Sections with no content are omitted. Granite runs at **temperature 0** with a
120-token cap so the leg is reproducible (the with/without delta needs a stable
before/after — a non-deterministic compressor poisons it).

## Gotchas

- **Granite is the worker, not the coder.** `granite4.1:8b` is invoked at runtime
  via Ollama's local API; it does not edit the repo.
- **RAM ceiling (16GB).** `granite4.1:8b` ≈ 5GB resident. The moment it swaps,
  fall back: `--model granite4.1:3b`. Don't debug memory pressure — route around
  it. Keep one Granite model resident at a time.
- **Ollama must be serving.** `ollama run granite4.1:8b "ok"` before relying on
  the `granite` engine. The `deterministic` engine needs no model and always runs.
- **Never invent facts.** Compression may only shorten reusable content; it must
  not fabricate or reorder durable decisions.
- **Determinism.** Always temperature 0 for any committed/eval numbers.

## References

- `MODEL_SELECTION.md` — why Granite 4.1, runtime routing table, $0-marginal cost.
- `references/granite-prompts.md` — copy-paste Granite prompts + Ollama harness.
- `scripts/granite_call.py` — minimal Ollama wrapper (the compression worker).
- `evals/run.py` — with/without harness → `benchmark.json`.
