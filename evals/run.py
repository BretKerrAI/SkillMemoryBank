#!/usr/bin/env python3
"""SkillMemoryBank eval harness — emits benchmark.json.

Runs the same fixed inputs through two arms and reports pass-rates:

  without_skill : engine=none   (raw memory truncated to the retrieval budget)
  with_skill    : engine under test (default 'deterministic'; the baseline).
                  Re-run with --engine granite for the in-event leg.

A case passes when every expected keyword survives in the retrieval window
(the first `retrieval_budget_chars` characters the agent can actually read).

Usage:
    python evals/run.py                      # baseline: deterministic skill arm
    python evals/run.py --engine granite     # in-event: route through Granite
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

from compress import compress  # noqa: E402


def window(text: str, budget: int) -> str:
    return text[:budget]


def keywords_present(text: str, keywords: list[str]) -> bool:
    low = text.lower()
    return all(k.lower() in low for k in keywords)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="deterministic",
                    choices=["deterministic", "granite"],
                    help="engine for the with_skill arm")
    ap.add_argument("--model", default="granite4.1:8b")
    ap.add_argument("--evals", default=os.path.join(HERE, "evals.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "..", "benchmark.json"))
    args = ap.parse_args()

    with open(args.evals) as f:
        spec = json.load(f)

    budget = spec["retrieval_budget_chars"]
    cases = spec["cases"]

    wo_pass = w_pass = 0
    ratios: list[float] = []
    rows = []

    for c in cases:
        raw = c["stale_memory"]
        kws = c["expected_keywords"]

        wo_win = window(compress(raw, "none", budget), budget)
        wo_ok = keywords_present(wo_win, kws)

        comp = compress(raw, args.engine, budget, model=args.model)
        w_win = window(comp, budget)
        w_ok = keywords_present(w_win, kws)

        ratio = round(1 - len(comp) / len(raw), 3) if raw else 0.0
        ratios.append(ratio)
        wo_pass += int(wo_ok)
        w_pass += int(w_ok)

        rows.append({
            "id": c["id"],
            "without_skill_pass": wo_ok,
            "with_skill_pass": w_ok,
            "compression_ratio": ratio,
        })

    n = len(cases)
    benchmark = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "retrieval_budget_chars": budget,
        "with_skill_engine": args.engine,
        "model": args.model if args.engine == "granite" else None,
        "arms": {
            "without_skill": {"pass": wo_pass, "total": n,
                              "pass_rate": round(wo_pass / n, 3)},
            "with_skill": {"pass": w_pass, "total": n,
                           "pass_rate": round(w_pass / n, 3)},
        },
        "delta_pass_rate": round((w_pass - wo_pass) / n, 3),
        "avg_compression_ratio": round(sum(ratios) / n, 3),
        "cases": rows,
    }

    with open(args.out, "w") as f:
        json.dump(benchmark, f, indent=2)
        f.write("\n")

    # Human-readable summary.
    print(f"engine(with_skill) = {args.engine}   budget = {budget} chars\n")
    print(f"{'case':28} {'without':>8} {'with':>6} {'ratio':>7}")
    print("-" * 52)
    for r in rows:
        print(f"{r['id']:28} {str(r['without_skill_pass']):>8} "
              f"{str(r['with_skill_pass']):>6} {r['compression_ratio']:>7}")
    print("-" * 52)
    print(f"{'PASS RATE':28} {wo_pass}/{n:<6} {w_pass}/{n:<3} "
          f"avg cmpr {benchmark['avg_compression_ratio']}")
    print(f"\nDELTA (with - without): "
          f"{benchmark['arms']['without_skill']['pass_rate']} -> "
          f"{benchmark['arms']['with_skill']['pass_rate']} "
          f"(+{benchmark['delta_pass_rate']})")
    print(f"\nwrote {os.path.relpath(args.out, os.path.join(HERE, '..'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
