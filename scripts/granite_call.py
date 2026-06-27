#!/usr/bin/env python3
"""Minimal Granite-via-Ollama wrapper for the SkillMemoryBank compression leg.

No API key, no egress — calls the local Ollama server at localhost:11434.
Deterministic by default (temperature 0) so the with/without eval delta stays
reproducible.

This module is the *runtime worker* for the compression stage. It is present in
the baseline but is NOT the default compression engine — wiring it into the
pipeline (see ../scripts/compress.py and ../evals/run.py --engine granite) is the
in-event improvement that produces the Lane 2 before/after delta.

Usage (library):
    from granite_call import granite, compress_memory
    summary = compress_memory(stale_text)                 # granite4.1:8b
    summary = compress_memory(stale_text, model="granite4.1:3b")  # RAM fallback

Usage (CLI):
    python scripts/granite_call.py            # smoke test -> prints "ready"
    python scripts/granite_call.py compress < stale_memory.txt
"""
import json
import sys
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "granite4.1:8b"  # swap to granite4.1:3b under 16GB memory pressure

# PROMPT 1 — stale-memory compression. Granite 4.1 is a non-thinking,
# instruction-following, structured-output model: one task, strict template,
# an example, temperature 0. Do not ask it to "think" — ask it to emit a shape.
SYSTEM_COMPRESS = (
    "You compress stale agent memory into a durable summary. You preserve only "
    "reusable procedures, constraints, and decisions. You drop greetings, "
    "chit-chat, one-off context, and anything not reusable. You never invent "
    "facts. You output ONLY the summary in the exact template. No preamble. "
    "Hard cap: 120 tokens."
)

USER_COMPRESS_TEMPLATE = """TEMPLATE (fill, keep headers, omit a section if empty):
PROCEDURES:
- <imperative step>
CONSTRAINTS:
- <rule that must always hold>
DECISIONS:
- <choice made and the reason>

MEMORY TO COMPRESS:
<<<
{stale_memory_text}
>>>"""


def granite(system: str, user: str, model: str = DEFAULT_MODEL,
            temperature: float = 0.0, timeout: int = 360) -> str:
    # timeout is generous on purpose: the first call cold-loads ~5GB into RAM,
    # which can take minutes near the 16GB ceiling. Warm calls are sub-second.
    """One chat round-trip to local Ollama. Returns the assistant content."""
    payload = {
        "model": model,
        "stream": False,
        "options": {"temperature": temperature},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["message"]["content"].strip()


def granite_json(system: str, user: str, **kw) -> dict:
    """Same call, but parse strict-JSON output. Raises on non-JSON."""
    raw = granite(system, user, **kw)
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)


def compress_memory(stale_memory_text: str, model: str = DEFAULT_MODEL) -> str:
    """Compress one block of stale memory via Granite into the durable template."""
    user = USER_COMPRESS_TEMPLATE.format(stale_memory_text=stale_memory_text)
    return granite(SYSTEM_COMPRESS, user, model=model)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compress":
        text = sys.stdin.read()
        print(compress_memory(text))
    else:
        # Smoke test: confirm the local server + model are live before the build.
        print(granite("Reply with one word.", "Say: ready"))
