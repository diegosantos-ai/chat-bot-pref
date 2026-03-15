#!/usr/bin/env python3
"""Exibe um resumo local do benchmark baseline inicial da Fase 3."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.llmops import (
    build_benchmark_dataset_summary,
    format_benchmark_dataset_summary,
    load_phase3_initial_baseline,
)


def main() -> int:
    """Carrega o baseline inicial da Fase 3 e imprime seu resumo agregador."""

    dataset = load_phase3_initial_baseline()
    summary = build_benchmark_dataset_summary(dataset)
    print(format_benchmark_dataset_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
