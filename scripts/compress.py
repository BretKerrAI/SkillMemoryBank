#!/usr/bin/env python3
"""SkillMemoryBank compression pipeline — engine dispatch.

Three engines, one interface:

  none           identity. The "without-skill" arm: raw memory, no compression.
  deterministic  the committed BASELINE. Pure-function heuristic, no model. It
                 extracts durable lines (procedures / constraints / decisions)
                 and drops chit-chat. Reproducible, zero cost, sub-millisecond.
  granite        the IN-EVENT LEG. Routes the same text through granite4.1:8b
                 (see granite_call.py). Present at baseline, NOT the default.

The before/after that scores Lane 2 is: baseline benchmark uses `deterministic`;
the in-event improvement re-runs the eval with `--engine granite`.

CLI:
    python scripts/compress.py --engine deterministic < stale_memory.txt
"""
from __future__ import annotations

import argparse
import sys

# Cue lexicons for the deterministic heuristic. Order of classification is
# DECISIONS -> PROCEDURES -> CONSTRAINTS so a "we'll use X instead of Y because"
# line lands under DECISIONS even though it also contains a procedure verb.
DECISION_CUES = ("decid", "chose", "choose", "will use", "we'll use",
                 "go with", "instead of", "rather than", "because")
PROCEDURE_CUES = (" deploy", "deploy,", "deploy:", " run ", "configure",
                  "install", "first ", "then ", "step ", " set ", "migrat")
CONSTRAINT_CUES = ("must", "never", "always", "do not", "don't", " limit",
                   "cap ", " max ", " only ", "required", "rate limit",
                   "deadline", " ban")

LABELS = ("decision:", "constraint:", "procedure:",
          "decisions:", "constraints:", "procedures:")

HEADERS = ("PROCEDURES", "CONSTRAINTS", "DECISIONS")


def _classify(line: str) -> str | None:
    low = line.lower()
    if any(c in low for c in DECISION_CUES):
        return "DECISIONS"
    if any(c in low for c in PROCEDURE_CUES):
        return "PROCEDURES"
    if any(c in low for c in CONSTRAINT_CUES):
        return "CONSTRAINTS"
    return None


def _strip_label(line: str) -> str:
    low = line.lower()
    for lab in LABELS:
        if low.startswith(lab):
            return line[len(lab):].strip()
    return line


def deterministic_compress(text: str, budget: int = 240) -> str:
    """Extract durable lines under the SMB template; drop everything else."""
    buckets: dict[str, list[str]] = {h: [] for h in HEADERS}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        cat = _classify(line)
        if cat is None:
            continue  # chit-chat / one-off context -> dropped
        buckets[cat].append(_strip_label(line))

    parts: list[str] = []
    for header in HEADERS:
        items = buckets[header]
        if not items:
            continue
        parts.append(header + ":")
        parts.extend("- " + it for it in items)

    out = "\n".join(parts)
    if len(out) > budget:  # keep highest-priority lines within budget
        lines = out.splitlines()
        while lines and len("\n".join(lines)) > budget:
            lines.pop()
        out = "\n".join(lines)
    return out


def compress(text: str, engine: str = "deterministic", budget: int = 240,
             model: str = "granite4.1:8b") -> str:
    if engine == "none":
        return text
    if engine == "deterministic":
        return deterministic_compress(text, budget)
    if engine == "granite":
        from granite_call import compress_memory  # lazy: only needs Ollama here
        return compress_memory(text, model=model)
    raise ValueError(f"unknown engine: {engine!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description="SkillMemoryBank compression")
    ap.add_argument("--engine", default="deterministic",
                    choices=["none", "deterministic", "granite"])
    ap.add_argument("--budget", type=int, default=240)
    ap.add_argument("--model", default="granite4.1:8b")
    args = ap.parse_args()
    text = sys.stdin.read()
    print(compress(text, engine=args.engine, budget=args.budget, model=args.model))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
