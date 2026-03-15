#!/usr/bin/env python3
"""Executa a avaliacao offline da Fase 4 e registra a run no MLflow local."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.llmops.benchmark_dataset import PHASE3_INITIAL_BASELINE_MANIFEST  # noqa: E402
from app.llmops.rag_evaluation_runner import (  # noqa: E402
    MlflowTrackingConfig,
    OfflineRagEvaluationExecutor,
)


def parse_args() -> argparse.Namespace:
    """Le os argumentos minimos da execucao offline da Fase 4."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default=str(PHASE3_INITIAL_BASELINE_MANIFEST),
        help="Manifest JSON do benchmark a ser avaliado.",
    )
    parser.add_argument(
        "--tenant-id",
        default="",
        help="Tenant explicito da run. Se vazio, usa o tenant do manifest.",
    )
    parser.add_argument(
        "--experiment-name",
        default="chat-pref-fase4-rag-evaluation",
        help="Nome do experimento no MLflow local.",
    )
    parser.add_argument(
        "--tracking-dir",
        default="artifacts/llmops/fase4_rag_evaluation",
        help="Diretorio local do backend SQLite e dos artifacts do MLflow.",
    )
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Case id especifico do benchmark. Pode ser repetido.",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=None,
        help="Limita a quantidade de casos executados a partir do recorte selecionado.",
    )
    return parser.parse_args()


async def run() -> int:
    """Executa a run offline e imprime um resumo curto em JSON."""

    args = parse_args()
    tracking_config = MlflowTrackingConfig(
        base_dir=(REPO_ROOT / args.tracking_dir).resolve(),
        experiment_name=args.experiment_name,
    )
    executor = OfflineRagEvaluationExecutor(
        tracking_config=tracking_config,
        experiment_name=args.experiment_name,
    )
    execution, logged_run = await executor.execute_and_track(
        manifest_path=Path(args.manifest).resolve(),
        tenant_id=args.tenant_id or None,
        case_ids=args.case_id or None,
        max_cases=args.max_cases,
    )

    print(
        json.dumps(
            {
                "tenant_id": execution.tenant_id,
                "dataset_version": execution.dataset.manifest.dataset_version,
                "run_id": logged_run.run_id,
                "tracking_uri": logged_run.tracking_uri,
                "cases_total": len(execution.case_executions),
                "cases_evaluated": execution.evaluated_cases_count(),
                "cases_partial": execution.partial_cases_count(),
                "cases_skipped": execution.skipped_cases_count(),
                "faithfulness_mean": execution.summary.faithfulness_mean,
                "answer_relevance_mean": execution.summary.answer_relevance_mean,
                "expected_context_coverage_mean": execution.summary.expected_context_coverage_mean,
                "retrieval_empty_rate": execution.summary.retrieval_empty_rate,
                "report_path": str(logged_run.report_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    import asyncio

    raise SystemExit(asyncio.run(run()))
