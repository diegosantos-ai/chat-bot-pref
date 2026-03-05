"""
Testes para o módulo de siglas (acronyms)

Execute com:
    python -m pytest tests/test_acronyms.py -v

Ou diretamente:
    python tests/test_acronyms.py
"""

import sys
import os

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag.acronyms import (
    extract_acronyms_from_query,
    get_acronym_boost,
    get_acronym_meaning,
    list_all_acronyms,
    ACRONYM_BOOST_VALUE,
)


def test_extract_acronyms_basic():
    """Testa extração básica de siglas."""
    # Teste simples
    result = extract_acronyms_from_query("quero saber sobre o REFIS")
    assert "REFIS" in result, f"Esperado ['REFIS'], obtido {result}"
    print("✓ Extração básica funciona")


def test_extract_acronyms_case_insensitive():
    """Testa que a extração é case-insensitive."""
    test_cases = [
        ("refis", ["REFIS"]),
        ("REFIS", ["REFIS"]),
        ("Refis", ["REFIS"]),
        ("ReFiS", ["REFIS"]),
    ]

    for query, expected in test_cases:
        result = extract_acronyms_from_query(query)
        assert result == expected, (
            f"Query '{query}': esperado {expected}, obtido {result}"
        )

    print("✓ Case-insensitive funciona")


def test_extract_multiple_acronyms():
    """Testa extração de múltiplas siglas."""
    query = "como emitir NFS-e e NFE"
    result = extract_acronyms_from_query(query)

    assert "NFS-E" in result, f"NFS-E não encontrado em {result}"
    assert "NFE" in result, f"NFE não encontrado em {result}"
    print(f"✓ Múltiplas siglas: {result}")


def test_extract_no_acronyms():
    """Testa query sem siglas."""
    query = "onde fica a prefeitura"
    result = extract_acronyms_from_query(query)

    assert result == [], f"Esperado [], obtido {result}"
    print("✓ Query sem siglas retorna lista vazia")


def test_extract_partial_match():
    """Testa que não pega match parcial (ex: ME não deve casar com COMO)."""
    query = "como fazer"
    result = extract_acronyms_from_query(query)

    # "ME" é uma sigla, mas não deve ser extraída de "como"
    assert "ME" not in result, f"'ME' não deve ser extraído de 'como', obtido {result}"
    print("✓ Não extrai match parcial")


def test_boost_with_acronym_match():
    """Testa que boost é aplicado quando há match de sigla."""
    query_acronyms = ["REFIS"]
    chunk_text = "O Programa REFIS 2025 foi prorrogado"

    boost = get_acronym_boost(query_acronyms, chunk_text)

    assert boost == ACRONYM_BOOST_VALUE, (
        f"Esperado {ACRONYM_BOOST_VALUE}, obtido {boost}"
    )
    print(f"✓ Boost aplicado: {boost}")


def test_boost_no_match():
    """Testa que não há boost quando não há match."""
    query_acronyms = ["REFIS"]
    chunk_text = "O gabinete do prefeito é responsável"

    boost = get_acronym_boost(query_acronyms, chunk_text)

    assert boost == 0.0, f"Esperado 0.0, obtido {boost}"
    print("✓ Sem boost quando não há match")


def test_boost_empty_acronyms():
    """Testa que não há boost quando não há siglas na query."""
    query_acronyms = []
    chunk_text = "Qualquer texto"

    boost = get_acronym_boost(query_acronyms, chunk_text)

    assert boost == 0.0, f"Esperado 0.0, obtido {boost}"
    print("✓ Sem boost quando query não tem siglas")


def test_boost_case_insensitive():
    """Testa que o boost é case-insensitive."""
    query_acronyms = ["REFIS"]

    test_cases = [
        "O refis foi prorrogado",
        "O REFIS foi prorrogado",
        "O Refis foi prorrogado",
    ]

    for chunk_text in test_cases:
        boost = get_acronym_boost(query_acronyms, chunk_text)
        assert boost == ACRONYM_BOOST_VALUE, f"Falhou para '{chunk_text}'"

    print("✓ Boost case-insensitive")


def test_get_meaning():
    """Testa obtenção de significado."""
    meaning = get_acronym_meaning("REFIS")
    assert "Recuperação Fiscal" in meaning, f"Significado incorreto: {meaning}"

    meaning = get_acronym_meaning("IPTU")
    assert "Imposto Predial" in meaning, f"Significado incorreto: {meaning}"

    print("✓ Significados corretos")


def test_get_meaning_not_found():
    """Testa sigla não encontrada."""
    meaning = get_acronym_meaning("XYZ999")
    assert meaning == "", f"Esperado string vazia, obtido {meaning}"
    print("✓ Retorna vazio para sigla desconhecida")


def test_list_all_acronyms():
    """Testa listagem de todas as siglas."""
    all_acr = list_all_acronyms()

    assert len(all_acr) > 0, "Lista de siglas está vazia"
    assert "REFIS" in all_acr, "REFIS não encontrado"
    assert "IPTU" in all_acr, "IPTU não encontrado"

    print(f"✓ Total de siglas: {len(all_acr)}")


def test_integration_retriever_simulation():
    """
    Simula o comportamento do retriever com boost de siglas.
    Verifica se o chunk correto seria priorizado.
    """
    query = "REFIS 2025"
    query_acronyms = extract_acronyms_from_query(query)

    # Simula chunks que seriam retornados
    chunks = [
        {
            "id": "0003_chunk_001",
            "text": "## Gabinete do Prefeito\n\n**Prefeito Municipal**: Amarildo Rigolin...",
            "score": 0.257,
        },
        {
            "id": "0006_chunk_004",
            "text": "## REFIS 2025 - Programa de Recuperação Fiscal\n\nO Programa de Recuperação Fiscal (REFIS 2025)...",
            "score": 0.246,
        },
    ]

    # Aplica boost
    for chunk in chunks:
        boost = get_acronym_boost(query_acronyms, chunk["text"])
        chunk["boosted_score"] = min(1.0, chunk["score"] + boost)

    # Ordena por score boosted
    chunks.sort(key=lambda c: c["boosted_score"], reverse=True)

    # Verifica se o chunk do REFIS ficou em primeiro
    assert chunks[0]["id"] == "0006_chunk_004", (
        f"Chunk do REFIS deveria estar em primeiro. Ordem: {[c['id'] for c in chunks]}"
    )

    print("✓ Integração simulada:")
    print(
        f"  - Chunk REFIS: score {chunks[0]['score']:.3f} -> {chunks[0]['boosted_score']:.3f}"
    )
    print(
        f"  - Chunk Gabinete: score {chunks[1]['score']:.3f} -> {chunks[1]['boosted_score']:.3f}"
    )


def test_real_refis_scenario():
    """
    Testa o cenário real do REFIS mencionado pelo usuário.
    """
    query = "REFIS 2025"
    query_acronyms = extract_acronyms_from_query(query)

    assert query_acronyms == ["REFIS"], f"Esperado ['REFIS'], obtido {query_acronyms}"

    # Texto do chunk 0006_chunk_004
    refis_chunk = """## REFIS 2025 - Programa de Recuperação Fiscal
O Programa de Recuperação Fiscal (REFIS 2025) foi prorrogado até 27 de fevereiro de 2025."""

    # Texto de outro chunk
    other_chunk = "O Gabinete do Prefeito é responsável pela coordenação geral"

    boost_refis = get_acronym_boost(query_acronyms, refis_chunk)
    boost_other = get_acronym_boost(query_acronyms, other_chunk)

    assert boost_refis == ACRONYM_BOOST_VALUE, "REFIS deveria ter boost"
    assert boost_other == 0.0, "Outro chunk não deveria ter boost"

    print("✓ Cenário real do REFIS funciona corretamente")


def run_all_tests():
    """Executa todos os testes."""
    print("=" * 60)
    print("TESTES DO MÓDULO DE SIGLAS (ACRONYMS)")
    print("=" * 60)

    tests = [
        test_extract_acronyms_basic,
        test_extract_acronyms_case_insensitive,
        test_extract_multiple_acronyms,
        test_extract_no_acronyms,
        test_extract_partial_match,
        test_boost_with_acronym_match,
        test_boost_no_match,
        test_boost_empty_acronyms,
        test_boost_case_insensitive,
        test_get_meaning,
        test_get_meaning_not_found,
        test_list_all_acronyms,
        test_integration_retriever_simulation,
        test_real_refis_scenario,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FALHOU: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERRO: {e}")
            failed += 1

    print("=" * 60)
    print(f"RESULTADO: {passed} passaram, {failed} falharam")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
