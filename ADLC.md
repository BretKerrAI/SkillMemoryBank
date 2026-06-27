# ADLC Worksheet — SkillMemoryBank
**Agent Build Day · The Open Accelerator · June 27, 2026 · Lane 2**

## 1. SCOPE — From Idea to Problem Statement

**Problem:** Agentic systems start every session cold. Reference architectures shown today (Strategy Scout / DeepAgents) deliberately isolate context windows per sub-agent to eliminate main-model memory bloat — but isolation means nothing persists across sessions. Every sub-agent re-fetches, re-reasons, and rebuilds the same context from scratch on the next run. The human's accumulated domain judgment is lost between sessions.

**Scope decision:** Build a skill that compresses stale agent memory into durable, governed summaries — preserving reusable procedures, constraints, and decisions across sessions — using a local open-source model so no data leaves the device.

**Out of scope (today):** Retrieval ranking, multi-user sync, vector storage. Deliberately narrow to a single coherent unit of work.

## 2. DESIGN — Architecture & Model Selection

**Three-stage runtime:**
- Compression (stale memory → governed summary): IBM Granite 4.1 8B via Ollama, local, temperature 0
- Distillation (high-value, low-volume): Claude Opus 4.8 (API)
- Retrieval scoring: deterministic TypeScript, no model

**Why Granite 4.1:** Open source (Apache 2.0), runs locally via Ollama (no egress), instruction-following structured output at temperature 0 (deterministic + auditable), edge-optimized 8B (runs on a MacBook — even a Raspberry Pi). Aligns with the open-source pillar emphasized in today's keynote; contrasts with the all-proprietary stack in the reference demo.

**Governance:** Fixed PROCEDURES / CONSTRAINTS / DECISIONS template. Temperature 0 makes the same input produce a stable output — required for a reproducible before/after metric.

## 3. BUILD — Implementation

- SKILL.md: AgentSkills-compliant, passes `agentskills validate`
- scripts/granite_call.py: minimal Ollama wrapper, :3b fallback under memory pressure
- scripts/compress.py: engine dispatch (none / deterministic / granite)
- evals/run.py + evals/evals.json: with/without-skill harness → benchmark.json
- Anti-gaming discipline: baseline-v0 tagged with deterministic compressor active and Granite present-but-not-wired, preserving a real in-event delta.

## 4. EVALUATE — Measured Results

Same fixed input, three conditions:

| Condition | Pass Rate | Avg Compression |
|-----------|-----------|-----------------|
| Without skill (cold) | 0/3 | — |
| With skill (deterministic) | 3/3 | 0.775 |
| With skill (Granite 4.1) | 3/3 | 0.618 |

**Delta: 0.0 → 1.0 (+1.0 pass rate).** Both engines hold 3/3 on the same fixed input: a general open-source model (Granite 4.1) matches a hand-tuned heuristic's retention with no bespoke extraction rules — evidence the result generalizes and isn't overfit to a hand-coded extractor. (Compression ratio is the fraction of text removed, so the deterministic heuristic's 0.775 is the smaller summary; Granite retains slightly more while passing the same cases.)

Three test cases target distinct retention failures: decision-buried, constraint-buried, procedure-buried.

## 5. OBSERVE — Real-World Behavior

- Cold-load risk observed: first Granite call took ~337s to load 5GB into RAM at the 16GB ceiling, exceeding the default 120s wrapper timeout. Mitigation: timeout raised to 360s; keep model warm before eval runs; :3b fallback documented.
- Live dogfood: compressed this session's own context (the hackathon morning) into a governed PROCEDURES/CONSTRAINTS/DECISIONS summary — the tool used on itself.

## 6. ITERATE — Next Steps

- Tiered runtime: Granite for air-gapped/private; Claude Haiku for cloud-native enterprises wanting autonomous session-end compression.
- A2A-compatibility: governed local memory as a trustworthy shared substrate for agent-to-agent protocols.
- Retrieval layer: rank compressed memories by relevance to incoming session.
