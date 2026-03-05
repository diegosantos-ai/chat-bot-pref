"""
Dicionário de Sinônimos - Vocabulário Popular vs Técnico

Mapeia termos técnicos/formais para equivalentes populares e vice-versa.
Permite que a TerezIA entenda tanto o empresário quanto a dona de casa.

Estrutura:
- Chave: termo canônico (usado na base de conhecimento)
- Valor: lista de sinônimos populares/alternativos
"""

# =============================================================================
# SAÚDE
# =============================================================================
SAUDE_SYNONYMS = {
    # Unidades de saúde
    "PSF": [
        "postinho",
        "postinho de saúde",
        "posto de saúde",
        "posto",
        "UBS",
        "unidade de saúde",
        "unidade básica",
        "centro de saúde",
        "posto médico",
        "ambulatório",
        "policlínica",
    ],
    "pronto atendimento": [
        "pronto socorro",
        "PS",
        "PA",
        "emergência",
        "urgência",
        "hospital",
        "UPA",
        "plantão médico",
        "atendimento 24 horas",
        "socorro",
        "emergencia",
        "urgencia",
    ],
    "SAMU": [
        "ambulância",
        "ambulancia",
        "resgate",
        "192",
        "socorro móvel",
    ],
    # Profissionais
    "médico": [
        "doutor",
        "doutora",
        "dr",
        "dra",
        "dotô",
        "doto",
        "medico",
        "clínico",
        "clinico",
    ],
    "enfermeiro": [
        "enfermeira",
        "enfermeir",
        "técnico de enfermagem",
        "técnica de enfermagem",
        "auxiliar de enfermagem",
    ],
    # Procedimentos
    "vacina": [
        "vacinação",
        "vacinacao",
        "imunização",
        "imunizacao",
        "dose",
        "picada",
        "injeção",
        "injecao",
    ],
    "exame": [
        "teste",
        "análise",
        "analise",
        "check-up",
        "checkup",
        "coleta",
        "sangue",
        "laboratorio",
        "laboratório",
    ],
    "papanicolau": [
        "preventivo",
        "exame preventivo",
        "papa nicolau",
        "exame da mulher",
        "citologia",
    ],
    "pré-natal": [
        "prenatal",
        "pre natal",
        "pré natal",
        "acompanhamento gestante",
        "consulta grávida",
        "consulta gravida",
        "acompanhamento gravidez",
    ],
}

# =============================================================================
# CONTATOS / COMUNICAÇÃO
# =============================================================================
CONTATO_SYNONYMS = {
    "telefone": [
        "número",
        "numero",
        "fone",
        "ligar",
        "contato telefônico",
        "discar",
        "tel",
        "celular",
        "ramal",
    ],
    "e-mail": [
        "email",
        "correio eletrônico",
        "endereço eletrônico",
        "mandar mensagem",
        "enviar mensagem",
    ],
    "endereço": [
        "endereco",
        "localização",
        "localizacao",
        "onde fica",
        "como chegar",
        "rua",
        "avenida",
        "número do prédio",
    ],
}

# =============================================================================
# DOCUMENTOS
# =============================================================================
DOCUMENTOS_SYNONYMS = {
    "RG": [
        "identidade",
        "carteira de identidade",
        "documento",
        "CI",
        "registro geral",
        "carteirinha",
    ],
    "CPF": [
        "cadastro pessoa física",
        "numero do CPF",
        "documento fiscal",
    ],
    "certidão de nascimento": [
        "certidao nascimento",
        "registro de nascimento",
        "documento de nascimento",
        "papel de nascido",
    ],
    "certidão de casamento": [
        "certidao casamento",
        "registro de casamento",
        "documento de casado",
        "papel de casado",
    ],
    "certidão de óbito": [
        "certidao obito",
        "atestado de óbito",
        "atestado obito",
        "documento de falecimento",
        "papel de morte",
    ],
    "segunda via": [
        "2a via",
        "2ª via",
        "cópia",
        "copia",
        "duplicata",
        "outro documento",
        "tirar de novo",
        "fazer outro",
    ],
    "certidão negativa": [
        "certidao negativa",
        "nada consta",
        "certidão de débitos",
        "certidao debitos",
        "comprovante sem dívida",
    ],
    "CNH": [
        "carteira de motorista",
        "habilitação",
        "carta de motorista",
        "carteira de habilitação",
        "carta",
        "cnh",
    ],
    "comprovante de residência": [
        "conta de luz",
        "conta de água",
        "conta telefone",
        "comprovante endereço",
        "prova de residência",
        "conta copel",
        "conta sanepar",
    ],
}

# =============================================================================
# TRIBUTÁRIO / FINANCEIRO
# =============================================================================
TRIBUTARIO_SYNONYMS = {
    "IPTU": [
        "imposto da casa",
        "imposto do terreno",
        "imposto predial",
        "carnê da casa",
        "carne da casa",
        "taxa da casa",
        "imposto territorial",
        "tributo imóvel",
    ],
    "ISS": [
        "imposto de serviço",
        "imposto sobre serviço",
        "taxa de serviço",
        "tributo serviço",
    ],
    "alvará": [
        "licença",
        "licenca",
        "autorização",
        "autorizacao",
        "permissão",
        "permissao",
        "liberação",
        "liberacao",
        "papel pra abrir empresa",
        "documento da firma",
    ],
    "nota fiscal": [
        "NF",
        "NFe",
        "nota",
        "cupom fiscal",
        "recibo",
        "comprovante de pagamento",
    ],
    "boleto": [
        "carnê",
        "carne",
        "guia de pagamento",
        "conta",
        "fatura",
        "cobrança",
        "cobranca",
    ],
    "parcelamento": [
        "dividir",
        "parcela",
        "pagar em vezes",
        "negociar dívida",
        "negociar divida",
        "acordo",
    ],
}

# =============================================================================
# EDUCAÇÃO
# =============================================================================
EDUCACAO_SYNONYMS = {
    "CMEI": [
        "creche",
        "escolinha",
        "maternal",
        "berçário",
        "bercario",
        "educação infantil",
        "educacao infantil",
        "pré-escola",
        "pre escola",
        "pré",
        "pre",
        "cmei",
        "cemei",
        "cmeis",
        "cemeis",
    ],
    "escola municipal": [
        "escola",
        "colégio",
        "colegio",
        "ensino fundamental",
        "escola pública",
        "escola publica",
    ],
    "matrícula": [
        "matricula",
        "matriculo",
        "matricular",
        "inscrição",
        "inscricao",
        "vaga",
        "vagas",
        "cadastro escolar",
        "registrar na escola",
    ],
    "transporte escolar": [
        "ônibus escolar",
        "onibus escolar",
        "van escolar",
        "condução escolar",
        "conducao escolar",
        "busão da escola",
    ],
    "merenda": [
        "merenda escolar",
        "alimentação escolar",
        "alimentacao escolar",
        "comida da escola",
        "lanche da escola",
    ],
}

# =============================================================================
# ASSISTÊNCIA SOCIAL
# =============================================================================
SOCIAL_SYNONYMS = {
    "CRAS": [
        "assistência social",
        "assistencia social",
        "social",
        "centro de referência",
        "ajuda social",
        "amparo social",
    ],
    "Bolsa Família": [
        "bolsa familia",
        "BF",
        "auxílio",
        "auxilio",
        "benefício",
        "beneficio",
        "ajuda do governo",
    ],
    "BPC": [
        "benefício de prestação continuada",
        "loas",
        "benefício idoso",
        "benefício deficiente",
        "salário do idoso",
        "aposentadoria especial",
    ],
    "CadÚnico": [
        "cadunico",
        "cad unico",
        "cadastro único",
        "cadastro unico",
        "cadastro social",
        "cadastro governo",
    ],
}

# =============================================================================
# INFRAESTRUTURA / SERVIÇOS
# =============================================================================
INFRAESTRUTURA_SYNONYMS = {
    "iluminação pública": [
        "iluminacao publica",
        "luz da rua",
        "poste",
        "lâmpada",
        "lampada",
        "luz queimada",
        "poste apagado",
    ],
    "coleta de lixo": [
        "lixo",
        "lixeiro",
        "caminhão de lixo",
        "caminhao lixo",
        "recolhimento",
        "entulho",
    ],
    "buraco": [
        "bueiro",
        "cratera",
        "rua esburacada",
        "asfalto ruim",
        "pista ruim",
        "pavimentação",
        "pavimentacao",
    ],
    "pavimentação": [
        "pavimentacao",
        "asfalto",
        "asfalto novo",
        "obra de asfalto",
        "obras de asfalto",
        "pavimento",
    ],
    "água": [
        "agua",
        "saneamento",
        "esgoto",
        "falta de água",
        "vazamento",
        "cano estourado",
    ],
    "poda de árvore": [
        "poda arvore",
        "corte de árvore",
        "galho",
        "árvore",
        "arvore",
        "mato",
        "vegetação",
        "vegetacao",
    ],
}

# =============================================================================
# LOCALIZAÇÃO / ESTRUTURAS
# =============================================================================
LOCALIZACAO_SYNONYMS = {
    "prefeitura": [
        "paço municipal",
        "prédio da prefeitura",
        "sede",
        "gabinete do prefeito",
        "administração municipal",
        "administracao municipal",
        "orgao publico",
    ],
    "câmara": [
        "camara",
        "câmara de vereadores",
        "camara vereadores",
        "legislativo",
        "casa das leis",
    ],
    "secretaria": [
        "setor",
        "departamento",
        "repartição",
        "reparticao",
        "órgão",
        "orgao",
    ],
}

# =============================================================================
# HORÁRIOS / ATENDIMENTO
# =============================================================================
SERVICOS_DIGITAIS_SYNONYMS = {
    "site da prefeitura": [
        "portal",
        "website",
        "pagina da internet",
        "online",
        "pela internet",
        "no computador",
        "na web",
    ],
    "agendamento": [
        "marcar hora",
        "agendar",
        "consulta marcada",
        "hora marcada",
        "vaga",
        "marcação",
        "marcacao",
    ],
    "protocolo online": [
        "protocolar",
        "solicitar online",
        "pedido online",
        "requerimento online",
        "reclamação online",
    ],
}

EMERGENCIA_SEGURANCA_SYNONYMS = {
    "defesa civil": [
        "emergencia",
        "desastre",
        "enchente",
        "temporal",
        "deslizamento",
        "alagamento",
        "chuva forte",
        "vendaval",
    ],
    "guarda municipal": [
        "guarda",
        "segurança",
        "policia municipal",
        "patrulha",
        "ronda",
        "agente municipal",
    ],
}

HORARIO_SYNONYMS = {
    "horário de funcionamento": [
        # Termos para melhorar busca vetorial (mais específicos primeiro)
        "atendimento geral",
        "segunda sexta",
        "8h 17h",
        # Variações comuns
        "expediente",
        "que horas abre",
        "que horas fecha",
    ],
    "atendimento ao público": [
        "atendimento publico",
        "atendimento cidadão",
        "atendimento cidadao",
        "horário atendimento",
        "recebe público",
    ],
    "plantão": [
        "24 horas",
        "final de semana",
        "sábado",
        "domingo",
        "feriado",
        "pronto atendimento",
    ],
}

# =============================================================================
# CONSOLIDAÇÃO
# =============================================================================
SYNONYMS = {
    **SAUDE_SYNONYMS,
    **DOCUMENTOS_SYNONYMS,
    **TRIBUTARIO_SYNONYMS,
    **EDUCACAO_SYNONYMS,
    **SOCIAL_SYNONYMS,
    **INFRAESTRUTURA_SYNONYMS,
    **LOCALIZACAO_SYNONYMS,
    **HORARIO_SYNONYMS,
    **CONTATO_SYNONYMS,
    **SERVICOS_DIGITAIS_SYNONYMS,
    **EMERGENCIA_SEGURANCA_SYNONYMS,
}

# Índice reverso: de sinônimo para termo canônico
_REVERSE_INDEX: dict[str, str] = {}
for canonical, synonyms in SYNONYMS.items():
    for syn in synonyms:
        _REVERSE_INDEX[syn.lower()] = canonical


def get_canonical(term: str) -> str | None:
    """
    Retorna o termo canônico para um sinônimo.

    Args:
        term: Termo a buscar

    Returns:
        Termo canônico ou None se não encontrado

    Example:
        >>> get_canonical("postinho")
        "PSF"
    """
    return _REVERSE_INDEX.get(term.lower())


def expand_terms(term: str) -> list[str]:
    """
    Expande um termo para incluir seus sinônimos.

    Args:
        term: Termo a expandir

    Returns:
        Lista com o termo original + sinônimos

    Example:
        >>> expand_terms("PSF")
        ["PSF", "postinho", "posto de saúde", "UBS", ...]
    """
    term_lower = term.lower()

    # Se é termo canônico, retorna ele + sinônimos
    if term in SYNONYMS:
        return [term] + SYNONYMS[term]

    # Se é sinônimo, encontra canônico e expande
    canonical = get_canonical(term)
    if canonical:
        return [term, canonical] + [
            s for s in SYNONYMS[canonical] if s.lower() != term_lower
        ]

    # Não encontrou, retorna só o termo
    return [term]


def _word_in_text(word: str, text: str) -> bool:
    """
    Verifica se uma palavra/frase está no texto como palavra completa.
    Usa word boundaries para evitar falsos positivos.
    """
    import re

    # Escapa caracteres especiais de regex
    pattern = r"\b" + re.escape(word.lower()) + r"\b"
    return bool(re.search(pattern, text.lower()))


def find_related_terms(text: str) -> dict[str, list[str]]:
    """
    Encontra todos os termos relacionados em um texto.

    Args:
        text: Texto a analisar

    Returns:
        Dicionário {termo_encontrado: [sinônimos]}

    Example:
        >>> find_related_terms("quero ir no postinho fazer vacina")
        {"postinho": ["PSF", "UBS", ...], "vacina": ["vacinação", ...]}
    """
    found = {}

    # Busca termos canônicos (word boundary match)
    for canonical, synonyms in SYNONYMS.items():
        if _word_in_text(canonical, text):
            found[canonical] = synonyms
            continue

        # Busca sinônimos
        for syn in synonyms:
            if _word_in_text(syn, text):
                found[syn] = [canonical] + [s for s in synonyms if s != syn]
                break

    return found
