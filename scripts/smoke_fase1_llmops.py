#!/usr/bin/env python3
"""
Smoke test oficial da Fase 1 — Fundação de LLMOps e Rastreabilidade Experimental.

Objetivo:
- validar o ambiente Python ativo da fase;
- verificar a presença das estruturas mínimas prometidas pela Fase 1;
- executar um smoke test local de MLflow com backend SQLite;
- gerar evidência reproduzível em artifacts/llmops/smoke_fase1/.

Regras:
- não altera comportamento do runtime principal;
- não depende de provider LLM externo;
- falha com código != 0 quando um contrato mínimo não é atendido.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.audit import (  # noqa: E402
    EXPERIMENT_TRACKING_BOUNDARY,
    OPERATIONAL_AUDIT_BOUNDARY,
    PHASE1_AUDIT_INSTRUMENTATION_POINTS,
    PHASE1_TENANT_SEGREGATION,
)
from app.llmops.tracking_integration import build_phase2_tracking_run  # noqa: E402
from app.rag import PHASE1_RAG_ARTIFACT_VERSIONS, PHASE1_RAG_INSTRUMENTATION_POINTS  # noqa: E402
from app.settings import settings  # noqa: E402

ARTIFACTS_DIR = REPO_ROOT / "artifacts" / "llmops" / "smoke_fase1"
MLFLOW_DB_PATH = ARTIFACTS_DIR / "mlflow.db"
MLFLOW_ARTIFACTS_DIR = ARTIFACTS_DIR / "mlartifacts"
MLFLOW_EXPERIMENT_NAME = "chat-pref-fase1-smoke"
REPORT_PATH = ARTIFACTS_DIR / "smoke_report.json"


@dataclass(slots=True)
class CheckResult:
    """Representa o resultado de uma checagem do smoke test."""

    name: str
    status: str
    detail: str


def ensure(condition: bool, message: str) -> None:
    """Interrompe a execução quando uma condição obrigatória falha."""
    if not condition:
        raise RuntimeError(message)


def check_virtualenv() -> CheckResult:
    """
    Valida se o interpretador atual pertence a uma virtualenv.

    Returns:
        CheckResult com o status da validação.
    """
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix) or bool(os.environ.get("VIRTUAL_ENV"))
    ensure(in_venv, "A virtualenv não está ativa. Ative .venv antes de executar o smoke test.")
    return CheckResult(
        name="virtualenv",
        status="PASS",
        detail=f"Interpretador ativo: {sys.executable}",
    )


def check_required_paths() -> list[CheckResult]:
    """
    Verifica a presença de arquivos e diretórios obrigatórios da fase.

    Returns:
        Lista de resultados por estrutura validada.
    """
    required_files = [
        REPO_ROOT / "requirements.txt",
        REPO_ROOT / "requirements-dev.txt",
        REPO_ROOT / "docs-LLMOps" / "README.md",
        REPO_ROOT / "docs-LLMOps" / "CONTEXTO-LLMOps.md",
        REPO_ROOT / "docs-LLMOps" / "ARQUITETURA-LLMOps.md",
    ]

    planning_candidates = [
        REPO_ROOT / "docs-LLMOps" / "PLANEJAMENTO-LLMOPS.md",
        REPO_ROOT / "docs-LLMOps" / "PLANEJAMENTO_LLMOPS.md",
        REPO_ROOT / "docs-LLMOps" / "PLANEJAMENTO-LLMOps.md",
        REPO_ROOT / "docs-LLMOps" / "PLANEJAMENTO_LLMOps.md",
    ]

    required_dirs = [
        REPO_ROOT / "app" / "rag",
        REPO_ROOT / "app" / "audit",
    ]

    results: list[CheckResult] = []

    for file_path in required_files:
        ensure(file_path.exists(), f"Arquivo obrigatório ausente: {file_path.relative_to(REPO_ROOT)}")
        results.append(CheckResult("path", "PASS", f"Arquivo presente: {file_path.relative_to(REPO_ROOT)}"))

    ensure(
        any(path.exists() for path in planning_candidates),
        "Arquivo de planejamento da fase não encontrado em nenhuma variante esperada.",
    )
    results.append(CheckResult("path", "PASS", "Arquivo de planejamento da fase encontrado."))

    for dir_path in required_dirs:
        ensure(dir_path.is_dir(), f"Diretório obrigatório ausente: {dir_path.relative_to(REPO_ROOT)}")
        results.append(CheckResult("path", "PASS", f"Diretório presente: {dir_path.relative_to(REPO_ROOT)}"))

    storage_audit_repo = REPO_ROOT / "app" / "storage" / "audit_repository.py"
    ensure(
        storage_audit_repo.exists(),
        "Repositório ativo de auditoria não encontrado em app/storage/audit_repository.py",
    )
    results.append(
        CheckResult(
            "path",
            "PASS",
            "Persistência operacional atual de auditoria encontrada em app/storage/audit_repository.py",
        )
    )
    ensure(
        OPERATIONAL_AUDIT_BOUNDARY.storage_target == "app/storage/audit_repository.py",
        "Contrato operacional de auditoria divergente do repositório ativo esperado.",
    )
    ensure(
        EXPERIMENT_TRACKING_BOUNDARY.storage_target == "mlflow",
        "Contrato experimental da Fase 1 deve apontar MLflow como stack de tracking.",
    )
    results.append(
        CheckResult(
            "path",
            "PASS",
            f"Fronteira operacional explícita em {OPERATIONAL_AUDIT_BOUNDARY.storage_target}",
        )
    )
    results.append(
        CheckResult(
            "path",
            "PASS",
            f"Fronteira experimental explícita em {EXPERIMENT_TRACKING_BOUNDARY.storage_target}",
        )
    )
    ensure(
        len(PHASE1_AUDIT_INSTRUMENTATION_POINTS) > 0,
        "Pontos mínimos de instrumentação de auditoria não foram definidos.",
    )
    ensure(
        len(PHASE1_RAG_INSTRUMENTATION_POINTS) > 0,
        "Pontos mínimos de instrumentação do RAG não foram definidos.",
    )
    results.append(
        CheckResult(
            "path",
            "PASS",
            f"Mapeamento mínimo de instrumentação disponível em app/audit ({len(PHASE1_AUDIT_INSTRUMENTATION_POINTS)} pontos)",
        )
    )
    results.append(
        CheckResult(
            "path",
            "PASS",
            f"Mapeamento mínimo de instrumentação disponível em app/rag ({len(PHASE1_RAG_INSTRUMENTATION_POINTS)} pontos)",
        )
    )

    return results


def check_imports() -> list[CheckResult]:
    """
    Valida imports mínimos do ambiente base e do ambiente de desenvolvimento.

    Returns:
        Lista de resultados por módulo.
    """
    modules = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "httpx",
        "chromadb",
        "opentelemetry",
        "mlflow",
        "pytest",
        "pandas",
        "numpy",
        "ragas",
    ]

    results: list[CheckResult] = []

    for module_name in modules:
        __import__(module_name)
        results.append(CheckResult("import", "PASS", f"Módulo importado com sucesso: {module_name}"))

    return results


def count_text_occurrences(root: Path, needle: str) -> int:
    """
    Conta ocorrências textuais simples em arquivos .py.

    Args:
        root: Diretório-base da busca.
        needle: Texto procurado.

    Returns:
        Quantidade de ocorrências encontradas.
    """
    total = 0
    for path in root.rglob("*.py"):
        if any(part in {".venv", "venv", "__pycache__", ".git"} for part in path.parts):
            continue
        try:
            total += path.read_text(encoding="utf-8").count(needle)
        except UnicodeDecodeError:
            continue
    return total


def check_runtime_contracts() -> list[CheckResult]:
    """
    Valida sinais mínimos dos contratos estruturais do projeto.

    Returns:
        Lista de resultados dos contratos encontrados.
    """
    app_root = REPO_ROOT / "app"
    tenant_count = count_text_occurrences(app_root, "tenant_id")
    request_count = count_text_occurrences(app_root, "request_id")

    ensure(tenant_count > 0, "Nenhuma ocorrência de tenant_id encontrada em app/.")
    ensure(request_count > 0, "Nenhuma ocorrência de request_id encontrada em app/.")
    ensure(
        PHASE1_RAG_ARTIFACT_VERSIONS.retriever_version == settings.RAG_RETRIEVER_VERSION,
        "retriever_version do contrato RAG divergente da configuração ativa.",
    )
    ensure(
        PHASE1_RAG_ARTIFACT_VERSIONS.embedding_version == settings.RAG_EMBEDDING_VERSION,
        "embedding_version do contrato RAG divergente da configuração ativa.",
    )

    return [
        CheckResult("contract", "PASS", f"tenant_id encontrado em app/ ({tenant_count} ocorrências)"),
        CheckResult("contract", "PASS", f"request_id encontrado em app/ ({request_count} ocorrências)"),
        CheckResult(
            "contract",
            "PASS",
            f"Versionamento inicial do RAG explícito: retriever={PHASE1_RAG_ARTIFACT_VERSIONS.retriever_version} | embedding={PHASE1_RAG_ARTIFACT_VERSIONS.embedding_version}",
        ),
    ]


def run_mlflow_smoke() -> list[CheckResult]:
    """
    Executa um smoke test local de MLflow com tracking em SQLite.

    O teste registra:
    - tags mínimas de segregação;
    - params mínimos de versionamento;
    - métricas técnicas básicas;
    - artifact JSON de evidência.

    Returns:
        Lista de resultados do teste.
    """
    import mlflow
    from mlflow.tracking import MlflowClient

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    MLFLOW_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    tracking_uri = f"sqlite:///{MLFLOW_DB_PATH.resolve().as_posix()}"
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient(tracking_uri=tracking_uri)
    experiment = client.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME)
    if experiment is None:
        experiment_id = client.create_experiment(
            MLFLOW_EXPERIMENT_NAME,
            artifact_location=MLFLOW_ARTIFACTS_DIR.resolve().as_uri(),
        )
    else:
        experiment_id = experiment.experiment_id

    request_id = f"req-smoke-{uuid4().hex[:12]}"
    tracking_run = build_phase2_tracking_run(
        tenant_id="tenant-smoke",
        request_id=request_id,
        dataset_version="smoke.dataset.v1",
        model_provider=settings.LLM_PROVIDER,
        model_name=settings.LLM_MODEL,
        latency_ms=0.0,
        estimated_cost=0.0,
    )
    PHASE1_TENANT_SEGREGATION.validate(tracking_run.run_contract)

    with mlflow.start_run(experiment_id=experiment_id, run_name="fase1_smoke_test") as run:
        start = time.perf_counter()
        mlflow.set_tags(
            {
                "phase": "F1",
                "run_kind": "smoke_test",
                **tracking_run.as_tags(),
            }
        )
        mlflow.log_params(tracking_run.as_params())

        elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
        final_tracking_run = build_phase2_tracking_run(
            tenant_id=tracking_run.run_contract.tenant_id,
            request_id=tracking_run.run_contract.request_id,
            dataset_version=tracking_run.run_contract.dataset_version,
            prompt_version=tracking_run.run_contract.prompt_version,
            policy_version=tracking_run.run_contract.policy_version,
            model_provider=tracking_run.run_contract.model_provider,
            model_name=tracking_run.run_contract.model_name,
            top_k=tracking_run.run_contract.top_k,
            latency_ms=elapsed_ms,
            estimated_cost=tracking_run.run_contract.estimated_cost,
        )

        mlflow.log_metrics({**final_tracking_run.as_metrics(), "smoke_success": 1.0})

        artifact_file = ARTIFACTS_DIR / f"{final_tracking_run.run_contract.request_id}_artifact.json"
        artifact_file.write_text(
            json.dumps(
                {
                    "phase": "F1",
                    "purpose": "smoke_test",
                    "tracking_backend": tracking_uri,
                    "boundary": EXPERIMENT_TRACKING_BOUNDARY.name,
                    "tenant_segregation_rule": PHASE1_TENANT_SEGREGATION.isolation_rule,
                    "instrumentation_points": {
                        "audit": [point.name for point in PHASE1_AUDIT_INSTRUMENTATION_POINTS],
                        "rag": [point.name for point in PHASE1_RAG_INSTRUMENTATION_POINTS],
                    },
                    **final_tracking_run.as_artifact_payload(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        mlflow.log_artifact(str(artifact_file))

        run_id = run.info.run_id

    last_error: Exception | None = None
    fetched_run = None

    for _ in range(5):
        try:
            fetched_run = client.get_run(run_id)
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.5)

    ensure(
        fetched_run is not None,
        f"Run '{run_id}' não foi recuperada via MLflow em '{tracking_uri}'. Erro final: {last_error}",
    )

    ensure(
        fetched_run.info.experiment_id == str(experiment_id),
        "A run recuperada não pertence ao experimento esperado.",
    )
    ensure(
        fetched_run.data.tags.get("phase") == "F1",
        "Tag phase não foi registrada corretamente.",
    )
    ensure(
        fetched_run.data.tags.get("run_kind") == "smoke_test",
        "Tag run_kind não foi registrada corretamente.",
    )

    for key, expected_value in tracking_run.as_tags().items():
        ensure(
            fetched_run.data.tags.get(key) == expected_value,
            f"Tag obrigatória '{key}' não foi registrada corretamente.",
        )

    for key, expected_value in tracking_run.as_params().items():
        ensure(
            fetched_run.data.params.get(key) == expected_value,
            f"Param obrigatório '{key}' não foi registrado corretamente.",
        )

    for key, expected_value in final_tracking_run.as_metrics().items():
        metric_value = fetched_run.data.metrics.get(key)
        ensure(metric_value is not None, f"Métrica obrigatória '{key}' não foi registrada.")
        ensure(
            abs(metric_value - expected_value) < 0.001,
            f"Métrica obrigatória '{key}' divergente: esperado={expected_value} obtido={metric_value}",
        )

    artifact_paths = {item.path for item in client.list_artifacts(run_id)}
    ensure(
        artifact_file.name in artifact_paths,
        f"Artifact mínimo '{artifact_file.name}' não foi registrado via MLflow.",
    )

    return [
        CheckResult("mlflow", "PASS", f"Tracking URI SQLite local validado: {tracking_uri}"),
        CheckResult("mlflow", "PASS", f"Experimento MLflow pronto para smoke local: {experiment_id}"),
        CheckResult("mlflow", "PASS", f"Run criada, recuperada e correlacionada: {run_id}"),
        CheckResult("mlflow", "PASS", f"Artifact mínimo registrado via MLflow: {artifact_file.name}"),
        CheckResult("mlflow", "PASS", f"Segregação experimental validada por {PHASE1_TENANT_SEGREGATION.tenant_field}/{PHASE1_TENANT_SEGREGATION.request_field}"),
        CheckResult(
            "mlflow",
            "PASS",
            "Versões de prompt, policy, retrieval e chunking emitidas no tracking experimental.",
        ),
    ]


def build_report(results: Iterable[CheckResult]) -> dict[str, object]:
    """
    Consolida os resultados em dicionário serializável.

    Args:
        results: Resultados individuais.

    Returns:
        Dicionário do relatório final.
    """
    rows = [asdict(result) for result in results]
    return {
        "phase": "F1",
        "repo_root": str(REPO_ROOT),
        "python_executable": sys.executable,
        "summary": {
            "pass": sum(1 for row in rows if row["status"] == "PASS"),
            "fail": sum(1 for row in rows if row["status"] == "FAIL"),
        },
        "results": rows,
    }


def main() -> int:
    """
    Executa o smoke test completo da Fase 1.

    Returns:
        Código de saída do processo.
    """
    all_results: list[CheckResult] = []

    try:
        all_results.append(check_virtualenv())
        all_results.extend(check_required_paths())
        all_results.extend(check_imports())
        all_results.extend(check_runtime_contracts())
        all_results.extend(run_mlflow_smoke())

        report = build_report(all_results)
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print("[PASS] Smoke test da Fase 1 executado com sucesso.")
        print(f"[INFO] Relatório salvo em: {REPORT_PATH}")
        return 0

    except Exception as exc:  # noqa: BLE001
        all_results.append(CheckResult("smoke", "FAIL", str(exc)))
        report = build_report(all_results)
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"[FAIL] {exc}")
        print(f"[INFO] Relatório salvo em: {REPORT_PATH}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
