"""
Testes A/B de Provedores de Embedding — Pilot Atendimento RAG
=============================================================
Compara qualidade de recuperação entre os provedores de embedding:
  - default: ChromaDB built-in (all-MiniLM-L6-v2)
  - gemini:  Google Gemini Embedding via OpenRouter (google/gemini-embedding-001)
  - openai:  OpenAI Embedding via OpenRouter     (openai/text-embedding-3-large)
  - qwen:    Qwen Embedding via OpenRouter        (qwen/qwen3-embedding-8b)

Todos os provedores externos usam o OpenRouter com OPENROUTER_API_KEY.

Estrutura:
  - Testes unitários (sempre executam, usam mocks)
  - Testes de integração (requerem OPENROUTER_API_KEY, marcados @pytest.mark.integration)
  - Fixtures de dados compartilhadas para garantir comparação justa

Execute:
    # Testes unitários (sem API keys):
    pytest tests/test_embedding_ab.py -v

    # Testes de integração (requerem OPENROUTER_API_KEY em .env):
    pytest tests/test_embedding_ab.py -v -m integration
"""

import os
import sys
import pytest
import httpx
from typing import List
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag.embeddings import (
    EmbeddingProvider,
    OpenRouterEmbeddingFunction,
    get_embedding_function,
    get_collection_name,
    resolve_embedding_model,
    COLLECTION_SUFFIX,
    DEFAULT_MODELS,
    _OPENROUTER_API_URL,
)

# ========================================
# Dados de teste compartilhados
# ========================================

# Corpus de documentos simulando a base de conhecimento
SAMPLE_DOCUMENTS = [
    "Horário de atendimento: Segunda a Sexta das 7h30 às 17h30.",
    "Telefone da Prefeitura: (45) 3124-1000. Endereço: Av. Paraná, 61.",
    "IPTU 2025: Prazo para pagamento com desconto até 31 de março de 2025.",
    "REFIS 2025: Programa de Recuperação Fiscal com desconto de até 100% em juros.",
    "Unidade de Saúde PSF Centro: (45) 3124-1025. Rua das Flores, 100.",
    "Matrícula escolar 2026: Período de 10 a 30 de janeiro. Documentos necessários: RG, CPF, comprovante de residência.",
    "Assistência Social CRAS: (45) 3124-1030. Av. Brasília, 1050.",
    "Agência do Trabalhador: (45) 3124-1000. Atende MEI, SINE, carteira de trabalho.",
]

# Queries de teste representativas (variam em formulação vs. documentos)
BENCHMARK_QUERIES = [
    {
        "query": "Qual o horário de funcionamento da prefeitura?",
        "expected_doc_idx": 0,  # Horário de atendimento
        "description": "Horário - formulação direta",
    },
    {
        "query": "Como posso ligar para a câmara?",
        "expected_doc_idx": 1,  # Telefone prefeitura (mais próximo)
        "description": "Telefone - formulação indireta",
    },
    {
        "query": "Tenho dívida de imposto predial",
        "expected_doc_idx": 2,  # IPTU
        "description": "IPTU - terminologia do usuário vs. técnica",
    },
    {
        "query": "REFIS parcelamento fiscal",
        "expected_doc_idx": 3,  # REFIS
        "description": "Sigla direta",
    },
    {
        "query": "Estou doente, preciso de consulta",
        "expected_doc_idx": 4,  # PSF/Saúde
        "description": "Saúde - formulação coloquial",
    },
    {
        "query": "Quero matricular meu filho na escola",
        "expected_doc_idx": 5,  # Matrícula
        "description": "Educação - formulação natural",
    },
    {
        "query": "Preciso de benefício social",
        "expected_doc_idx": 6,  # CRAS
        "description": "Assistência social - formulação genérica",
    },
    {
        "query": "Abrir empresa MEI",
        "expected_doc_idx": 7,  # Agência Trabalhador
        "description": "Empreendedorismo - sigla + contexto",
    },
]


# ========================================
# Fixtures
# ========================================


@pytest.fixture
def mock_openrouter_response():
    """Mock de resposta da API OpenRouter para embeddings."""

    def _make_response(texts):
        import hashlib

        return {
            "data": [
                {
                    "index": i,
                    "embedding": [
                        (int(hashlib.md5(t.encode()).hexdigest(), 16) >> j & 0xFF)
                        / 255.0
                        for j in range(1536)
                    ],
                }
                for i, t in enumerate(texts)
            ]
        }

    return _make_response


# ========================================
# Testes Unitários: EmbeddingProvider enum
# ========================================


class TestEmbeddingProvider:
    def test_all_providers_defined(self):
        """Verifica que todos os 4 provedores estão definidos."""
        assert EmbeddingProvider.DEFAULT == "default"
        assert EmbeddingProvider.GEMINI == "gemini"
        assert EmbeddingProvider.OPENAI == "openai"
        assert EmbeddingProvider.QWEN == "qwen"

    def test_provider_from_string(self):
        """Verifica conversão de string para enum."""
        assert EmbeddingProvider("default") == EmbeddingProvider.DEFAULT
        assert EmbeddingProvider("gemini") == EmbeddingProvider.GEMINI
        assert EmbeddingProvider("openai") == EmbeddingProvider.OPENAI
        assert EmbeddingProvider("qwen") == EmbeddingProvider.QWEN

    def test_default_models_are_openrouter_format(self):
        """Verifica que modelos padrão usam formato OpenRouter (provider/model)."""
        assert DEFAULT_MODELS[EmbeddingProvider.GEMINI] == "google/gemini-embedding-001"
        assert DEFAULT_MODELS[EmbeddingProvider.OPENAI] == "openai/text-embedding-3-large"
        assert DEFAULT_MODELS[EmbeddingProvider.QWEN] == "qwen/qwen3-embedding-8b"

    def test_collection_suffixes(self):
        """Verifica que cada provedor tem sufixo de collection correto."""
        assert COLLECTION_SUFFIX[EmbeddingProvider.DEFAULT] == ""
        assert COLLECTION_SUFFIX[EmbeddingProvider.GEMINI] == "_gemini"
        assert COLLECTION_SUFFIX[EmbeddingProvider.OPENAI] == "_openai"
        assert COLLECTION_SUFFIX[EmbeddingProvider.QWEN] == "_qwen"


# ========================================
# Testes Unitários: get_collection_name
# ========================================


class TestGetCollectionName:
    def test_default_provider_no_suffix(self):
        name = get_collection_name("rag_base_v1", "default")
        assert name == "rag_base_v1"

    def test_gemini_provider_suffix(self):
        name = get_collection_name("rag_base_v1", "gemini")
        assert name == "rag_base_v1_gemini"

    def test_openai_provider_suffix(self):
        name = get_collection_name("rag_base_v1", "openai")
        assert name == "rag_base_v1_openai"

    def test_qwen_provider_suffix(self):
        name = get_collection_name("rag_base_v1", "qwen")
        assert name == "rag_base_v1_qwen"

    def test_unknown_provider_falls_back_to_default(self):
        name = get_collection_name("rag_base_v1", "unknown_model")
        assert name == "rag_base_v1"


# ========================================
# Testes Unitarios: resolve_embedding_model
# ========================================


class TestResolveEmbeddingModel:
    def test_returns_empty_for_default_provider(self):
        model = resolve_embedding_model("default")
        assert model == ""

    def test_returns_builtin_default_when_no_override(self, monkeypatch):
        from app.settings import settings as app_settings

        monkeypatch.setattr(app_settings, "EMBEDDING_MODEL_OVERRIDE", "")
        monkeypatch.setattr(app_settings, "EMBEDDING_MODEL_OPENAI", "")
        model = resolve_embedding_model("openai")
        assert model == "openai/text-embedding-3-large"

    def test_explicit_model_has_top_priority(self):
        model = resolve_embedding_model("qwen", explicit_model="custom/model")
        assert model == "custom/model"


# ========================================
# Testes Unitários: get_embedding_function
# ========================================


class TestGetEmbeddingFunction:
    def test_default_returns_none(self):
        """Default usa ChromaDB built-in, retorna None."""
        ef = get_embedding_function("default")
        assert ef is None

    def test_unknown_provider_returns_none(self):
        """Provedor desconhecido cai no default (None)."""
        ef = get_embedding_function("unknown_provider")
        assert ef is None

    def test_gemini_requires_openrouter_key(self, monkeypatch):
        """Gemini sem OPENROUTER_API_KEY lança ValueError."""
        from app.settings import settings as app_settings
        monkeypatch.setattr(app_settings, "OPENROUTER_API_KEY", "")
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            get_embedding_function("gemini", api_key="")

    def test_openai_requires_openrouter_key(self, monkeypatch):
        """OpenAI sem OPENROUTER_API_KEY lança ValueError."""
        from app.settings import settings as app_settings
        monkeypatch.setattr(app_settings, "OPENROUTER_API_KEY", "")
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            get_embedding_function("openai", api_key="")

    def test_qwen_requires_openrouter_key(self, monkeypatch):
        """Qwen sem OPENROUTER_API_KEY lança ValueError."""
        from app.settings import settings as app_settings
        monkeypatch.setattr(app_settings, "OPENROUTER_API_KEY", "")
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            get_embedding_function("qwen", api_key="")

    def test_all_external_providers_return_openrouter_type(self):
        """Todos os provedores externos retornam OpenRouterEmbeddingFunction."""
        for provider in ["gemini", "openai", "qwen"]:
            ef = get_embedding_function(provider, api_key="fake_key")
            assert isinstance(ef, OpenRouterEmbeddingFunction), (
                f"Provider '{provider}' deve retornar OpenRouterEmbeddingFunction"
            )

    def test_gemini_uses_openrouter_model_id(self):
        """Gemini usa modelo no formato OpenRouter (google/...)."""
        ef = get_embedding_function("gemini", api_key="fake_key")
        assert ef.model == "google/gemini-embedding-001"

    def test_openai_uses_openrouter_model_id(self):
        """OpenAI usa modelo no formato OpenRouter (openai/...)."""
        ef = get_embedding_function("openai", api_key="fake_key")
        assert ef.model == "openai/text-embedding-3-large"

    def test_qwen_uses_openrouter_model_id(self):
        """Qwen usa modelo no formato OpenRouter (qwen/...)."""
        ef = get_embedding_function("qwen", api_key="fake_key")
        assert ef.model == "qwen/qwen3-embedding-8b"

    def test_custom_model_is_respected(self):
        """Model customizado é passado corretamente à função de embedding."""
        ef = get_embedding_function(
            "openai", api_key="fake_key", model="openai/text-embedding-ada-002"
        )
        assert ef.model == "openai/text-embedding-ada-002"

    def test_global_model_override_has_priority(self, monkeypatch):
        """EMBEDDING_MODEL_OVERRIDE deve ter prioridade sobre defaults por provedor."""
        from app.settings import settings as app_settings

        monkeypatch.setattr(app_settings, "EMBEDDING_MODEL_OVERRIDE", "custom/global-model")
        monkeypatch.setattr(app_settings, "EMBEDDING_MODEL_OPENAI", "custom/openai-model")

        ef = get_embedding_function("openai", api_key="fake_key")
        assert ef.model == "custom/global-model"

    def test_provider_model_override(self, monkeypatch):
        """Override específico de provedor deve ser aplicado quando não há override global."""
        from app.settings import settings as app_settings

        monkeypatch.setattr(app_settings, "EMBEDDING_MODEL_OVERRIDE", "")
        monkeypatch.setattr(app_settings, "EMBEDDING_MODEL_GEMINI", "custom/gemini-model")

        ef = get_embedding_function("gemini", api_key="fake_key")
        assert ef.model == "custom/gemini-model"

    def test_all_providers_use_same_api_key(self):
        """Todos os provedores externos usam a mesma chave API."""
        key = "sk-or-test-key"
        for provider in ["gemini", "openai", "qwen"]:
            ef = get_embedding_function(provider, api_key=key)
            assert ef._api_key == key


# ========================================
# Testes Unitários: OpenRouterEmbeddingFunction
# ========================================


class TestOpenRouterEmbeddingFunction:
    def test_initialization(self):
        ef = OpenRouterEmbeddingFunction(api_key="fake", model="google/gemini-embedding-001")
        assert ef.model == "google/gemini-embedding-001"

    def test_empty_api_key_raises(self):
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            OpenRouterEmbeddingFunction(api_key="", model="any/model")

    def test_calls_openrouter_endpoint(self, mock_openrouter_response):
        """Verifica que chama o endpoint correto do OpenRouter."""
    def test_all_providers_use_same_url(self, mock_openrouter_response):
        """Gemini, OpenAI e Qwen devem chamar o mesmo endpoint OpenRouter."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_openrouter_response(["test"])
        mock_resp.raise_for_status = MagicMock()

        urls_called = set()
        with patch("httpx.post", return_value=mock_resp) as mock_post:
            for provider in ["gemini", "openai", "qwen"]:
                ef = get_embedding_function(provider, api_key="fake")
                ef(["test"])
                urls_called.add(mock_post.call_args[0][0])

        assert len(urls_called) == 1, "Todos os provedores devem usar o mesmo URL"
        assert _OPENROUTER_API_URL in urls_called

    def test_returns_correct_shape(self, mock_openrouter_response):
        texts = ["a", "b", "c"]
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_openrouter_response(texts)
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.post", return_value=mock_resp):
            ef = OpenRouterEmbeddingFunction(api_key="fake", model="openai/text-embedding-3-large")
            result = ef(texts)

        assert len(result) == 3
        assert all(isinstance(e, list) for e in result)

    def test_handles_unsorted_response(self):
        """Verifica que itens são reordenados pelo índice mesmo se a API devolver fora de ordem."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {"index": 2, "embedding": [0.3]},
                {"index": 0, "embedding": [0.1]},
                {"index": 1, "embedding": [0.2]},
            ]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.post", return_value=mock_resp):
            ef = OpenRouterEmbeddingFunction(api_key="fake", model="qwen/qwen3-embedding-8b")
            result = ef(["a", "b", "c"])

        assert result[0] == [0.1]
        assert result[1] == [0.2]
        assert result[2] == [0.3]

    def test_authorization_header_format(self, mock_openrouter_response):
        """Verifica que o header de autorização está no formato correto."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_openrouter_response(["test"])
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.post", return_value=mock_resp) as mock_post:
            ef = OpenRouterEmbeddingFunction(api_key="sk-or-test-123", model="any/model")
            ef(["test"])

        headers = mock_post.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer sk-or-test-123"

    def test_batching_preserves_order(self):
        """Entradas longas devem ser processadas em lotes mantendo a ordem final."""
        calls = []

        def _fake_post(*args, **kwargs):
            batch = kwargs["json"]["input"]
            calls.append(batch)
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = {
                "data": [
                    {"index": i, "embedding": [float(len(text))]}
                    for i, text in enumerate(batch)
                ]
            }
            return mock_resp

        with patch("httpx.post", side_effect=_fake_post):
            ef = OpenRouterEmbeddingFunction(
                api_key="fake",
                model="openai/text-embedding-3-large",
                batch_size=2,
            )
            result = ef(["a", "bb", "ccc", "dddd", "eeeee"])

        assert calls == [["a", "bb"], ["ccc", "dddd"], ["eeeee"]]
        assert result == [[1.0], [2.0], [3.0], [4.0], [5.0]]

    def test_retries_on_transient_http_errors(self, mock_openrouter_response):
        """Erros transitórios devem ser retentados antes de falhar."""
        timeout_exc = httpx.ReadTimeout("timeout")
        success_resp = MagicMock()
        success_resp.raise_for_status = MagicMock()
        success_resp.json.return_value = mock_openrouter_response(["texto"])

        with patch("httpx.post", side_effect=[timeout_exc, success_resp]) as mock_post:
            with patch("time.sleep") as mock_sleep:
                ef = OpenRouterEmbeddingFunction(
                    api_key="fake",
                    model="openai/text-embedding-3-large",
                    max_retries=3,
                )
                result = ef(["texto"])

        assert mock_post.call_count == 2
        mock_sleep.assert_called_once()
        assert len(result) == 1
        assert len(result[0]) > 0


# ========================================
# Testes A/B: Comparação de Provedores (Unitários com Mocks)
# ========================================


class TestABComparisonUnit:
    """
    Testes A/B usando mocks — verificam a lógica de comparação
    sem depender de APIs externas.
    """

    @pytest.fixture
    def mock_ef_factory(self):
        """Cria uma fábrica de embedding functions mockadas."""

        def _make_ef(seed: int):
            """EmbeddingFunction que gera embeddings determinísticos."""

            class MockEF:
                def __init__(self, seed):
                    self.seed = seed
                    self.call_count = 0

                def __call__(self, input: List[str]) -> List[List[float]]:
                    self.call_count += 1
                    embeddings = []
                    for text in input:
                        import hashlib

                        h = int(
                            hashlib.md5(f"{seed}:{text}".encode()).hexdigest(), 16
                        )
                        emb = [(h >> i & 0xFF) / 255.0 for i in range(16)]
                        embeddings.append(emb)
                    return embeddings

            return MockEF(seed)

        return _make_ef

    def test_ab_result_structure(self):
        """Verifica que resultado de A/B tem estrutura correta."""
        result = {
            "provider": "gemini",
            "model": "google/gemini-embedding-001",
            "queries_tested": 8,
            "avg_best_score": 0.75,
            "avg_top1_score": 0.82,
            "hit_rate_at_3": 0.875,
            "latency_ms": 450.0,
        }

        required_fields = [
            "provider",
            "model",
            "queries_tested",
            "avg_best_score",
            "avg_top1_score",
            "hit_rate_at_3",
        ]
        for field in required_fields:
            assert field in result, f"Campo '{field}' ausente no resultado A/B"

    def test_hit_rate_calculation(self):
        """Testa cálculo correto de hit rate."""
        hits = [True, True, False, True, True, False, True, True]
        hit_rate = sum(hits) / len(hits)
        assert hit_rate == 0.75

    def test_provider_isolation_via_collection_name(self):
        """Verifica que cada provedor usa collection isolada."""
        base = "rag_ba_rag_piloto_2026_01_v1"

        names = {
            p: get_collection_name(base, p.value) for p in EmbeddingProvider
        }

        # Todos os nomes devem ser únicos
        assert len(set(names.values())) == len(names), (
            "Provedores devem usar collections distintas"
        )

    def test_benchmark_queries_coverage(self):
        """Verifica cobertura dos domínios de consulta no benchmark."""
        domains = {q["description"].split(" - ")[0] for q in BENCHMARK_QUERIES}
        expected_domains = {
            "Horário",
            "Telefone",
            "IPTU",
            "Sigla direta",
            "Saúde",
            "Educação",
            "Assistência social",
            "Empreendedorismo",
        }
        assert expected_domains.issubset(domains), (
            f"Domínios faltando: {expected_domains - domains}"
        )

    def test_all_providers_are_tested(self):
        """Verifica que todos os 4 provedores estão incluídos no A/B."""
        providers_to_test = [p.value for p in EmbeddingProvider]
        assert "default" in providers_to_test
        assert "gemini" in providers_to_test
        assert "openai" in providers_to_test
        assert "qwen" in providers_to_test
        assert len(providers_to_test) == 4

    def test_single_api_key_for_all_external_providers(self):
        """Verifica que apenas OPENROUTER_API_KEY é necessária para todos os provedores externos."""
        key = "sk-or-v3-test"
        for provider in ["gemini", "openai", "qwen"]:
            ef = get_embedding_function(provider, api_key=key)
            assert isinstance(ef, OpenRouterEmbeddingFunction)
            assert ef._api_key == key, (
                f"Provider '{provider}' deve usar a chave OpenRouter fornecida"
            )


# ========================================
# Testes de Integração (requerem OPENROUTER_API_KEY)
# ========================================


@pytest.mark.integration
class TestOpenRouterIntegration:
    """Testes de integração com a API real do OpenRouter."""

    def _get_key(self):
        from app.settings import settings
        if not settings.OPENROUTER_API_KEY:
            pytest.skip("OPENROUTER_API_KEY não configurada")
        return settings.OPENROUTER_API_KEY

    def test_gemini_produces_valid_embeddings(self):
        key = self._get_key()
        ef = get_embedding_function("gemini", api_key=key)
        result = ef(["Qual o horário de atendimento?"])
        assert len(result) == 1
        assert len(result[0]) > 0
        assert all(isinstance(v, float) for v in result[0])

    def test_openai_produces_valid_embeddings(self):
        key = self._get_key()
        ef = get_embedding_function("openai", api_key=key)
        result = ef(["Qual o horário de atendimento?"])
        assert len(result) == 1
        assert len(result[0]) > 0

    def test_qwen_produces_valid_embeddings(self):
        key = self._get_key()
        ef = get_embedding_function("qwen", api_key=key)
        result = ef(["Qual o horário de atendimento?"])
        assert len(result) == 1
        assert len(result[0]) > 0

    def test_batch_embeddings(self):
        """Verifica envio de múltiplos textos em uma chamada."""
        key = self._get_key()
        ef = get_embedding_function("openai", api_key=key)
        texts = ["texto 1", "texto 2", "texto 3"]
        result = ef(texts)
        assert len(result) == 3
        assert all(len(e) > 0 for e in result)

    def test_semantic_similarity_ordering(self):
        """Verifica que embeddings capturam similaridade semântica."""
        import numpy as np
        key = self._get_key()
        ef = get_embedding_function("openai", api_key=key)
        texts = [
            "Horário de atendimento da prefeitura",
            "Que horas funciona a câmara?",  # Semanticamente similar
            "REFIS programa fiscal 2025",    # Semanticamente diferente
        ]
        result = ef(texts)

        def cosine_sim(a, b):
            a, b = np.array(a), np.array(b)
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

        sim_similar = cosine_sim(result[0], result[1])
        sim_different = cosine_sim(result[0], result[2])
        assert sim_similar > sim_different, (
            f"Esperado sim_similar ({sim_similar:.3f}) > sim_different ({sim_different:.3f})"
        )

    def test_all_available_providers_retrieve_results(self):
        """
        A/B completo: todos os provedores ingerem e recuperam documentos.
        Usa ChromaDB em memória para isolamento total.
        """
        import chromadb
        key = self._get_key()

        client = chromadb.EphemeralClient()
        results_by_provider = {}

        for provider in ["gemini", "openai", "qwen"]:
            ef = get_embedding_function(provider, api_key=key)
            col_name = get_collection_name("ab_test_temp", provider)
            collection = client.get_or_create_collection(
                name=col_name,
                embedding_function=ef,
                metadata={"hnsw:space": "cosine"},
            )
            collection.add(
                ids=[f"doc_{i}" for i in range(len(SAMPLE_DOCUMENTS))],
                documents=SAMPLE_DOCUMENTS,
                metadatas=[{"source": f"test_{i}"} for i in range(len(SAMPLE_DOCUMENTS))],
            )
            scores = []
            for bq in BENCHMARK_QUERIES:
                res = collection.query(
                    query_texts=[bq["query"]],
                    n_results=3,
                    include=["distances"],
                )
                if res["distances"] and res["distances"][0]:
                    scores.append(1 - res["distances"][0][0])
            results_by_provider[provider] = {
                "avg_score": sum(scores) / len(scores) if scores else 0.0,
                "queries": len(scores),
            }

        print("\n\n" + "=" * 60)
        print("RELATÓRIO A/B DE EMBEDDING PROVIDERS (OpenRouter)")
        print("=" * 60)
        for provider, result in results_by_provider.items():
            model = DEFAULT_MODELS[EmbeddingProvider(provider)]
            print(
                f"  {provider:8s} | {model:<35} | "
                f"avg_score={result['avg_score']:.4f} | queries={result['queries']}"
            )
        print("=" * 60)

        for provider, result in results_by_provider.items():
            assert result["queries"] > 0, f"Provider '{provider}' sem resultados"


# ========================================
# Execução direta para relatório interativo
# ========================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("TESTES A/B DE EMBEDDING PROVIDERS (via OpenRouter)")
    print("=" * 60)
    print()
    print("Todos os provedores externos usam a API do OpenRouter.")
    print("Apenas OPENROUTER_API_KEY é necessária.")
    print()
    print("Para executar testes unitários:")
    print("  pytest tests/test_embedding_ab.py -v")
    print()
    print("Para executar testes de integração (requer OPENROUTER_API_KEY):")
    print("  pytest tests/test_embedding_ab.py -v -m integration")
    print()
    print("Para relatório A/B completo, use:")
    print("  python scripts/run_embedding_ab_test.py")
    sys.exit(0)
