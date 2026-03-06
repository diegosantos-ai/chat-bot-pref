"""
Normalizador de Texto - Adapta linguagem para diferentes perfis

Funções:
- Normalização de acentos e caracteres especiais
- Detecção de nível de formalidade
- Expansão de abreviações comuns
- Correção de erros ortográficos frequentes
"""

import re
import unicodedata
from enum import Enum


class FormalityLevel(str, Enum):
    """Nível de formalidade detectado na mensagem."""
    FORMAL = "formal"           # Empresário, advogado
    NEUTRAL = "neutral"         # Padrão
    INFORMAL = "informal"       # Popular, coloquial
    VERY_INFORMAL = "very_informal"  # Gírias pesadas, erros


# =============================================================================
# ABREVIAÇÕES COMUNS
# =============================================================================
ABBREVIATIONS = {
    # Internet/SMS
    "vc": "você",
    "vcs": "vocês",
    "tb": "também",
    "tbm": "também",
    "pq": "porque",
    "pra": "para",
    "pro": "para o",
    "pros": "para os",
    "ta": "está",
    "to": "estou",
    "tô": "estou",
    "né": "não é",
    "q": "que",
    "oq": "o que",
    "qd": "quando",
    "qdo": "quando",
    "qto": "quanto",
    "cmg": "comigo",
    "ctg": "contigo",
    "msg": "mensagem",
    "obg": "obrigado",
    "vlw": "valeu",
    "blz": "beleza",
    "pfv": "por favor",
    "pfvr": "por favor",
    "pls": "por favor",
    "hj": "hoje",
    "agr": "agora",
    "dps": "depois",
    "msm": "mesmo",
    "mto": "muito",
    "mt": "muito",
    "nd": "nada",
    "ngm": "ninguém",
    "alg": "alguém",
    "algm": "alguém",
    "td": "tudo",
    "tds": "todos",
    "bjs": "beijos",
    "abs": "abraços",
    "att": "atenciosamente",
    "ñ": "não",
    "n": "não",
    "s": "sim",
    "c": "com",
    "d": "de",
    "p": "para",
    
    # Locais
    "pref": "prefeitura",
    "sec": "secretaria",
    "hosp": "hospital",
    
    # Documentos
    "doc": "documento",
    "docs": "documentos",
    "cert": "certidão",
}

# =============================================================================
# ERROS ORTOGRÁFICOS COMUNS
# =============================================================================
COMMON_TYPOS = {
    # Acentuação
    "agua": "água",
    "saude": "saúde",
    "servico": "serviço",
    "horario": "horário",
    "telefono": "telefone",
    "numero": "número",
    "endereco": "endereço",
    "informacao": "informação",
    "atencao": "atenção",
    "educacao": "educação",
    "vacinacao": "vacinação",
    "certidao": "certidão",
    "orgao": "órgão",
    "onibus": "ônibus",
    "lampada": "lâmpada",
    
    # Trocas comuns
    "porisso": "por isso",
    "derrepente": "de repente",
    "agente": "a gente",
    "concerteza": "com certeza",
    "mim fazer": "eu fazer",
    "mim ir": "eu ir",
    "pra mim fazer": "para eu fazer",
    "fazê": "fazer",
    "podê": "poder",
    "sabê": "saber",
    "vê": "ver",
    "i": "ir",
    "vo": "vou",
    "tá": "está",
    
    # Regionalismos PR
    "piá": "menino",
    "guria": "menina",
    "tri": "muito",
    "barbaridade": "nossa",
}

# =============================================================================
# INDICADORES DE FORMALIDADE
# =============================================================================
FORMAL_INDICATORS = [
    r"\b(prezad[oa]s?|senhor[a]?|ilustríssim[oa])\b",
    r"\b(solicito|requeiro|venho por meio|encaminho)\b",
    r"\b(atenciosamente|cordialmente|respeitosamente)\b",
    r"\b(conforme|mediante|referente|supracitad[oa])\b",
    r"\b(outrossim|destarte|mormente|porquanto)\b",
    r"\b(vossa senhoria|v\.sa\.|excelentíssim[oa])\b",
]

INFORMAL_INDICATORS = [
    r"\b(oi|opa|eai|eae|fala|salve)\b",
    r"\b(blz|vlw|flw|tmj|mano|cara|véi|vei)\b",
    r"\b(show|top|massa|dahora|da hora|legal)\b",
    r"\b(tipo assim|sei lá|sei la|tá ligado|sabe)\b",
    r"(kkk+|haha+|rsrs+|aeee+|uhuuu+)",
    r"(!{2,}|\?{2,}|\.{3,})",
]

VERY_INFORMAL_INDICATORS = [
    r"\b(mano|véi|vei|bicho|brother|bro|parça)\b",
    r"\b(pô|putz|caramba|eita|oxe|uai)\b",
    r"(kkk{3,}|haha{3,})",
    r"[^aeiouAEIOU]{5,}",  # Muitas consoantes (ex: "blz", "vlw")
]


def remove_accents(text: str) -> str:
    """Remove acentos de um texto (para comparação)."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def expand_abbreviations(text: str) -> str:
    """
    Expande abreviações comuns.
    
    Args:
        text: Texto com abreviações
        
    Returns:
        Texto com abreviações expandidas
        
    Example:
        >>> expand_abbreviations("vc pode me ajudar?")
        "você pode me ajudar?"
    """
    words = text.split()
    expanded = []
    
    for word in words:
        word_lower = word.lower()
        # Remove pontuação para comparar
        word_clean = re.sub(r'[^\w]', '', word_lower)
        
        # Só expande se for uma abreviação conhecida
        # E apenas letras (não números ou muito curto)
        if word_clean in ABBREVIATIONS and len(word_clean) >= 2:
            # Preserva pontuação original
            punct_after = re.search(r'[^\w]+$', word)
            replacement = ABBREVIATIONS[word_clean]
            if punct_after:
                replacement += punct_after.group()
            expanded.append(replacement)
        else:
            expanded.append(word)
    
    return ' '.join(expanded)


def fix_common_typos(text: str) -> str:
    """
    Corrige erros ortográficos comuns.
    
    Args:
        text: Texto com possíveis erros
        
    Returns:
        Texto corrigido
    """
    result = text
    
    for typo, correction in COMMON_TYPOS.items():
        # Só replace palavras completas (não substrings)
        # \b garante word boundary
        pattern = re.compile(r'\b' + re.escape(typo) + r'\b', re.IGNORECASE)
        result = pattern.sub(correction, result)
    
    return result


def detect_formality_level(text: str) -> FormalityLevel:
    """
    Detecta o nível de formalidade de uma mensagem.
    
    Args:
        text: Texto a analisar
        
    Returns:
        FormalityLevel indicando o nível detectado
        
    Example:
        >>> detect_formality_level("Prezado senhor, solicito informações")
        FormalityLevel.FORMAL
        >>> detect_formality_level("eae blz? qro saber do postinho")
        FormalityLevel.VERY_INFORMAL
    """
    text_lower = text.lower()
    
    # Conta indicadores
    formal_count = sum(
        1 for pattern in FORMAL_INDICATORS 
        if re.search(pattern, text_lower)
    )
    
    informal_count = sum(
        1 for pattern in INFORMAL_INDICATORS 
        if re.search(pattern, text_lower)
    )
    
    very_informal_count = sum(
        1 for pattern in VERY_INFORMAL_INDICATORS 
        if re.search(pattern, text_lower)
    )
    
    # Determina nível
    if formal_count >= 2:
        return FormalityLevel.FORMAL
    elif very_informal_count >= 2 or (informal_count >= 3 and very_informal_count >= 1):
        return FormalityLevel.VERY_INFORMAL
    elif informal_count >= 2:
        return FormalityLevel.INFORMAL
    elif formal_count >= 1:
        return FormalityLevel.FORMAL
    else:
        return FormalityLevel.NEUTRAL


def normalize_text(
    text: str,
    expand_abbrev: bool = True,
    fix_typos: bool = True,
    preserve_case: bool = False,
) -> str:
    """
    Normaliza texto para processamento.
    
    Args:
        text: Texto original
        expand_abbrev: Expandir abreviações
        fix_typos: Corrigir erros comuns
        preserve_case: Manter maiúsculas/minúsculas
        
    Returns:
        Texto normalizado
        
    Example:
        >>> normalize_text("vc sabe onde fica o postinho d saude?")
        "você sabe onde fica o postinho de saúde?"
    """
    result = text.strip()
    
    # Remove espaços múltiplos
    result = re.sub(r'\s+', ' ', result)
    
    # Expande abreviações
    if expand_abbrev:
        result = expand_abbreviations(result)
    
    # Corrige erros comuns
    if fix_typos:
        result = fix_common_typos(result)
    
    # Normaliza case se necessário
    if not preserve_case:
        # Mantém primeira letra maiúscula de sentenças
        sentences = re.split(r'([.!?]+\s*)', result)
        normalized_sentences = []
        for i, part in enumerate(sentences):
            if i % 2 == 0 and part:  # É uma sentença (não pontuação)
                part = part[0].upper() + part[1:].lower() if len(part) > 1 else part.upper()
            normalized_sentences.append(part)
        result = ''.join(normalized_sentences)
    
    return result


def adapt_response_formality(
    response: str,
    target_level: FormalityLevel,
) -> str:
    """
    Adapta o nível de formalidade de uma resposta.
    
    Nota: Implementação básica. Para produção, usar LLM para reescrever.
    
    Args:
        response: Resposta original
        target_level: Nível de formalidade desejado
        
    Returns:
        Resposta adaptada
    """
    # Por enquanto, apenas ajusta saudações e fechamentos
    if target_level == FormalityLevel.FORMAL:
        # Adiciona formalidade
        if not any(f in response.lower() for f in ["prezad", "senhor", "atenciosamente"]):
            response = response.rstrip(".")
            if not response.endswith(("!", "?")):
                response += "."
    
    elif target_level in (FormalityLevel.INFORMAL, FormalityLevel.VERY_INFORMAL):
        # Remove formalidade excessiva
        response = re.sub(r"Prezad[oa]s?\s*,?\s*", "", response, flags=re.IGNORECASE)
        response = re.sub(r"Atenciosamente,?\s*", "", response, flags=re.IGNORECASE)
        
        # Adiciona emoji amigável no final se informal
        if target_level == FormalityLevel.INFORMAL and not any(
            emoji in response for emoji in ["😊", "👍", "✅", "📍", "📞"]
        ):
            response = response.rstrip(".") + " 😊"
    
    return response.strip()
