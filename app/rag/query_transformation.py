"""Transformacao controlada de query antes do retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from app.rag.retrieval_scoring import tokenize_retrieval_text

NO_QUERY_TRANSFORM_STRATEGY_NAME = "no_query_transformation_v1"
TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME = "tenant_keyword_query_expansion_v1"
SUPPORTED_QUERY_TRANSFORM_SOURCE_FIELDS = ("keywords", "intents")


class QueryTransformDocument(Protocol):
    """Contrato minimo do documento usado na expansao heuristica da query."""

    keywords: list[str]
    intents: list[str]


@dataclass(frozen=True, slots=True)
class QueryTransformationConfig:
    """Representa os parametros ativos da transformacao de query."""

    max_added_terms: int
    source_fields: tuple[str, ...]

    def __post_init__(self) -> None:
        """Valida a configuracao minima para evitar expansao silenciosa invalida."""

        if self.max_added_terms < 1:
            raise ValueError("max_added_terms da transformacao de query deve ser maior ou igual a 1.")
        if not self.source_fields:
            raise ValueError("source_fields da transformacao de query nao pode ficar vazio.")


@dataclass(frozen=True, slots=True)
class QueryTransformationResult:
    """Representa o resultado tecnico da etapa de transformacao da query."""

    strategy_name: str
    applied: bool
    original_query: str
    retrieval_query: str
    added_terms: tuple[str, ...]
    source_fields: tuple[str, ...]
    max_added_terms: int


def build_identity_query_transformation(
    *,
    query_text: str,
    strategy_name: str,
    config: QueryTransformationConfig,
) -> QueryTransformationResult:
    """Retorna um resultado sem alteracao da query original."""

    return QueryTransformationResult(
        strategy_name=strategy_name,
        applied=False,
        original_query=query_text,
        retrieval_query=query_text,
        added_terms=(),
        source_fields=config.source_fields,
        max_added_terms=config.max_added_terms,
    )


class QueryTransformationService:
    """Aplica transformacao heuristica de query de forma opt-in e rastreavel."""

    def transform_query(
        self,
        *,
        query_text: str,
        documents: Sequence[QueryTransformDocument],
        strategy_name: str,
        config: QueryTransformationConfig,
    ) -> QueryTransformationResult:
        """Transforma a query original quando a estrategia ativa permitir expansao."""

        if strategy_name == NO_QUERY_TRANSFORM_STRATEGY_NAME:
            return build_identity_query_transformation(
                query_text=query_text,
                strategy_name=strategy_name,
                config=config,
            )
        if strategy_name != TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME:
            raise ValueError(f"strategy_name de query transformation nao suportada: {strategy_name}")

        query_tokens = tuple(dict.fromkeys(tokenize_retrieval_text(query_text)))
        if not query_tokens:
            return build_identity_query_transformation(
                query_text=query_text,
                strategy_name=strategy_name,
                config=config,
            )

        added_terms = self._select_expansion_terms(
            query_tokens=query_tokens,
            documents=documents,
            config=config,
        )
        if not added_terms:
            return build_identity_query_transformation(
                query_text=query_text,
                strategy_name=strategy_name,
                config=config,
            )

        retrieval_query = f"{query_text} {' '.join(added_terms)}".strip()
        return QueryTransformationResult(
            strategy_name=strategy_name,
            applied=True,
            original_query=query_text,
            retrieval_query=retrieval_query,
            added_terms=tuple(added_terms),
            source_fields=config.source_fields,
            max_added_terms=config.max_added_terms,
        )

    def _select_expansion_terms(
        self,
        *,
        query_tokens: Sequence[str],
        documents: Sequence[QueryTransformDocument],
        config: QueryTransformationConfig,
    ) -> list[str]:
        """Seleciona poucos termos adicionais a partir de metadados do tenant."""

        unique_query_tokens = {token for token in query_tokens if token}
        candidate_entries: list[tuple[int, int, tuple[str, ...]]] = []

        for document in documents:
            document_metadata_tokens: list[str] = []
            for field_name in config.source_fields:
                for raw_value in self._iter_field_values(document, field_name):
                    document_metadata_tokens.extend(tokenize_retrieval_text(raw_value))

            unique_document_tokens = tuple(dict.fromkeys(document_metadata_tokens))
            if not unique_document_tokens:
                continue
            overlap_count = len(unique_query_tokens.intersection(unique_document_tokens))
            if overlap_count == 0:
                continue
            new_terms = tuple(
                token
                for token in unique_document_tokens
                if token not in unique_query_tokens
            )
            if not new_terms:
                continue
            candidate_entries.append((overlap_count, len(new_terms), new_terms))

        candidate_entries.sort(key=lambda item: (-item[0], item[1], item[2]))

        selected_terms: list[str] = []
        for _, _, new_terms in candidate_entries:
            for term in new_terms:
                if term in unique_query_tokens or term in selected_terms:
                    continue
                selected_terms.append(term)
                if len(selected_terms) >= config.max_added_terms:
                    return selected_terms
        return selected_terms

    def _iter_field_values(
        self,
        document: QueryTransformDocument,
        field_name: str,
    ) -> tuple[str, ...]:
        """Extrai os valores configurados do documento sem assumir estrutura externa."""

        if field_name not in SUPPORTED_QUERY_TRANSFORM_SOURCE_FIELDS:
            raise ValueError(f"source_field de query transformation nao suportado: {field_name}")
        raw_value = getattr(document, field_name)
        values = raw_value if isinstance(raw_value, list) else [raw_value]
        normalized_values = [str(value).strip() for value in values if str(value).strip()]
        return tuple(normalized_values)
