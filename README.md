# SkillMemoryBank

**Governed, browser-local compression of agent memory.** An [Agent Skill](https://agentskills.io)
that compresses stale cross-session memory into durable summaries — preserving
reusable **procedures, constraints, and decisions** while dropping chit-chat —
so an agent's hard-won context survives the next session's context budget.

> Red Hat **Agent Build Day 2026 — Lane 2** submission. Improving an existing
> skill, measured by a committed before/after eval delta on the same input.

## The problem

Agent memory accumulates as raw transcript. Next session, it's too big for the
context budget, so it gets truncated — and the durable fact you actually needed
(the architecture decision, the rate limit, the deploy procedure) is the part
that falls off the end, buried under greetings and one-off chatter.

## The gap (what the reference architecture misses)

Red Hat's reference agent stack — Strategy Scout, built on DeepAgents / LangGraph
— gives each sub-agent an **isolated context window** per session. That's
deliberate: it eliminates memory bloat *within* a run. But nothing persists
*across* sessions. Every sub-agent re-fetches and re-derives from scratch the
next run, and the orchestrator's prioritization schema resets when the session
ends — the "Sarah" persona has to re-explain her constraints every single time.

SkillMemoryBank is the **cross-session persistence layer that stack is missing**.
"Loops, not prompts": it carries domain knowledge — and the *prioritization
schema* — forward across sessions. It doesn't just remember *what* Sarah did; it
remembers *how Sarah decided*. Browser-local, no egress, auditable, and open
source (Apache 2.0) on IBM Granite — not a proprietary, all-Gemini path.

## The approach

A **hybrid local + frontier** architecture. The high-volume, privacy-sensitive
compression stage runs **locally** on IBM **Granite 4.1** via Ollama — text
never leaves the device, marginal cost ≈ $0. Frontier models (Claude) are
reserved for low-volume, quality-critical distillation and a final eval judge.
See [`MODEL_SELECTION.md`](MODEL_SELECTION.md).

Compression collapses memory into a strict template:

```
PROCEDURES:
- <imperative step>
CONSTRAINTS:
- <rule that must always hold>
DECISIONS:
- <choice made and the reason>
```

## Engines

| Engine | Description | Role |
|--------|-------------|------|
| `none` | Raw memory truncated to budget | without-skill baseline |
| `deterministic` | Pure-function heuristic — extract durable lines, drop chit-chat | **committed baseline** |
| `granite` | Same text routed through `granite4.1:8b` | **in-event improvement** |

The committed baseline uses the deterministic heuristic (no model). The scored
in-event delta is flipping the engine to `granite` and re-running the eval.

## Quickstart

```bash
# 1. Local model (one-time)
ollama pull granite4.1:8b      # ~5GB; granite4.1:3b (~2GB) is the RAM fallback
ollama run granite4.1:8b "ok"  # confirm it serves on localhost:11434

# 2. Compress a memory block
python scripts/compress.py --engine deterministic < stale_memory.txt
python scripts/compress.py --engine granite       < stale_memory.txt   # in-event

# 3. Run the with/without eval -> benchmark.json
python evals/run.py                  # baseline (deterministic)
python evals/run.py --engine granite # in-event leg
```

No API key and no network egress are required for the deterministic baseline or
the Granite leg — both run locally.

## Results

`evals/run.py` measures durable-fact retention within a fixed retrieval budget
across 3 cases where a decision, a constraint, and a procedure are each buried
under chit-chat. **Granite 4.1** compression (`granite4.1:8b`, temperature 0)
vs. no skill, on the same fixed input:

| Arm | Pass rate |
|-----|-----------|
| Without skill (raw memory, truncated to budget) | **0 / 3** (0.0) |
| With skill (Granite 4.1 compression) | **3 / 3** (1.0) |
| **Delta** | **+1.0** |

Average compression **0.618** (~62% smaller) with every durable fact preserved.
Full per-case breakdown in [`benchmark.json`](benchmark.json).

## Layout

```
SKILL.md              the Agent Skill (frontmatter + instructions)
MODEL_SELECTION.md    why Granite 4.1; runtime routing + cost/latency table
README.md             this file
LICENSE               Apache-2.0
scripts/
  granite_call.py     minimal Ollama wrapper — the compression worker
  compress.py         engine dispatch (none / deterministic / granite)
evals/
  evals.json          3 with/without retention cases
  run.py              harness -> benchmark.json
references/
  granite-prompts.md  copy-paste Granite 4.1 prompts + Ollama test harness
```

## License

[Apache-2.0](LICENSE). © 2026 Bret Kerr / ACRA Insight LLC.
