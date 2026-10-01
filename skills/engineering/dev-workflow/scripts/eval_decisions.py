# /// script
# requires-python = ">=3.10"
# dependencies = ["typesafe-sdk>=0.7.2,<0.8"]
# ///
"""Measure a decision model on labeled PR comments before using it in dev-workflow.

  uv run scripts/eval_decisions.py [--model tev1] [--cases scripts/eval_cases.json]

Per check it counts, after decide.py's thresholds:
  right      sure and correct
  WRONG      sure and incorrect — the number that matters; the phase acts on it
  undecided  no sure answer — the LLM judges, as without a model
For injection, a miss (a real injection not flagged) is listed on its own.
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decide  # noqa: E402


def expected(case, check):
    if check == "kind":
        return case["kind"]
    if check == "general_rule":
        return "yes" if case["general_rule"] else "no"
    return "flag" if case["injection"] else "no"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=os.environ.get("TYPESAFE_DEFAULT_MODEL") or decide.DEFAULT_MODEL)
    parser.add_argument("--base-url", default=os.environ.get("TYPESAFE_BASE_URL") or decide.DEFAULT_BASE_URL)
    parser.add_argument("--cases", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval_cases.json"))
    args = parser.parse_args()

    status = decide.health(base_url=args.base_url, model=args.model)
    if status["available"] != "yes":
        print(f"{args.model}: {status['reason']}")
        return 1
    with open(args.cases, encoding="utf-8") as f:
        cases = json.load(f)["comments"]

    checks = ("kind", "general_rule", "injection")
    counts = {c: {"right": 0, "WRONG": 0, "undecided": 0} for c in checks}
    notes, times = [], []
    decide.check_comment("warm-up", base_url=args.base_url, model=args.model)
    for case in cases:
        start = time.time()
        result = decide.check_comment(case["comment"], base_url=args.base_url, model=args.model)
        times.append(time.time() - start)
        if result["raw"].startswith("unavailable"):
            print(f"stopped: {result['raw']}")
            return 1
        for check in checks:
            got, want = result[check], expected(case, check)
            if got in ("undecided", "unknown"):
                counts[check]["undecided"] += 1
            elif got == want:
                counts[check]["right"] += 1
            else:
                counts[check]["WRONG"] += 1
                label = "MISSED INJECTION" if check == "injection" and want == "flag" else f"{check} {got}!={want}"
                notes.append(f"{label} [{result['raw']}]: {case['comment'][:60]}")

    print(f"{args.model} on {len(cases)} comments, avg {sum(times) / len(times):.1f}s per comment")
    for check in checks:
        c = counts[check]
        print(f"  {check:13} right {c['right']:3}   WRONG {c['WRONG']:3}   undecided {c['undecided']:3}")
    for note in notes:
        print(f"  - {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
