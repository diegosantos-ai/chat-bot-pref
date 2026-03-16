#!/usr/bin/env python3
"""Executa uma matriz pequena de comparacao da Fase 5 e consolida um sumario JSON."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.llmops.benchmark_dataset import PHASE3_INITIAL_BASELINE_MANIFEST  # noqa: E402
from app.llmops.rag_evaluation_runner import (  # noqa: E402
    MlflowTrackingConfig,
    OfflineRagEvaluationExecutor,
)
from app.rag.query_transformation import (  # noqa: E402
    NO_QUERY_TRANSFORM_STRATEGY_NAME,
    TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME,
)
from app.rag.reranking import (  # noqa: E402
    HEURISTIC_POST_RETRIEVAL_RERANK_STRATEGY_NAME,
    NO_RERANK_STRATEGY_NAME,
)
from app.rag.retrieval_scoring import (  # noqa: E402
    BASELINE_RETRIEVAL_STRATEGY_NAME,
    HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
)


@dataclass(frozen=True, slots=True)
class Phase5StrategyVariant:
    """Representa uma combinacao comparativa pequena da Fase 5."""

    label: str
    rationale: str
    retrieval_strategy_name: str
    query_transform_strategy_name: str
    rerank_strategy_name: str


def build_default_phase5_matrix() -> tuple[Phase5StrategyVariant, ...]:
    """Retorna a matriz pequena e justificavel usada no comparativo da Fase 5."""

    return (
        Phase5StrategyVariant(
            label="baseline_semantic_only",
            rationale="Controla a referencia herdada sem retrieval lexical complementar, query expansion ou reranking.",
            retrieval_strategy_name=BASELINE_RETRIEVAL_STRATEGY_NAME,
            query_transform_strategy_name=NO_QUERY_TRANSFORM_STRATEGY_NAME,
            rerank_strategy_name=NO_RERANK_STRATEGY_NAME,
        ),
        Phase5StrategyVariant(
            label="hybrid_lexical_only",
            rationale="Isola o impacto da camada lexical complementar real sem alterar query nem ranking final.",
            retrieval_strategy_name=HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
            query_transform_strategy_name=NO_QUERY_TRANSFORM_STRATEGY_NAME,
            rerank_strategy_name=NO_RERANK_STRATEGY_NAME,
        ),
        Phase5StrategyVariant(
            label="hybrid_plus_query_transform",
            rationale="Mede o ganho ou ruido adicional da query expansion sobre a variante hibrida.",
            retrieval_strategy_name=HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
            query_transform_strategy_name=TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME,
            rerank_strategy_name=NO_RERANK_STRATEGY_NAME,
        ),
        Phase5StrategyVariant(
            label="hybrid_plus_rerank",
            rationale="Mede o efeito do reranking heuristico mantendo a query original.",
            retrieval_strategy_name=HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
            query_transform_strategy_name=NO_QUERY_TRANSFORM_STRATEGY_NAME,
            rerank_strategy_name=HEURISTIC_POST_RETRIEVAL_RERANK_STRATEGY_NAME,
        ),
        Phase5StrategyVariant(
            label="hybrid_plus_query_transform_plus_rerank",
            rationale="Mede a composicao completa atualmente suportada na Fase 5, sem promover default.",
            retrieval_strategy_name=HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
            query_transform_strategy_name=TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME,
            rerank_strategy_name=HEURISTIC_POST_RETRIEVAL_RERANK_STRATEGY_NAME,
        ),
    )


def _safe_delta(value: float | None, baseline: float | None) -> float | None:
    """Calcula delta simples contra a baseline quando ambos os valores existem."""

    if value is None or baseline is None:
        return None
    return round(value - baseline, 6)


def build_phase5_comparison_summary(
    *,
    experiment_name: str,
    manifest_path: Path,
    selected_case_ids: list[str],
    max_cases: int | None,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Consolida os resultados lado a lado sem inferir promocao automatica."""

    baseline = results[0]
    baseline_metrics = baseline["metrics"]
    return {
        "phase": "F5",
        "artifact_type": "phase5_strategy_comparison",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_name": experiment_name,
        "manifest_path": str(manifest_path),
        "selected_case_ids": selected_case_ids,
        "max_cases": max_cases,
        "variants_compared": len(results),
        "methodology_notes": [
            "A matriz compara apenas combinacoes ja implementadas e rastreaveis da Fase 5.",
            "Nao houve mudanca de algoritmo durante a comparacao; apenas execucao do benchmark offline existente.",
            "Latencia observada e total por run; nao representa perfil detalhado por estagio.",
            "Ausencia de melhora clara tambem e resultado valido para fechamento do bloco.",
        ],
        "baseline_reference": {
            "label": baseline["label"],
            "retrieval_strategy_name": baseline["retrieval_strategy_name"],
            "query_transform_strategy_name": baseline["query_transform_strategy_name"],
            "rerank_strategy_name": baseline["rerank_strategy_name"],
            "run_id": baseline["run_id"],
        },
        "results": [
            {
                **result,
                "deltas_vs_baseline": {
                    "faithfulness_mean": _safe_delta(
                        result["metrics"]["faithfulness_mean"],
                        baseline_metrics["faithfulness_mean"],
                    ),
                    "answer_relevance_mean": _safe_delta(
                        result["metrics"]["answer_relevance_mean"],
                        baseline_metrics["answer_relevance_mean"],
                    ),
                    "expected_context_coverage_mean": _safe_delta(
                        result["metrics"]["expected_context_coverage_mean"],
                        baseline_metrics["expected_context_coverage_mean"],
                    ),
                    "retrieval_empty_rate": _safe_delta(
                        result["metrics"]["retrieval_empty_rate"],
                        baseline_metrics["retrieval_empty_rate"],
                    ),
                    "total_latency_ms": _safe_delta(
                        result["metrics"]["total_latency_ms"],
                        baseline_metrics["total_latency_ms"],
                    ),
                },
            }
            for result in results
        ],
    }


def parse_args() -> argparse.Namespace:
    """Le os argumentos minimos da comparacao da Fase 5."""

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
        default="chat-pref-fase5-retrieval-comparison",
        help="Nome do experimento no MLflow local.",
    )
    parser.add_argument(
        "--tracking-dir",
        default="artifacts/llmops/fase5_retrieval_comparison",
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
    parser.add_argument(
        "--output",
        default="",
        help="Caminho opcional do JSON consolidado. Se vazio, grava no diretorio de reports.",
    )
    return parser.parse_args()


async def run() -> int:
    """Executa a matriz da Fase 5 e imprime um sumario JSON consolidado."""

    args = parse_args()
    manifest_path = Path(args.manifest).resolve()
    tracking_config = MlflowTrackingConfig(
        base_dir=(REPO_ROOT / args.tracking_dir).resolve(),
        experiment_name=args.experiment_name,
    )
    executor = OfflineRagEvaluationExecutor(
        tracking_config=tracking_config,
        experiment_name=args.experiment_name,
    )

    results: list[dict[str, Any]] = []
    for variant in build_default_phase5_matrix():
        execution, logged_run = await executor.execute_and_track(
            manifest_path=manifest_path,
            tenant_id=args.tenant_id or None,
            case_ids=args.case_id or None,
            max_cases=args.max_cases,
            strategy_name=variant.retrieval_strategy_name,
            query_transform_strategy_name=variant.query_transform_strategy_name,
            rerank_strategy_name=variant.rerank_strategy_name,
        )
        results.append(
            {
                "label": variant.label,
                "rationale": variant.rationale,
                "run_id": logged_run.run_id,
                "tenant_id": execution.tenant_id,
                "dataset_version": execution.dataset.manifest.dataset_version,
                "retrieval_strategy_name": execution.tracking_run.run_contract.retrieval_strategy_name,
                "query_transform_strategy_name": execution.tracking_run.run_contract.query_transform_strategy_name,
                "rerank_strategy_name": execution.tracking_run.run_contract.rerank_strategy_name,
                "phase5_experiment_axes": execution.tracking_run.tracking_metadata.phase5_experiment_axes,
                "metrics": {
                    "cases_total": execution.summary.total_cases,
                    "cases_evaluated": execution.evaluated_cases_count(),
                    "cases_partial": execution.partial_cases_count(),
                    "cases_skipped": execution.skipped_cases_count(),
                    "faithfulness_mean": execution.summary.faithfulness_mean,
                    "answer_relevance_mean": execution.summary.answer_relevance_mean,
                    "expected_context_coverage_mean": execution.summary.expected_context_coverage_mean,
                    "retrieval_empty_rate": execution.summary.retrieval_empty_rate,
                    "total_latency_ms": execution.total_latency_ms,
                    "estimated_cost": execution.tracking_run.run_contract.estimated_cost,
                },
                "report_path": str(logged_run.report_path),
                "comparison_snapshot_path": str(logged_run.comparison_snapshot_path),
            }
        )

    summary = build_phase5_comparison_summary(
        experiment_name=args.experiment_name,
        manifest_path=manifest_path,
        selected_case_ids=args.case_id,
        max_cases=args.max_cases,
        results=results,
    )

    output_path = (
        Path(args.output).resolve()
        if args.output
        else tracking_config.reports_dir / "phase5_strategy_comparison_summary.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({**summary, "output_path": str(output_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    import asyncio

    raise SystemExit(asyncio.run(run()))
