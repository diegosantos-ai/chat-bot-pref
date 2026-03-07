"""
Script de Teste A/B de Embedding Providers
==========================================
Compara qualidade de recuperação RAG entre os provedores:
  - default: ChromaDB built-in (all-MiniLM-L6-v2)
  - gemini:  Google Gemini Embedding 001
  - openai:  OpenAI text-embedding-3-large
  - qwen:    Qwen3 via OpenRouter

Métricas:
  - avg_best_score:  Score médio do chunk mais relevante
  - hit_rate_at_3:   Proporção de queries onde o doc esperado aparece no top-3
  - avg_latency_ms:  Latência média de embedding+busca por query
  - score_stddev:    Desvio padrão dos scores (maior = mais discriminativo)

Uso:
    python scripts/run_embedding_ab_test.py
    python scripts/run_embedding_ab_test.py --providers default,gemini
    python scripts/run_embedding_ab_test.py --output /tmp/ab_results.json

Requisitos:
    - .env com API keys dos provedores que deseja testar
    - pip install -r requirements.txt
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Adiciona raiz ao path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import chromadb  # noqa: E402

from app.rag.embeddings import (  # noqa: E402
    EmbeddingProvider,
    get_embedding_function,
    get_collection_name,
    resolve_embedding_model,
)

from app.settings import settings  # noqa: E402


# ========================================
# Corpus de teste
# ========================================

SAMPLE_DOCUMENTS = [
    {
        "id": "horarios",
        "text": "Horário de atendimento: Segunda a Sexta das 7h30 às 17h30. Não há atendimento aos sábados, domingos e feriados.",
        "domain": "Horários",
    },
    {
        "id": "contatos",
        "text": "Telefone da Prefeitura: (45) 3124-1000. Endereço: Av. Paraná, 61, centro. Atendimento presencial.",
        "domain": "Contatos",
    },
    {
        "id": "iptu",
        "text": "IPTU 2025: Prazo para pagamento com desconto de 10% até 31 de março de 2025. Emita sua guia no site.",
        "domain": "Tributos",
    },
    {
        "id": "refis",
        "text": "REFIS 2025: Programa de Recuperação Fiscal com desconto de até 100% em juros e multas. Negociação até 28/02/2025.",
        "domain": "Tributos",
    },
    {
        "id": "saude",
        "text": "PSF Centro: Unidade de Saúde. Telefone: (45) 3124-1025. Rua das Flores, 100. Atendimento médico e de enfermagem.",
        "domain": "Saúde",
    },
    {
        "id": "educacao",
        "text": "Matrícula escolar 2026: Período de 10 a 30 de janeiro. Documentos: RG, CPF, comprovante de residência e certidão de nascimento.",
        "domain": "Educação",
    },
    {
        "id": "cras",
        "text": "CRAS - Centro de Referência de Assistência Social: Telefone: (45) 3124-1030. Av. Brasília, 1050. Bolsa Família, Cadastro Único.",
        "domain": "Assistência Social",
    },
    {
        "id": "trabalhador",
        "text": "Agência do Trabalhador: (45) 3124-1000. Serviços: abertura de MEI, carteira de trabalho, SINE, intermediação de emprego.",
        "domain": "Empreendedorismo",
    },
]

BENCHMARK_QUERIES = [
    {
        "query": "Qual o horário de funcionamento?",
        "expected_id": "horarios",
        "description": "Horário - formulação direta",
    },
    {
        "query": "Que horas a prefeitura abre?",
        "expected_id": "horarios",
        "description": "Horário - paráfrase coloquial",
    },
    {
        "query": "Qual o número de telefone para entrar em contato?",
        "expected_id": "contatos",
        "description": "Contato - formulação formal",
    },
    {
        "query": "Tenho dívida de imposto predial, como regularizar?",
        "expected_id": "iptu",
        "description": "IPTU - terminologia leiga",
    },
    {
        "query": "REFIS parcelamento fiscal",
        "expected_id": "refis",
        "description": "REFIS - sigla direta",
    },
    {
        "query": "Estou doente, quero consulta médica",
        "expected_id": "saude",
        "description": "Saúde - formulação coloquial",
    },
    {
        "query": "Quero colocar meu filho na escola, o que preciso?",
        "expected_id": "educacao",
        "description": "Educação - formulação natural",
    },
    {
        "query": "Preciso de auxílio para minha família",
        "expected_id": "cras",
        "description": "Assistência social - formulação vaga",
    },
    {
        "query": "Quero abrir minha empresa MEI",
        "expected_id": "trabalhador",
        "description": "Empreendedorismo - sigla+contexto",
    },
    {
        "query": "Carteira de trabalho onde emitir",
        "expected_id": "trabalhador",
        "description": "Emprego - formulação direta",
    },
]


# ========================================
# Funções de teste
# ========================================


def get_available_providers(requested: Optional[List[str]] = None) -> List[str]:
    """Retorna provedores disponíveis (com API keys configuradas)."""
    has_openrouter = bool(settings.OPENROUTER_API_KEY)
    all_providers = [
        ("default", True),        # Sempre disponível (ChromaDB built-in)
        ("gemini", has_openrouter),  # Via OpenRouter
        ("openai", has_openrouter),  # Via OpenRouter
        ("qwen",   has_openrouter),  # Via OpenRouter
    ]

    available = [p for p, ok in all_providers if ok]

    if requested:
        unavailable = [p for p in requested if p not in available]
        if unavailable:
            print(f"\n[WARN] Provedores indisponíveis (sem API key): {unavailable}")
        return [p for p in requested if p in available]

    return available


def create_test_collection(
    client: chromadb.ClientAPI,
    provider: str,
    base_name: str = "ab_test_temp",
) -> chromadb.Collection:
    """Cria collection de teste com os documentos de benchmark."""
    col_name = get_collection_name(base_name, provider)

    # Remove collection existente para garantir dados frescos
    try:
        client.delete_collection(col_name)
    except Exception:
        pass

    ef = get_embedding_function(provider)
    kwargs = {
        "name": col_name,
        "metadata": {"hnsw:space": "cosine"},
    }
    if ef is not None:
        kwargs["embedding_function"] = ef

    collection = client.create_collection(**kwargs)

    print(f"  [INGEST] Ingerindo {len(SAMPLE_DOCUMENTS)} documentos para '{provider}'...")
    t0 = time.perf_counter()

    collection.add(
        ids=[doc["id"] for doc in SAMPLE_DOCUMENTS],
        documents=[doc["text"] for doc in SAMPLE_DOCUMENTS],
        metadatas=[{"domain": doc["domain"]} for doc in SAMPLE_DOCUMENTS],
    )

    elapsed = (time.perf_counter() - t0) * 1000
    print(f"     [OK] Ingestão concluída em {elapsed:.0f}ms")

    return collection


def run_benchmark(
    collection: chromadb.Collection,
    provider: str,
    top_k: int = 3,
) -> Dict:
    """Executa queries de benchmark e coleta métricas."""
    scores_all = []
    latencies = []
    hits = []
    query_results = []

    for bq in BENCHMARK_QUERIES:
        t0 = time.perf_counter()
        results = collection.query(
            query_texts=[bq["query"]],
            n_results=min(top_k, len(SAMPLE_DOCUMENTS)),
            include=["documents", "metadatas", "distances"],
        )
        elapsed = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed)

        ids = results["ids"][0] if results["ids"] else []
        distances = results["distances"][0] if results["distances"] else []

        best_score = (1 - distances[0]) if distances else 0.0
        scores_all.append(best_score)

        hit = bq["expected_id"] in ids
        hits.append(hit)

        query_results.append(
            {
                "query": bq["query"],
                "description": bq["description"],
                "expected_id": bq["expected_id"],
                "retrieved_ids": ids,
                "best_score": round(best_score, 4),
                "hit": hit,
                "latency_ms": round(elapsed, 1),
            }
        )

    import statistics

    avg_score = sum(scores_all) / len(scores_all) if scores_all else 0.0
    hit_rate = sum(hits) / len(hits) if hits else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    score_stddev = statistics.stdev(scores_all) if len(scores_all) > 1 else 0.0

    try:
        model_name = resolve_embedding_model(EmbeddingProvider(provider))
    except ValueError:
        model_name = ""
    if not model_name:
        model_name = "chromadb-default (all-MiniLM-L6-v2)"

    return {
        "provider": provider,
        "model": model_name,
        "queries_tested": len(BENCHMARK_QUERIES),
        "avg_best_score": round(avg_score, 4),
        "hit_rate_at_3": round(hit_rate, 4),
        "avg_latency_ms": round(avg_latency, 1),
        "score_stddev": round(score_stddev, 4),
        "per_query": query_results,
    }


def print_summary(results: List[Dict]) -> None:
    """Imprime tabela comparativa dos resultados."""
    print("\n" + "=" * 80)
    print("RELATÓRIO COMPARATIVO — EMBEDDING PROVIDERS A/B TEST")
    print("=" * 80)
    print(
        f"{'Provedor':<10} | {'Modelo':<35} | {'Avg Score':>9} | "
        f"{'Hit@3':>6} | {'Latência':>10} | {'Stddev':>7}"
    )
    print("-" * 80)

    for r in results:
        model_short = r["model"][:34] if len(r["model"]) > 34 else r["model"]
        print(
            f"{r['provider']:<10} | {model_short:<35} | "
            f"{r['avg_best_score']:>9.4f} | "
            f"{r['hit_rate_at_3']:>6.1%} | "
            f"{r['avg_latency_ms']:>8.0f}ms | "
            f"{r['score_stddev']:>7.4f}"
        )

    print("=" * 80)
    print()
    print("Legenda:")
    print("  Avg Score:  Score médio do chunk mais relevante por query (maior = melhor)")
    print("  Hit@3:      Taxa de acerto do doc esperado no top-3 (maior = melhor)")
    print("  Latência:   Tempo médio de busca por query (menor = melhor)")
    print("  Stddev:     Desvio padrão dos scores (maior = mais discriminativo)")
    print()

    # Destaca melhor em cada métrica
    if len(results) > 1:
        best_score_p = max(results, key=lambda r: r["avg_best_score"])["provider"]
        best_hit_p = max(results, key=lambda r: r["hit_rate_at_3"])["provider"]
        best_lat_p = min(results, key=lambda r: r["avg_latency_ms"])["provider"]
        best_disc_p = max(results, key=lambda r: r["score_stddev"])["provider"]

        print("Destaques:")
        print(f"   Maior score médio:     {best_score_p}")
        print(f"   Maior hit rate:        {best_hit_p}")
        print(f"   Menor latência:        {best_lat_p}")
        print(f"   Mais discriminativo:   {best_disc_p}")
        print()


def print_per_query_detail(results: List[Dict]) -> None:
    """Imprime detalhes por query para cada provedor."""
    print("\n" + "=" * 80)
    print("DETALHES POR QUERY")
    print("=" * 80)

    for bq_idx, bq in enumerate(BENCHMARK_QUERIES):
        print(f"\nQuery {bq_idx + 1}: {bq['query']}")
        print(f"   Domínio: {bq['description']}")
        print(f"   Esperado: {bq['expected_id']}")

        for r in results:
            pq = r["per_query"][bq_idx]
            hit_icon = "OK" if pq["hit"] else "MISS"
            print(
                f"   {r['provider']:8s}: score={pq['best_score']:.4f} "
                f"top3={pq['retrieved_ids']} {hit_icon}"
            )


# ========================================
# Main
# ========================================


def main():
    parser = argparse.ArgumentParser(
        description="Teste A/B de provedores de embedding para RAG"
    )
    parser.add_argument(
        "--providers",
        type=str,
        default=None,
        help="Provedores separados por vírgula (ex: default,gemini). Padrão: todos disponíveis.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Arquivo JSON para salvar resultados (ex: /tmp/ab_results.json)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Número de resultados a recuperar por query (padrão: 3)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Exibir detalhes por query",
    )
    args = parser.parse_args()

    requested = args.providers.split(",") if args.providers else None
    providers = get_available_providers(requested)

    if not providers:
        print("[ERROR] Nenhum provedor disponível. Configure API keys no .env.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("TESTE A/B — EMBEDDING PROVIDERS")
    print("=" * 60)
    print(f"Provedores: {providers}")
    print(f"Queries:    {len(BENCHMARK_QUERIES)}")
    print(f"Documentos: {len(SAMPLE_DOCUMENTS)}")
    print(f"Top-K:      {args.top_k}")
    print()

    # ChromaDB em memória para isolamento total
    client = chromadb.EphemeralClient()
    all_results = []

    for provider in providers:
        print(f"\n[TEST] Testando provedor: {provider}")
        try:
            collection = create_test_collection(client, provider)
            result = run_benchmark(collection, provider, top_k=args.top_k)
            all_results.append(result)
            print(
                f"  [OK] {provider}: avg_score={result['avg_best_score']:.4f}, "
                f"hit@3={result['hit_rate_at_3']:.1%}, "
                f"latency={result['avg_latency_ms']:.0f}ms"
            )
        except Exception as e:
            print(f"  [ERROR] {provider}: erro - {e}")

    if not all_results:
        print("\n[ERROR] Nenhum provedor executou com sucesso.")
        sys.exit(1)

    print_summary(all_results)

    if args.verbose:
        print_per_query_detail(all_results)

    # Salva resultados em JSON se solicitado
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\n[FILE] Resultados salvos em: {output_path}")


if __name__ == "__main__":
    main()
