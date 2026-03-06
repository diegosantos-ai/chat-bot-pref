#!/usr/bin/env python3
"""Generate quick offline RAG evaluation metrics from JSONL traces.

Expected JSONL keys:
- query (str)
- answer (str)
- expected_answer (str, optional)
- contexts (list[str], optional)
- expected_facts (list[str], optional)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _tokenize(text: str) -> set[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return {t for t in cleaned.split() if t}


def _jaccard(a: str, b: str) -> float:
    ta = _tokenize(a)
    tb = _tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _contains_expected_fact(contexts: list[str], facts: list[str]) -> bool:
    if not facts:
        return False
    blob = " ".join(contexts).lower()
    return all(fact.lower() in blob for fact in facts)


def evaluate(records: list[dict[str, Any]]) -> dict[str, float]:
    total = len(records)
    if total == 0:
        return {
            "samples": 0,
            "avg_answer_similarity": 0.0,
            "context_fact_coverage": 0.0,
        }

    similarity_sum = 0.0
    similarity_count = 0
    fact_hits = 0
    fact_checks = 0

    for rec in records:
        answer = str(rec.get("answer", ""))
        expected = rec.get("expected_answer")
        if isinstance(expected, str) and expected.strip():
            similarity_sum += _jaccard(answer, expected)
            similarity_count += 1

        contexts = rec.get("contexts", [])
        facts = rec.get("expected_facts", [])
        if isinstance(contexts, list) and isinstance(facts, list) and facts:
            fact_checks += 1
            if _contains_expected_fact([str(x) for x in contexts], [str(x) for x in facts]):
                fact_hits += 1

    avg_similarity = (similarity_sum / similarity_count) if similarity_count else 0.0
    fact_coverage = (fact_hits / fact_checks) if fact_checks else 0.0

    return {
        "samples": float(total),
        "avg_answer_similarity": avg_similarity,
        "context_fact_coverage": fact_coverage,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Quick RAG offline evaluation report.")
    parser.add_argument("input", type=Path, help="Path to JSONL traces file.")
    args = parser.parse_args()

    records: list[dict[str, Any]] = []
    for line in args.input.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))

    report = evaluate(records)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
