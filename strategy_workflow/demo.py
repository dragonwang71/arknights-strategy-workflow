"""Run the extracted proposal logic on a synthetic input; no battle execution."""

import json
from pathlib import Path

from .timing import retreat_order_proposals, retreat_wait_proposals


def main():
    example = Path(__file__).resolve().parents[1] / "examples" / "timing_case.json"
    case = json.loads(example.read_text(encoding="utf-8"))
    proposals = retreat_wait_proposals(case["plan"], case["result"])
    proposals += retreat_order_proposals(case["plan"], case["result"])
    print(json.dumps({
        "input_kind": case["input_kind"],
        "scope": "Candidate generation only; outcomes have not been evaluated.",
        "candidate_count": len(proposals),
        "candidates": proposals,
    }, indent=2))


if __name__ == "__main__":
    main()
