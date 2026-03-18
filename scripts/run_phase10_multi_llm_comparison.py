#!/usr/bin/env python3
"""Executa uma matriz pequena comparativa de Modelos/Providers da Fase 10."""
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
from app.services.llm_service import ( # noqa: E402
    LLMComposeService,
    MockLLMProvider,
    GeminiLLMProvider,
    OpenAILLMProvider,
)
from app.settings import settings


@dataclass(frozen=True)
class Phase10LLMVariant:
    label: str
    rationale: str
    provider_name: str
    model_name: str
    temperature: float = 0.0


def build_default_phase10_matrix() -> tuple[Phase10LLMVariant, ...]:
    """Retorna a matriz pequena e justificável usada no comparativo."""

    # Se existirem chaves reais, poderíamos rodar provedores reais.
    # Para o Bloco 2 garantimos o fallback seguro pro modo mock:
    return (
        Phase10LLMVariant(
            label="mock_padrão_rapido",
            rationale="Baseline transacional - Mock rápido e simulando custo baixo.",
            provider_name="mock",
            model_name="mock-compose-v1-flash",
        ),
        Phase10LLMVariant(
            label="mock_pesado_lento",
            rationale="Simula provedor mais complexo com latência e custo maiores.",
            provider_name="mock",
            model_name="mock-compose-v2-pro",
        ),
    )


def extract_variant_summary(
    variant: Phase10LLMVariant,
    result_data: dict[str, Any],
) -> dict[str, Any]:
    return {
        "variant_label": variant.label,
        "provider": variant.provider_name,
        "model": variant.model_name,
        "rationale": variant.rationale,
        "latency_avg_ms": sum(case.get("latency_ms", 0) for case in result_data.get("executions", [])) / max(len(result_data.get("executions", [])), 1),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compara Modelos de LLM (Fase 10)")
    parser.add_argument(
        "--manifest",
        default=str(REPO_ROOT / PHASE3_INITIAL_BASELINE_MANIFEST),
        help="Caminho para o JSON de manifest do benchmark.",
    )
    parser.add_argument(
        "--tenant-id",
        default="prefeitura-vila-serena",
        help="Tenant para benchmark.",
    )
    parser.add_argument(
        "--experiment-name",
        default="chat-pref-fase10-multi-llm-comparison",
        help="Nome do experimento no MLflow.",
    )
    parser.add_argument(
        "--tracking-dir",
        default="artifacts/llmops/fase10_multi_llm_comparison",
        help="Diretório MLflow.",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=2,
        help="Limite de casos pra não demorar no teste.",
    )
    return parser.parse_args()


async def run() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).resolve()

    tracking_config = MlflowTrackingConfig(
        base_dir=(REPO_ROOT / args.tracking_dir).resolve(),
        experiment_name=args.experiment_name,
    )

    # Roda pelo dataset construindo os llm_services customizados
    results: list[dict[str, Any]] = []

    for variant in build_default_phase10_matrix():
        print(f"\n--- Iniciando Variante: {variant.label} ({variant.model_name}) ---")

        # Constrói o custom LLM provider (o fallback lógico)
        if variant.provider_name == "openai":
            provider_instance = OpenAILLMProvider(model=variant.model_name, temperature=variant.temperature)
        elif variant.provider_name == "gemini":
            provider_instance = GeminiLLMProvider(model=variant.model_name)
        else:
            provider_instance = MockLLMProvider(model=variant.model_name)

        llm_service = LLMComposeService(provider=provider_instance)

        executor = OfflineRagEvaluationExecutor(
            tracking_config=tracking_config,
            experiment_name=args.experiment_name,
            llm_service=llm_service,
        )

        try:
            run_result, logged_run = await executor.execute_and_track(
                manifest_path=manifest_path,
                tenant_id=args.tenant_id,
                case_ids=None,
                max_cases=args.max_cases,
                # Parâmetros de contexto que estariam definidos
                # Forçamos default aqui pra focar no LLM
                strategy_name=None,
            )
        except Exception as e:
            print(f"ERRO: Variante {variant.label} falhou: {e}")
            import traceback
            traceback.print_exc()
            continue

        import mlflow
        mlflow.set_tracking_uri(tracking_config.tracking_uri())
        with mlflow.start_run(run_id=logged_run.run_id):
            mlflow.log_param("phase10_variant_label", variant.label)
            mlflow.log_param("phase10_llm_temperature", variant.temperature)
            mlflow.log_param("phase10_provider_name", variant.provider_name)
            mlflow.log_param("phase10_model_name", variant.model_name)

        raw_cases = []
        for case_exec in run_result.case_executions:
            raw_cases.append({
                "case_id": case_exec.case_input.case_id,
                "model_provider": variant.provider_name,
                "model_name": variant.model_name,
                "latency_ms": case_exec.latency_ms,
                "score_faithfulness": case_exec.case_result.faithfulness,
                "score_relevance": case_exec.case_result.answer_relevance,
            })

        variant_data = {"variant": variant.label, "executions": raw_cases}
        results.append(extract_variant_summary(variant, variant_data))

    print("\n--- SUMÁRIO DE COMPARAÇÃO FASE 10 ---")
    print(json.dumps(results, indent=2, ensure_ascii=False))

    report_path = tracking_config.base_dir / f"phase10_comparison_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nRelatório comparativo salvo em: {report_path.relative_to(REPO_ROOT)}")

    return 0

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(run()))
