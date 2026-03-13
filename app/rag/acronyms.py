"""
Acronyms and Siglas - Mapeamento de siglas para boost no RAG

Este arquivo contém siglas e acrônimos relevantes para o contexto municipal
de {client_name}, organizados por categoria.

Uso:
    from app.rag.acronyms import get_acronym_boost, extract_acronyms_from_query

    # Extrair siglas de uma query
    acronyms = extract_acronyms_from_query("quero saber sobre o REFIS 2025")
    # Resultado: ["REFIS"]

    # Verificar boost para um chunk
    boost = get_acronym_boost(query_acronyms, chunk_text)
    # Resultado: 0.2 se o chunk contiver "REFIS"

Regras:
    - Busca case-insensitive (REFIS = refis = Refis)
    - Boost de +0.2 quando há match exato da sigla no texto
    - Apenas siglas presentes na query geram boost
"""

from typing import Dict, List, Set

# =============================================================================
# SIGLAS POR CATEGORIA
# =============================================================================

SIGLAS_TRIBUTOS_FINANCAS: Dict[str, str] = {
    "REFIS": "Programa de Recuperação Fiscal",
    "IPTU": "Imposto Predial e Territorial Urbano",
    "ITBI": "Imposto sobre Transmissão de Bens Imóveis",
    "ISS": "Imposto Sobre Serviços",
    "ICMS": "Imposto sobre Circulação de Mercadorias e Serviços",
    "NFS-E": "Nota Fiscal de Serviço Eletrônica",
    "NFS": "Nota Fiscal de Serviço",
    "NF-E": "Nota Fiscal Eletrônica",
    "NFE": "Nota Fiscal Eletrônica",
    "DAS": "Documento de Arrecadação do Simples Nacional",
    "DASN": "Declaração Anual do Simples Nacional",
    "DASN-SIMEI": "Declaração Anual do Simples Nacional para MEI",
    "CCMEI": "Certificado de Condição de Microempreendedor Individual",
    "PGMEI": "Programa de Gestão do MEI",
    "MEI": "Microempreendedor Individual",
    "CNPJ": "Cadastro Nacional da Pessoa Jurídica",
    "CPF": "Cadastro de Pessoas Físicas",
}

SIGLAS_EMPREENDEDORISMO: Dict[str, str] = {
    "ME": "Microempresa",
    "EPP": "Empresa de Pequeno Porte",
    "SEBRAE": "Serviço Brasileiro de Apoio às Micro e Pequenas Empresas",
    "JUCEPAR": "Junta Comercial do Paraná",
}

SIGLAS_SAUDE: Dict[str, str] = {
    "SUS": "Sistema Único de Saúde",
    "PSF": "Programa de Saúde da Família",
    "UBS": "Unidade Básica de Saúde",
    "UBSF": "Unidade Básica de Saúde da Família",
    "PA": "Pronto Atendimento",
    "NASF": "Núcleo de Apoio à Saúde da Família",
    "CEO": "Centro de Especialidades Odontológicas",
    "CAPS": "Centro de Atenção Psicossocial",
    "SAMU": "Serviço de Atendimento Móvel de Urgência",
}

SIGLAS_ASSISTENCIA_SOCIAL: Dict[str, str] = {
    "CRAS": "Centro de Referência de Assistência Social",
    "CADUNICO": "Cadastro Único para Programas Sociais",
    "CADÚNICO": "Cadastro Único para Programas Sociais",
    "BPC": "Benefício de Prestação Continuada",
    "LOAS": "Lei Orgânica da Assistência Social",
    "BPC/LOAS": "Benefício de Prestação Continuada",
    "INSS": "Instituto Nacional do Seguro Social",
}

SIGLAS_EDUCACAO: Dict[str, str] = {
    "CMEI": "Centro Municipal de Educação Infantil",
    "CEI": "Centro de Educação Infantil",
    "NEE": "Necessidades Educacionais Especiais",
}

SIGLAS_TRANSITO: Dict[str, str] = {
    "DETRAN": "Departamento Estadual de Trânsito",
    "CIRETRAN": "Circunscrição Regional de Trânsito",
    "CONTRAN": "Conselho Nacional de Trânsito",
    "JARI": "Junta Administrativa de Recursos de Infrações",
}

SIGLAS_INFRAESTRUTURA: Dict[str, str] = {
    "COSIP": "Contribuição para Custeio do Serviço de Iluminação Pública",
    "COPEL": "Companhia Paranaense de Energia",
}

SIGLAS_PLANEJAMENTO: Dict[str, str] = {
    "PPA": "Plano Plurianual",
    "LOA": "Lei Orçamentária Anual",
    "LDO": "Lei de Diretrizes Orçamentárias",
}

SIGLAS_EMERGENCIA: Dict[str, str] = {
    "PM": "Polícia Militar",
    "BM": "Bombeiros Militares",
}

# =============================================================================
# TODAS AS SIGLAS CONSOLIDADAS
# =============================================================================

ALL_ACRONYMS: Dict[str, str] = {
    **SIGLAS_TRIBUTOS_FINANCAS,
    **SIGLAS_EMPREENDEDORISMO,
    **SIGLAS_SAUDE,
    **SIGLAS_ASSISTENCIA_SOCIAL,
    **SIGLAS_EDUCACAO,
    **SIGLAS_TRANSITO,
    **SIGLAS_INFRAESTRUTURA,
    **SIGLAS_PLANEJAMENTO,
    **SIGLAS_EMERGENCIA,
}

# Conjunto de siglas para busca rápida (case-insensitive)
ALL_ACRONYM_KEYS: Set[str] = set(ALL_ACRONYMS.keys())
ALL_ACRONYM_KEYS_LOWER: Set[str] = set(k.lower() for k in ALL_ACRONYMS.keys())


# =============================================================================
# CONFIGURAÇÃO DE BOOST
# =============================================================================

# Boost aplicado quando há match de sigla (0.0 a 1.0)
ACRONYM_BOOST_VALUE = 0.2


def extract_acronyms_from_query(query: str) -> List[str]:
    """
    Extrai siglas presentes na query do usuário.

    Args:
        query: Texto da query do usuário

    Returns:
        Lista de siglas encontradas (em maiúsculas)

    Example:
        >>> extract_acronyms_from_query("quero saber sobre o REFIS 2025")
        ["REFIS"]

        >>> extract_acronyms_from_query("como emitir NFS-e ou NFE")
        ["NFS-E", "NFE"]
    """
    query_upper = query.upper()
    found_acronyms = []

    for acronym in ALL_ACRONYM_KEYS:
        # Verifica se a sigla aparece como palavra completa
        # ou no início/fim do texto
        acronym_upper = acronym.upper()

        # Procura a sigla no texto (case-insensitive)
        if acronym_upper in query_upper:
            # Verifica se é uma ocorrência válida (palavra completa)
            # Evita match parcial (ex: "ME" não deve casar com "COMO")
            idx = query_upper.find(acronym_upper)
            if idx != -1:
                # Verifica se é palavra completa
                before = idx == 0 or not query_upper[idx - 1].isalnum()
                after = (
                    idx + len(acronym_upper) >= len(query_upper)
                    or not query_upper[idx + len(acronym_upper)].isalnum()
                )

                if before and after:
                    found_acronyms.append(acronym_upper)

    # Remove duplicatas mantendo ordem
    seen = set()
    unique_acronyms = []
    for acr in found_acronyms:
        if acr not in seen:
            seen.add(acr)
            unique_acronyms.append(acr)

    return unique_acronyms


def get_acronym_boost(query_acronyms: List[str], chunk_text: str) -> float:
    """
    Calcula o boost de score baseado em match de siglas.

    Args:
        query_acronyms: Lista de siglas extraídas da query
        chunk_text: Texto do chunk a ser avaliado

    Returns:
        Valor de boost (0.0 ou ACRONYM_BOOST_VALUE)

    Note:
        - Retorna o boost se pelo menos uma sigla da query estiver no chunk
        - Busca case-insensitive
        - Não acumula boosts (máximo uma vez por chunk)
    """
    if not query_acronyms:
        return 0.0

    chunk_upper = chunk_text.upper()

    for acronym in query_acronyms:
        # Verifica se a sigla aparece no texto do chunk
        if acronym in chunk_upper:
            # Verifica se é ocorrência válida (palavra completa)
            idx = chunk_upper.find(acronym)
            while idx != -1:
                before = idx == 0 or not chunk_upper[idx - 1].isalnum()
                after = (
                    idx + len(acronym) >= len(chunk_upper)
                    or not chunk_upper[idx + len(acronym)].isalnum()
                )

                if before and after:
                    return ACRONYM_BOOST_VALUE

                # Procura próxima ocorrência
                idx = chunk_upper.find(acronym, idx + 1)

    return 0.0


def get_acronym_meaning(acronym: str) -> str:
    """
    Retorna o significado de uma sigla.

    Args:
        acronym: Sigla (case-insensitive)

    Returns:
        Significado da sigla ou string vazia se não encontrada
    """
    return ALL_ACRONYMS.get(acronym.upper(), "")


def list_all_acronyms() -> Dict[str, str]:
    """
    Retorna dicionário com todas as siglas e seus significados.

    Returns:
        Dict[str, str]: Mapeamento sigla -> significado
    """
    return ALL_ACRONYMS.copy()


def expand_query_with_acronyms(query: str) -> str:
    """
    Expande siglas na query adicionando seus significados.

    Isso melhora a busca semântica porque o embedding pode encontrar
    documentos que usam o nome completo em vez da sigla.

    Args:
        query: Query original do usuário

    Returns:
        Query expandida com significados das siglas

    Example:
        >>> expand_query_with_acronyms("quero aderir ao REFIS 2025")
        "quero aderir ao REFIS 2025 Programa de Recuperação Fiscal"

        >>> expand_query_with_acronyms("onde fica o PSF central")
        "onde fica o PSF central Programa de Saúde da Família"
    """
    acronyms = extract_acronyms_from_query(query)
    if not acronyms:
        return query

    expansions = []
    for acronym in acronyms:
        meaning = get_acronym_meaning(acronym)
        if meaning:
            expansions.append(meaning)

    if expansions:
        return f"{query} {' '.join(expansions)}"

    return query


# =============================================================================
# FUNÇÕES AUXILIARES PARA DEBUG
# =============================================================================


def debug_acronym_extraction(query: str) -> None:
    """
    Função de debug para verificar extração de siglas.

    Args:
        query: Query de teste
    """
    print(f"Query: '{query}'")
    print(f"Siglas encontradas: {extract_acronyms_from_query(query)}")
    print()


def debug_acronym_boost(query: str, chunk_text: str) -> None:
    """
    Função de debug para verificar cálculo de boost.

    Args:
        query: Query do usuário
        chunk_text: Texto do chunk
    """
    acronyms = extract_acronyms_from_query(query)
    boost = get_acronym_boost(acronyms, chunk_text)

    print(f"Query: '{query}'")
    print(f"Siglas na query: {acronyms}")
    print(f"Boost calculado: {boost}")
    print()


if __name__ == "__main__":
    # Testes de exemplo
    print("=" * 60)
    print("TESTES DE EXTRAÇÃO DE SIGLAS")
    print("=" * 60)

    test_queries = [
        "quero saber sobre o REFIS 2025",
        "como emitir NFS-e ou NFE",
        "onde fica o PSF central",
        "preciso do BPC LOAS",
        "como funciona o MEI e CNPJ",
        "quero pagar o DAS do MEI",
        "nada de siglas aqui",
    ]

    for query in test_queries:
        debug_acronym_extraction(query)

    print("=" * 60)
    print("TESTES DE BOOST")
    print("=" * 60)

    test_boosts = [
        ("REFIS 2025", "O Programa de Recuperação Fiscal (REFIS 2025) foi prorrogado"),
        ("REFIS 2025", "O gabinete do prefeito é responsável"),
        ("MEI", "O Microempreendedor Individual (MEI) é uma categoria"),
        ("NFS-e", "A emissão é feita via sistema web"),
    ]

    for query, chunk in test_boosts:
        debug_acronym_boost(query, chunk)
