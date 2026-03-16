"""Integração mínima entre artefatos versionados da Fase 2 e tracking experimental."""

from __future__ import annotations

from dataclasses import dataclass
import json

from app.audit import ExperimentalRunContract, PHASE1_TENANT_SEGREGATION
from app.llmops.active_artifacts import ActiveArtifactResolver, ActiveTextArtifact
from app.settings import settings
from app.storage.chroma_repository import TenantChromaRepository


@dataclass(frozen=True, slots=True)
class Phase2TrackingMetadata:
    """Representa os metadados adicionais da Fase 2 anexados ao tracking experimental."""

    prompt_version_id: str
    policy_version_id: str
    retriever_version_id: str
    chunking_version: str
    chunking_version_id: str
    phase5_experiment_axes: dict[str, object]

    def as_tags(self) -> dict[str, str]:
        """Retorna as tags comparativas da Fase 2 para filtragem no tracking."""

        return {
            "prompt_version_id": self.prompt_version_id,
            "policy_version_id": self.policy_version_id,
            "retriever_version_id": self.retriever_version_id,
            "chunking_version_id": self.chunking_version_id,
        }

    def as_params(self) -> dict[str, str]:
        """Retorna os parâmetros adicionais da Fase 2 para comparação entre runs."""

        return {
            "chunking_version": self.chunking_version,
            "phase5_experiment_axes_json": json.dumps(
                self.phase5_experiment_axes,
                ensure_ascii=False,
                sort_keys=True,
            ),
        }

    def as_artifact_payload(self) -> dict[str, str]:
        """Retorna o payload serializável adicional da Fase 2."""

        return {
            "prompt_version_id": self.prompt_version_id,
            "policy_version_id": self.policy_version_id,
            "retriever_version_id": self.retriever_version_id,
            "chunking_version": self.chunking_version,
            "chunking_version_id": self.chunking_version_id,
            "phase5_experiment_axes": self.phase5_experiment_axes,
        }


@dataclass(frozen=True, slots=True)
class Phase2TrackingRun:
    """Agrupa o contrato base da Fase 1 com os metadados extras da Fase 2."""

    run_contract: ExperimentalRunContract
    tracking_metadata: Phase2TrackingMetadata

    def as_tags(self) -> dict[str, str]:
        """Retorna todas as tags emitidas no tracking experimental."""

        return {
            **self.run_contract.as_tags(),
            **self.tracking_metadata.as_tags(),
        }

    def as_params(self) -> dict[str, str]:
        """Retorna todos os parâmetros comparativos emitidos no tracking."""

        return {
            **self.run_contract.as_params(),
            **self.tracking_metadata.as_params(),
        }

    def as_metrics(self) -> dict[str, float]:
        """Retorna as métricas técnicas mínimas da execução."""

        return self.run_contract.as_metrics()

    def as_artifact_payload(self) -> dict[str, object]:
        """Retorna o payload mínimo do artifact experimental enriquecido pela Fase 2."""

        return {
            **self.run_contract.as_artifact_payload(),
            **self.tracking_metadata.as_artifact_payload(),
        }


def build_phase2_tracking_run(
    *,
    tenant_id: str,
    request_id: str,
    dataset_version: str,
    prompt_version: str | None = None,
    policy_version: str | None = None,
    retrieval_strategy_name: str | None = None,
    query_transform_strategy_name: str | None = None,
    rerank_strategy_name: str | None = None,
    model_provider: str | None = None,
    model_name: str | None = None,
    top_k: int | None = None,
    latency_ms: float = 0.0,
    estimated_cost: float = 0.0,
    artifact_resolver: ActiveArtifactResolver | None = None,
    chroma_repository: TenantChromaRepository | None = None,
) -> Phase2TrackingRun:
    """Monta a run experimental mínima com as versões ativas dos artefatos de IA."""

    resolver = artifact_resolver or ActiveArtifactResolver()
    prompt_artifact = _resolve_prompt_artifact(prompt_version, resolver)
    policy_artifact = _resolve_policy_artifact(policy_version, resolver)
    retrieval_artifact = resolver.resolve_retrieval_config()
    chunking_artifact = resolver.resolve_chunking_config()
    repository = chroma_repository or TenantChromaRepository(artifact_resolver=resolver)
    experimental_config = resolver.resolve_phase5_experimental_config(
        retrieval_strategy_name=retrieval_strategy_name,
        query_transform_strategy_name=query_transform_strategy_name,
        rerank_strategy_name=rerank_strategy_name,
    )

    run_contract = ExperimentalRunContract(
        tenant_id=tenant_id,
        request_id=request_id,
        prompt_version=prompt_artifact.version,
        policy_version=policy_artifact.version,
        retriever_version=repository.retriever_version(),
        retrieval_strategy_name=experimental_config.retrieval.strategy_name,
        query_transform_strategy_name=experimental_config.query_transformation.strategy_name,
        rerank_strategy_name=experimental_config.reranking.strategy_name,
        embedding_version=repository.embedding_version(),
        dataset_version=dataset_version,
        model_provider=(model_provider or settings.LLM_PROVIDER).strip(),
        model_name=(model_name or settings.LLM_MODEL).strip(),
        top_k=top_k if top_k is not None else resolver.retrieval_top_k_default(),
        latency_ms=latency_ms,
        estimated_cost=estimated_cost,
    )
    PHASE1_TENANT_SEGREGATION.validate(run_contract)

    tracking_metadata = Phase2TrackingMetadata(
        prompt_version_id=prompt_artifact.version_id,
        policy_version_id=policy_artifact.version_id,
        retriever_version_id=retrieval_artifact.version_id,
        chunking_version=chunking_artifact.version,
        chunking_version_id=chunking_artifact.version_id,
        phase5_experiment_axes=experimental_config.as_payload(),
    )
    return Phase2TrackingRun(
        run_contract=run_contract,
        tracking_metadata=tracking_metadata,
    )


def _resolve_prompt_artifact(
    prompt_version: str | None,
    resolver: ActiveArtifactResolver,
) -> ActiveTextArtifact:
    """Resolve o prompt versionado efetivamente usado na execução experimental."""

    composer_prompt = resolver.resolve_composer_prompt()
    fallback_prompt = resolver.resolve_fallback_prompt()
    desired_version = (prompt_version or composer_prompt.version).strip()

    for artifact in (composer_prompt, fallback_prompt):
        if artifact.version == desired_version:
            return artifact

    raise ValueError(f"Prompt versionado não suportado para tracking experimental: {desired_version}")


def _resolve_policy_artifact(
    policy_version: str | None,
    resolver: ActiveArtifactResolver,
) -> ActiveTextArtifact:
    """Resolve a policy textual usada como referência da execução experimental."""

    policy_artifact = resolver.resolve_policy_text()
    desired_version = (policy_version or policy_artifact.version).strip()
    if policy_artifact.version != desired_version:
        raise ValueError(f"Policy versionada não suportada para tracking experimental: {desired_version}")
    return policy_artifact
