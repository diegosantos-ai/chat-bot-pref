"""Resolvedor dos artefatos ativos da Fase 2 usados pelo runtime atual."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from app.llmops.artifact_catalog import AI_ARTIFACTS_DIR, PHASE2_ARTIFACT_CATALOG, Phase2ArtifactCatalog
from app.llmops.artifact_catalog import VersionedArtifactDescriptor
from app.rag.retrieval_scoring import RetrievalScoreWeights
from app.rag.query_transformation import (
    NO_QUERY_TRANSFORM_STRATEGY_NAME,
    QueryTransformationConfig,
    SUPPORTED_QUERY_TRANSFORM_SOURCE_FIELDS,
)
from app.rag.reranking import (
    NO_RERANK_STRATEGY_NAME,
    RerankScoreWeights,
    RerankingConfig,
)
from app.llmops.versioning import ArtifactVersionMetadata, build_content_hash, load_artifact_metadata
from app.settings import settings


@dataclass(frozen=True, slots=True)
class ActiveTextArtifact:
    """Representa um artefato textual ativo resolvido para o runtime."""

    descriptor: VersionedArtifactDescriptor
    metadata: ArtifactVersionMetadata
    path: Path
    content: str

    @property
    def version(self) -> str:
        """Retorna o rótulo de versão ativa do artefato."""

        return self.metadata.version_label

    @property
    def version_id(self) -> str:
        """Retorna o identificador comparável da versão ativa."""

        return self.metadata.version_id


@dataclass(frozen=True, slots=True)
class ActiveJsonArtifact:
    """Representa um artefato JSON ativo resolvido para o runtime."""

    descriptor: VersionedArtifactDescriptor
    metadata: ArtifactVersionMetadata
    path: Path
    payload: dict[str, Any]

    @property
    def version(self) -> str:
        """Retorna o rótulo de versão ativa do artefato."""

        return self.metadata.version_label

    @property
    def version_id(self) -> str:
        """Retorna o identificador comparável da versão ativa."""

        return self.metadata.version_id


class ActiveArtifactResolver:
    """Resolve e valida a versão ativa dos artefatos versionáveis da Fase 2."""

    def __init__(
        self,
        *,
        catalog: Phase2ArtifactCatalog | None = None,
        artifacts_dir: Path | None = None,
    ) -> None:
        self.catalog = catalog or PHASE2_ARTIFACT_CATALOG
        self.artifacts_dir = artifacts_dir or AI_ARTIFACTS_DIR

    def resolve_composer_prompt(self) -> ActiveTextArtifact:
        """Resolve o prompt principal ativo."""

        return self._resolve_text_artifact(self.catalog.composer_prompt)

    def resolve_fallback_prompt(self) -> ActiveTextArtifact:
        """Resolve o prompt de fallback ativo."""

        return self._resolve_text_artifact(self.catalog.fallback_prompt)

    def resolve_policy_text(self) -> ActiveTextArtifact:
        """Resolve a policy textual ativa."""

        return self._resolve_text_artifact(self.catalog.policy_text)

    def resolve_retrieval_config(self) -> ActiveJsonArtifact:
        """Resolve a configuração ativa de retrieval."""

        return self._resolve_json_artifact(self.catalog.retrieval_config)

    def resolve_chunking_config(self) -> ActiveJsonArtifact:
        """Resolve a configuração ativa de chunking."""

        return self._resolve_json_artifact(self.catalog.chunking_config)

    def retrieval_top_k_default(self) -> int:
        """Retorna o `top_k` ativo do runtime com fallback explícito para settings."""

        payload = self.resolve_retrieval_config().payload
        raw_value = payload.get("top_k_default", settings.LLM_CONTEXT_TOP_K)
        top_k = int(raw_value)
        if top_k < 1:
            raise ValueError("top_k_default deve ser maior ou igual a 1.")
        return top_k

    def retrieval_embedding_version(self) -> str:
        """Retorna a versão ativa do embedding declarada para o retrieval."""

        payload = self.resolve_retrieval_config().payload
        return str(payload.get("embedding_version", settings.RAG_EMBEDDING_VERSION)).strip()

    def retrieval_strategy_name(self) -> str:
        """Retorna o nome tecnico da estrategia ativa de retrieval."""

        payload = self.resolve_retrieval_config().payload
        raw_value = str(payload.get("strategy_name", self.resolve_retrieval_config().version)).strip()
        if not raw_value:
            raise ValueError("strategy_name do retrieval nao pode ser vazio.")
        return raw_value

    def retrieval_supported_strategy_names(self) -> tuple[str, ...]:
        """Retorna as estrategias de retrieval declaradas pelo artefato ativo."""

        payload = self.resolve_retrieval_config().payload
        raw_values = payload.get("supported_strategies")
        active_strategy = self.retrieval_strategy_name()
        if raw_values in (None, []):
            return (active_strategy,)
        if not isinstance(raw_values, list):
            raise ValueError("supported_strategies do retrieval deve ser uma lista JSON.")

        normalized_values: list[str] = []
        for item in raw_values:
            normalized_item = str(item).strip()
            if normalized_item and normalized_item not in normalized_values:
                normalized_values.append(normalized_item)
        if not normalized_values:
            raise ValueError("supported_strategies do retrieval nao pode ficar vazia.")
        if active_strategy not in normalized_values:
            raise ValueError("A strategy_name ativa precisa constar em supported_strategies.")
        return tuple(normalized_values)

    def resolve_retrieval_strategy_name(self, strategy_name: str | None = None) -> str:
        """Resolve a strategy_name efetivamente usada na execucao."""

        desired_strategy = str(strategy_name or self.retrieval_strategy_name()).strip()
        if not desired_strategy:
            raise ValueError("strategy_name do retrieval nao pode ser vazia.")
        supported_strategies = self.retrieval_supported_strategy_names()
        if desired_strategy not in supported_strategies:
            raise ValueError(f"strategy_name de retrieval nao suportada: {desired_strategy}")
        return desired_strategy

    def retrieval_candidate_pool_multiplier(self) -> int:
        """Retorna o multiplicador do pool inicial de candidatos do retrieval."""

        payload = self.resolve_retrieval_config().payload
        multiplier = int(payload.get("candidate_pool_multiplier", 3))
        if multiplier < 1:
            raise ValueError("candidate_pool_multiplier deve ser maior ou igual a 1.")
        return multiplier

    def retrieval_score_weights(self) -> RetrievalScoreWeights:
        """Retorna os pesos ativos do score combinado do retrieval atual."""

        payload = self.resolve_retrieval_config().payload
        raw_weights = payload.get("score_weights", {})
        if raw_weights is None:
            raw_weights = {}
        if not isinstance(raw_weights, dict):
            raise ValueError("score_weights do retrieval deve ser um objeto JSON.")
        lexical = float(raw_weights.get("lexical", 0.75))
        semantic = float(raw_weights.get("semantic", 0.25))
        return RetrievalScoreWeights(lexical=lexical, semantic=semantic)

    def query_transform_strategy_name(self) -> str:
        """Retorna o nome tecnico da estrategia ativa de query transformation."""

        payload = self.resolve_retrieval_config().payload
        raw_value = str(payload.get("query_transform_strategy_name", NO_QUERY_TRANSFORM_STRATEGY_NAME)).strip()
        if not raw_value:
            raise ValueError("query_transform_strategy_name nao pode ser vazio.")
        return raw_value

    def query_transform_supported_strategy_names(self) -> tuple[str, ...]:
        """Retorna as estrategias de query transformation declaradas no artefato ativo."""

        payload = self.resolve_retrieval_config().payload
        raw_values = payload.get("supported_query_transform_strategies")
        active_strategy = self.query_transform_strategy_name()
        if raw_values in (None, []):
            return (active_strategy,)
        if not isinstance(raw_values, list):
            raise ValueError("supported_query_transform_strategies deve ser uma lista JSON.")

        normalized_values: list[str] = []
        for item in raw_values:
            normalized_item = str(item).strip()
            if normalized_item and normalized_item not in normalized_values:
                normalized_values.append(normalized_item)
        if not normalized_values:
            raise ValueError("supported_query_transform_strategies nao pode ficar vazia.")
        if active_strategy not in normalized_values:
            raise ValueError(
                "A query_transform_strategy_name ativa precisa constar em supported_query_transform_strategies."
            )
        return tuple(normalized_values)

    def resolve_query_transform_strategy_name(self, strategy_name: str | None = None) -> str:
        """Resolve a estrategia de query transformation usada na execucao."""

        desired_strategy = str(strategy_name or self.query_transform_strategy_name()).strip()
        if not desired_strategy:
            raise ValueError("query_transform_strategy_name nao pode ser vazia.")
        supported_strategies = self.query_transform_supported_strategy_names()
        if desired_strategy not in supported_strategies:
            raise ValueError(
                f"strategy_name de query transformation nao suportada: {desired_strategy}"
            )
        return desired_strategy

    def query_transformation_config(self) -> QueryTransformationConfig:
        """Retorna os parametros ativos da etapa de query transformation."""

        payload = self.resolve_retrieval_config().payload
        raw_params = payload.get("query_transform_params", {})
        if raw_params is None:
            raw_params = {}
        if not isinstance(raw_params, dict):
            raise ValueError("query_transform_params deve ser um objeto JSON.")

        max_added_terms = int(raw_params.get("max_added_terms", 4))
        raw_source_fields = raw_params.get("source_fields", ["keywords"])
        if not isinstance(raw_source_fields, list):
            raise ValueError("query_transform_params.source_fields deve ser uma lista JSON.")

        normalized_source_fields: list[str] = []
        for item in raw_source_fields:
            normalized_item = str(item).strip()
            if not normalized_item:
                continue
            if normalized_item not in SUPPORTED_QUERY_TRANSFORM_SOURCE_FIELDS:
                raise ValueError(
                    f"source_field de query transformation nao suportado: {normalized_item}"
                )
            if normalized_item not in normalized_source_fields:
                normalized_source_fields.append(normalized_item)

        return QueryTransformationConfig(
            max_added_terms=max_added_terms,
            source_fields=tuple(normalized_source_fields or ("keywords",)),
        )

    def rerank_strategy_name(self) -> str:
        """Retorna o nome tecnico da estrategia ativa de reranking."""

        payload = self.resolve_retrieval_config().payload
        raw_value = str(payload.get("rerank_strategy_name", NO_RERANK_STRATEGY_NAME)).strip()
        if not raw_value:
            raise ValueError("rerank_strategy_name nao pode ser vazio.")
        return raw_value

    def rerank_supported_strategy_names(self) -> tuple[str, ...]:
        """Retorna as estrategias de reranking declaradas no artefato ativo."""

        payload = self.resolve_retrieval_config().payload
        raw_values = payload.get("supported_rerank_strategies")
        active_strategy = self.rerank_strategy_name()
        if raw_values in (None, []):
            return (active_strategy,)
        if not isinstance(raw_values, list):
            raise ValueError("supported_rerank_strategies deve ser uma lista JSON.")

        normalized_values: list[str] = []
        for item in raw_values:
            normalized_item = str(item).strip()
            if normalized_item and normalized_item not in normalized_values:
                normalized_values.append(normalized_item)
        if not normalized_values:
            raise ValueError("supported_rerank_strategies nao pode ficar vazia.")
        if active_strategy not in normalized_values:
            raise ValueError(
                "A rerank_strategy_name ativa precisa constar em supported_rerank_strategies."
            )
        return tuple(normalized_values)

    def resolve_rerank_strategy_name(self, strategy_name: str | None = None) -> str:
        """Resolve a estrategia de reranking usada na execucao."""

        desired_strategy = str(strategy_name or self.rerank_strategy_name()).strip()
        if not desired_strategy:
            raise ValueError("rerank_strategy_name nao pode ser vazia.")
        supported_strategies = self.rerank_supported_strategy_names()
        if desired_strategy not in supported_strategies:
            raise ValueError(f"strategy_name de reranking nao suportada: {desired_strategy}")
        return desired_strategy

    def reranking_config(self) -> RerankingConfig:
        """Retorna os parametros ativos da etapa de reranking."""

        payload = self.resolve_retrieval_config().payload
        raw_params = payload.get("rerank_params", {})
        if raw_params is None:
            raw_params = {}
        if not isinstance(raw_params, dict):
            raise ValueError("rerank_params deve ser um objeto JSON.")

        max_candidates = int(raw_params.get("max_candidates", 5))
        raw_weights = raw_params.get("score_weights", {})
        if raw_weights is None:
            raw_weights = {}
        if not isinstance(raw_weights, dict):
            raise ValueError("rerank_params.score_weights deve ser um objeto JSON.")

        score_weights = RerankScoreWeights(
            retrieval_score=float(raw_weights.get("retrieval_score", 0.35)),
            title_overlap=float(raw_weights.get("title_overlap", 0.35)),
            tag_overlap=float(raw_weights.get("tag_overlap", 0.2)),
            text_density=float(raw_weights.get("text_density", 0.1)),
        )
        return RerankingConfig(
            max_candidates=max_candidates,
            score_weights=score_weights,
        )

    def chunk_split_strategy(self) -> str:
        """Retorna a estratégia ativa de fracionamento textual."""

        payload = self.resolve_chunking_config().payload
        return str(payload.get("split_strategy", "double_newline_paragraphs")).strip()

    def chunk_section_id_template(self) -> str:
        """Retorna o template ativo de identificador de seção."""

        payload = self.resolve_chunking_config().payload
        return str(payload.get("section_id_template", "section-{index}")).strip()

    def chunk_empty_content_fallback(self) -> str:
        """Retorna a política de fallback para conteúdo vazio no chunking."""

        payload = self.resolve_chunking_config().payload
        return str(payload.get("empty_content_fallback", "full_content")).strip()

    def _resolve_text_artifact(self, descriptor: VersionedArtifactDescriptor) -> ActiveTextArtifact:
        """Carrega um artefato textual e valida sua consistência com o sidecar."""

        artifact_path = self._artifact_path(descriptor)
        metadata = self._load_and_validate_metadata(descriptor, artifact_path)
        return ActiveTextArtifact(
            descriptor=descriptor,
            metadata=metadata,
            path=artifact_path,
            content=artifact_path.read_text(encoding="utf-8"),
        )

    def _resolve_json_artifact(self, descriptor: VersionedArtifactDescriptor) -> ActiveJsonArtifact:
        """Carrega um artefato JSON e valida sua consistência com o sidecar."""

        artifact_path = self._artifact_path(descriptor)
        metadata = self._load_and_validate_metadata(descriptor, artifact_path)
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"O artefato JSON ativo deve ser um objeto: {artifact_path}")
        return ActiveJsonArtifact(
            descriptor=descriptor,
            metadata=metadata,
            path=artifact_path,
            payload=payload,
        )

    def _load_and_validate_metadata(
        self,
        descriptor: VersionedArtifactDescriptor,
        artifact_path: Path,
    ) -> ArtifactVersionMetadata:
        """Carrega o sidecar e valida sua consistência com o artefato ativo."""

        metadata = load_artifact_metadata(self._metadata_path(descriptor))
        if metadata.artifact_type != descriptor.artifact_type:
            raise ValueError(f"artifact_type inconsistente para {artifact_path}")
        if metadata.artifact_name != descriptor.artifact_name:
            raise ValueError(f"artifact_name inconsistente para {artifact_path}")
        if metadata.version_label != descriptor.version:
            raise ValueError(f"version_label inconsistente para {artifact_path}")
        if metadata.content_hash != build_content_hash(artifact_path):
            raise ValueError(f"content_hash inconsistente para {artifact_path}")
        return metadata

    def _artifact_path(self, descriptor: VersionedArtifactDescriptor) -> Path:
        """Resolve o caminho absoluto do artefato a partir da pasta ativa."""

        return self.artifacts_dir / descriptor.relative_path

    def _metadata_path(self, descriptor: VersionedArtifactDescriptor) -> Path:
        """Resolve o caminho absoluto do sidecar a partir da pasta ativa."""

        artifact_path = self._artifact_path(descriptor)
        return artifact_path.with_suffix(f"{artifact_path.suffix}.meta.json")
