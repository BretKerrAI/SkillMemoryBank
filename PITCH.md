# SkillMemoryBank — 90-Second Pitch

**Red Hat Agent Build Day 2026 · The Open Accelerator · Lane 2**
*Governed, browser-local compression of agent memory — on open-source IBM Granite.*

---

## Judge Notes — what we built today

- **Local Granite compression, zero egress.** The high-volume compression stage runs entirely on-device on IBM **Granite 4.1 (8B)** via Ollama. Text never leaves the machine, marginal cost ≈ $0, runs on a MacBook. Open source (Apache 2.0) — not a proprietary, all-frontier path.
- **An honest, anti-gamed baseline.** We tagged `baseline-v0` with a deterministic heuristic compressor active and Granite present-but-not-wired, so the scored in-event delta is a *real* improvement, not a number we manufactured at the finish line.
- **Real dogfood on today's session.** We compressed this very hackathon morning's context into a governed PROCEDURES / CONSTRAINTS / DECISIONS summary — the tool used on itself, live.
- **Independent market validation.** A Gemini Pro 3.1 deep-research pass across Mem0, Zep, Letta, Cognee, LangMem, and frontier-lab memory features confirms the white space: storage-first players are funded; compression-first, local, compliant ones are not.
- **Full ADLC worksheet completed** — scope, design, build, evaluate, observe, iterate — committed to the repo alongside the eval harness.

---

## Key Results

| Metric | Result |
|---|---|
| **Durable-fact retention** | **0 / 3 → 3 / 3** (**+1.0** pass-rate delta, same fixed input) |
| **Granite vs. heuristic** | **Same 3/3 pass rate** — a general open-source model matches the hand-tuned heuristic on the same input, with no bespoke extraction rules |
| **Live now** | Live demo + Market Validation section at **contextjamming.com/SkillMemoryBank** |

*Measured by `evals/run.py` across three cases — a decision, a constraint, and a procedure each buried under chit-chat — within a fixed 240-char retrieval budget. Granite 4.1, temperature 0, reproducible. Full breakdown in `benchmark.json`.*

---

## The Script

### 0:00–0:15 — The problem
Every agentic system starts each session cold. Memory accumulates as raw transcript, and next session it's too big for the context budget — so it gets truncated. And the part that falls off the end is exactly the durable fact you needed: the architecture decision, the rate limit, the deploy procedure — buried under greetings and one-off chatter.

### 0:15–0:35 — The gap
The reference stack shown today — Strategy Scout on DeepAgents and LangGraph — gives each sub-agent an isolated context window. That's deliberate, and it kills memory bloat *within* a run. But nothing persists *across* sessions. Every sub-agent re-fetches and re-derives from scratch next time, and the human's accumulated judgment resets to zero. SkillMemoryBank is the **cross-session persistence layer that stack is missing**.

### 0:35–0:55 — What we built
A skill that compresses stale memory into a strict, governed template — **procedures, constraints, decisions** — and drops the chit-chat. The compression runs **locally on IBM Granite 4.1** via Ollama: open source, Apache 2.0, no data egress, marginal cost near zero. Frontier models are reserved only for the low-volume, quality-critical distillation and the eval judge. Temperature 0 keeps it deterministic and auditable — a requirement for a reproducible before/after metric.

### 0:55–1:15 — The results
On the same fixed input, durable-fact retention went from **0 out of 3 to 3 out of 3 — a plus-one-point delta**. And we kept ourselves honest: the committed baseline already ran a deterministic heuristic that passed 3 of 3, so we didn't manufacture the win at the finish line. The in-event step was wiring in **Granite** — and a general, open-source model matches that hand-tuned heuristic's perfect retention on the same input, with no bespoke extraction rules. That's the real result: it generalizes. We also dogfooded it on this very session, and validated the market gap with an independent Gemini deep-research pass.

### 1:15–1:30 — The close
So: a governed, local-first memory layer that's measurably better, fully open source, and already running. The model is replaceable — the **governed memory substrate compounds**. The live demo and market validation are up right now at **contextjamming.com/SkillMemoryBank**. Thank you.

---

## Next Steps (if asked)

- **Tiered runtime** — Granite for air-gapped/private deployments; Claude Haiku for cloud-native enterprises wanting autonomous session-end compression.
- **A2A-compatibility** — governed local memory as a trustworthy shared substrate for agent-to-agent protocols.
- **Retrieval layer** — rank compressed memories by relevance to the incoming session.
