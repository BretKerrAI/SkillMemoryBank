# Model Selection

SkillMemoryBank is a **hybrid local + frontier** system. Two decisions, kept
separate on purpose: which model *writes the code* (build-time) and which models
*ship inside the skill* (runtime). This document is about runtime — what the
pipeline actually invokes.

## Runtime routing

| Stage | Model | Tier | Why | Cost | Latency |
|-------|-------|------|-----|------|---------|
| Compression / stale-memory summary | **granite4.1:8b** (Ollama, local) | local | High volume, latency- and privacy-sensitive; text never leaves the device. | ≈ $0 marginal | Local, sub-second |
| Distillation (conversation → skill) | Claude Opus 4.8 (API) | frontier | Quality-critical, low volume; judgment pays off once. | High/call, low total | Seconds, off hot path |
| Retrieval scoring / graph pulse | deterministic TS/Py | deterministic | Pure functions; no model needed; reproducible. | Zero | Microseconds |
| Eval judge (blind coherence) | Sonnet 4.6 iterating → Opus 4.8 final | frontier | Cheap impartial judge while iterating; one Opus pass for committed numbers. | Moderate, eval-time | Seconds, offline |

The in-event change vs the committed baseline: the **compression row** moves from
"deterministic heuristic, no model" → real `granite4.1:8b`. That move *is* the
Lane 2 delta.

## Why IBM Granite 4.1 for compression

**Edge-optimized.** The 8B Granite 4.1 (`granite4.1:8b`, ≈5GB Q4_K_M) runs on a
single laptop through Ollama at `localhost:11434`. Memory compression is a
high-frequency operation that runs every session — keeping it on a small local
model makes it fast, free, and **on-device**. A `granite4.1:3b` (≈2GB) variant is
the drop-in fallback the moment a 16GB machine starts swapping; swap the model
string and keep moving.

**Open source / Apache 2.0.** Granite 4.1 ships under **Apache 2.0**. For a
*governed* memory system this is load-bearing: no usage restrictions on
processing internal or regulated content, weights can be vendored, audited, and
pinned for reproducible compression, and there is no third-party API's terms,
uptime, or data-retention policy sitting in the path of every memory write.

**Red Hat ecosystem alignment.** Granite is IBM/Red Hat's open model family and
is first-class in the **Red Hat AI / RHEL AI / OpenShift AI** stack. For any
deployment standardized on Red Hat tooling, Granite is the supported,
ecosystem-native choice — same supply chain, same provenance and governance
story, the model Red Hat backs for on-prem and edge inference. SkillMemoryBank is
therefore deployable inside a Red Hat-governed environment without an
out-of-ecosystem dependency. (Built for **Red Hat Agent Build Day 2026**, Lane 2.)

**Deterministic by contract.** All compression calls run at **temperature 0**.
The with/without eval delta requires the *same input* to produce a *stable*
before/after; a non-deterministic compressor poisons the measured delta, so
determinism is a hard requirement, not a nicety.

## Why not a hosted frontier model for compression

- **Governance:** sending memory to a hosted API breaks the on-device guarantee
  and creates a retention/audit surface for every memory write.
- **Cost & latency:** compression runs constantly; a local 8B is cheaper and
  lower-latency than per-call API billing.
- **Reproducibility:** a pinned local model at temperature 0 gives deterministic
  compression a versioned hosted endpoint cannot guarantee over time.

Frontier models remain the right tool for the agent's *reasoning* and for
one-shot distillation/judging. They are overkill — and a governance liability —
for the narrow, high-volume task of shortening stale memory.

## Operational notes

- Endpoint: `POST http://localhost:11434/api/chat` — no key, no egress.
- Model tag: `granite4.1:8b`; fallback `granite4.1:3b`.
- Determinism: `"options": {"temperature": 0}` on every call.
- Pull once: `ollama pull granite4.1:8b`. Keep only one Granite model resident
  at a time (`ollama stop` the other) under the 16GB ceiling.
