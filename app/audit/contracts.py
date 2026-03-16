"""Contratos mínimos da Fase 1 para separar operação e experimentação."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class AuditBoundary:
    """Descreve uma fronteira explícita entre responsabilidade operacional e experimental."""

    name: str
    purpose: str
    storage_target: str


@dataclass(frozen=True, slots=True)
class InstrumentationPoint:
    """Descreve um ponto mínimo de instrumentação para correlação operacional ou experimental."""

    name: str
    source_path: str
    purpose: str
    required_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExperimentalTenantSegregation:
    """Formaliza a regra mínima de segregação experimental por tenant na Fase 1."""

    tenant_field: str
    request_field: str
    isolation_rule: str
    required_run_fields: tuple[str, ...]

    def validate(self, run_contract: "ExperimentalRunContract") -> None:
        """Valida se uma run atende ao contrato mínimo de segregação por tenant."""

        values = {
            self.tenant_field: getattr(run_contract, self.tenant_field, ""),
            self.request_field: getattr(run_contract, self.request_field, ""),
        }
        for field_name, value in values.items():
            if not str(value).strip():
                raise ValueError(f"Campo obrigatório de segregação ausente: {field_name}")


@dataclass(frozen=True, slots=True)
class ExperimentalRunContract:
    """Representa o contrato mínimo de uma run experimental da Fase 1."""

    tenant_id: str
    request_id: str
    prompt_version: str
    policy_version: str
    retriever_version: str
    retrieval_strategy_name: str
    query_transform_strategy_name: str
    rerank_strategy_name: str
    embedding_version: str
    dataset_version: str
    model_provider: str
    model_name: str
    top_k: int
    latency_ms: float
    estimated_cost: float

    def __post_init__(self) -> None:
        """Impõe o contrato mínimo da run experimental logo na criação do objeto."""

        required_strings = {
            "tenant_id": self.tenant_id,
            "request_id": self.request_id,
            "prompt_version": self.prompt_version,
            "policy_version": self.policy_version,
            "retriever_version": self.retriever_version,
            "retrieval_strategy_name": self.retrieval_strategy_name,
            "query_transform_strategy_name": self.query_transform_strategy_name,
            "rerank_strategy_name": self.rerank_strategy_name,
            "embedding_version": self.embedding_version,
            "dataset_version": self.dataset_version,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
        }
        for field_name, value in required_strings.items():
            if not str(value).strip():
                raise ValueError(f"Campo obrigatório da run experimental ausente: {field_name}")
        if self.top_k < 1:
            raise ValueError("top_k deve ser maior ou igual a 1.")
        if self.latency_ms < 0:
            raise ValueError("latency_ms não pode ser negativo.")
        if self.estimated_cost < 0:
            raise ValueError("estimated_cost não pode ser negativo.")

    def as_tags(self) -> dict[str, str]:
        """Retorna as tags mínimas de correlação operacional para a run."""

        return {
            "tenant_id": self.tenant_id,
            "request_id": self.request_id,
        }

    def as_params(self) -> dict[str, str]:
        """Retorna os parâmetros versionados e comparáveis da execução."""

        return {
            "prompt_version": self.prompt_version,
            "policy_version": self.policy_version,
            "retriever_version": self.retriever_version,
            "retrieval_strategy_name": self.retrieval_strategy_name,
            "query_transform_strategy_name": self.query_transform_strategy_name,
            "rerank_strategy_name": self.rerank_strategy_name,
            "embedding_version": self.embedding_version,
            "dataset_version": self.dataset_version,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "top_k": str(self.top_k),
        }

    def as_metrics(self) -> dict[str, float]:
        """Retorna as métricas técnicas mínimas exigidas pela fase."""

        return {
            "latency_ms": self.latency_ms,
            "estimated_cost": self.estimated_cost,
        }

    def as_artifact_payload(self) -> dict[str, object]:
        """Retorna o payload serializável do artifact mínimo da run."""

        return {
            "tenant_id": self.tenant_id,
            "request_id": self.request_id,
            "prompt_version": self.prompt_version,
            "policy_version": self.policy_version,
            "retriever_version": self.retriever_version,
            "retrieval_strategy_name": self.retrieval_strategy_name,
            "query_transform_strategy_name": self.query_transform_strategy_name,
            "rerank_strategy_name": self.rerank_strategy_name,
            "embedding_version": self.embedding_version,
            "dataset_version": self.dataset_version,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "top_k": self.top_k,
            "latency_ms": self.latency_ms,
            "estimated_cost": self.estimated_cost,
        }


OPERATIONAL_AUDIT_BOUNDARY: Final[AuditBoundary] = AuditBoundary(
    name="operational_audit",
    purpose="Registrar fatos operacionais do atendimento sem misturar tracking experimental.",
    storage_target="app/storage/audit_repository.py",
)

EXPERIMENT_TRACKING_BOUNDARY: Final[AuditBoundary] = AuditBoundary(
    name="experimental_tracking",
    purpose="Registrar runs, params, metrics e artifacts comparáveis por tenant na Fase 1.",
    storage_target="mlflow",
)

PHASE1_TENANT_SEGREGATION: Final[ExperimentalTenantSegregation] = ExperimentalTenantSegregation(
    tenant_field="tenant_id",
    request_field="request_id",
    isolation_rule="Toda run experimental da Fase 1 deve ser filtrável por tenant_id e correlacionável por request_id.",
    required_run_fields=("tenant_id", "request_id"),
)

PHASE1_AUDIT_INSTRUMENTATION_POINTS: Final[tuple[InstrumentationPoint, ...]] = (
    InstrumentationPoint(
        name="audit_event_emission",
        source_path="app/services/chat_service.py:_append_event",
        purpose="Emitir fatos operacionais correlacionáveis antes da persistência em auditoria.",
        required_fields=("tenant_id", "request_id", "session_id", "channel", "event_type"),
    ),
    InstrumentationPoint(
        name="audit_event_persistence",
        source_path="app/storage/audit_repository.py:append_event",
        purpose="Persistir a trilha operacional por tenant sem misturar tracking experimental.",
        required_fields=("tenant_id", "request_id", "session_id", "channel", "event_type"),
    ),
)
