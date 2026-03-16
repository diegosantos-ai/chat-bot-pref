from app.contracts.dto import RagDocumentRecord
from app.llmops import ActiveArtifactResolver
from app.rag.query_transformation import (
    NO_QUERY_TRANSFORM_STRATEGY_NAME,
    TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME,
    QueryTransformationService,
)


def test_query_transformation_disabled_preserves_original_query() -> None:
    service = QueryTransformationService()
    resolver = ActiveArtifactResolver()

    result = service.transform_query(
        query_text="Qual o horario?",
        documents=[
            RagDocumentRecord(
                tenant_id="prefeitura-demo",
                title="Horario Alvara",
                content="Conteudo",
                keywords=["alvara", "horario"],
                intents=["INFO_REQUEST"],
            )
        ],
        strategy_name=NO_QUERY_TRANSFORM_STRATEGY_NAME,
        config=resolver.query_transformation_config(),
    )

    assert result.strategy_name == NO_QUERY_TRANSFORM_STRATEGY_NAME
    assert result.applied is False
    assert result.original_query == "Qual o horario?"
    assert result.retrieval_query == "Qual o horario?"
    assert result.added_terms == ()


def test_query_transformation_expands_query_from_tenant_keywords() -> None:
    service = QueryTransformationService()
    resolver = ActiveArtifactResolver()

    result = service.transform_query(
        query_text="Qual o horario?",
        documents=[
            RagDocumentRecord(
                tenant_id="prefeitura-demo",
                title="Horario Alvara",
                content="Conteudo",
                keywords=["alvara", "horario"],
                intents=["INFO_REQUEST"],
            ),
            RagDocumentRecord(
                tenant_id="prefeitura-demo",
                title="Outra Guia",
                content="Conteudo",
                keywords=["guia"],
                intents=["INFO_REQUEST"],
            ),
        ],
        strategy_name=TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME,
        config=resolver.query_transformation_config(),
    )

    assert result.strategy_name == TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME
    assert result.applied is True
    assert result.original_query == "Qual o horario?"
    assert result.retrieval_query == "Qual o horario? alvara"
    assert result.added_terms == ("alvara",)
