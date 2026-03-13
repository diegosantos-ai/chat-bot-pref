"""
Análise de Sentimentos - Detecta emoções e tom da mensagem

Permite adaptar a resposta ao estado emocional do cidadão:
- Frustrado/irritado → resposta mais empática
- Ansioso/preocupado → resposta tranquilizadora
- Satisfeito/agradecido → resposta calorosa
- Neutro → resposta objetiva
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Sentiment(str, Enum):
    """Sentimento geral da mensagem."""
    VERY_POSITIVE = "very_positive"   # Muito satisfeito, entusiasmado
    POSITIVE = "positive"             # Satisfeito, agradecido
    NEUTRAL = "neutral"               # Objetivo, sem emoção clara
    NEGATIVE = "negative"             # Insatisfeito, preocupado
    VERY_NEGATIVE = "very_negative"   # Irritado, frustrado


class Emotion(str, Enum):
    """Emoção específica detectada."""
    JOY = "joy"               # Alegria, satisfação
    GRATITUDE = "gratitude"   # Agradecimento
    HOPE = "hope"             # Esperança, expectativa positiva
    ANXIETY = "anxiety"       # Ansiedade, preocupação
    FRUSTRATION = "frustration"  # Frustração
    ANGER = "anger"           # Raiva
    SADNESS = "sadness"       # Tristeza
    CONFUSION = "confusion"   # Confusão, dúvida
    URGENCY = "urgency"       # Urgência
    NEUTRAL = "neutral"       # Sem emoção clara


@dataclass
class SentimentResult:
    """Resultado da análise de sentimentos."""
    sentiment: Sentiment
    emotion: Emotion
    confidence: float
    intensity: float  # 0.0 a 1.0
    
    # Flags específicos
    is_frustrated: bool = False
    is_urgent: bool = False
    is_vulnerable: bool = False  # Ex: grávida confusa, idoso perdido
    needs_empathy: bool = False
    
    # Sugestões para resposta
    tone_suggestion: str = "neutral"  # "empathetic", "reassuring", "warm", "professional"


# =============================================================================
# LÉXICO DE SENTIMENTOS (adaptado para PT-BR)
# =============================================================================

# Palavras positivas com intensidade
POSITIVE_WORDS = {
    # Muito positivas (intensidade 1.0)
    "excelente": 1.0, "maravilhoso": 1.0, "fantástico": 1.0, "perfeito": 1.0,
    "incrível": 1.0, "sensacional": 1.0, "espetacular": 1.0, "ótimo": 0.9,
    "parabéns": 1.0, "parabenizo": 1.0,
    
    # Positivas (intensidade 0.7)
    "bom": 0.7, "legal": 0.7, "bacana": 0.7, "massa": 0.7, "show": 0.8,
    "top": 0.8, "maneiro": 0.7, "dahora": 0.7,
    
    # Levemente positivas (intensidade 0.5)
    "ok": 0.5, "tudo bem": 0.5, "tranquilo": 0.5, "beleza": 0.5,
    "certo": 0.4, "correto": 0.4,
    
    # Agradecimento
    "obrigado": 0.7, "obrigada": 0.7, "agradeço": 0.8, "agradecida": 0.8,
    "valeu": 0.6, "vlw": 0.6, "grato": 0.7, "grata": 0.7,
}

# Palavras negativas com intensidade
NEGATIVE_WORDS = {
    # Muito negativas (intensidade -1.0)
    "péssimo": -1.0, "horrível": -1.0, "terrível": -1.0, "absurdo": -1.0,
    "vergonha": -0.9, "descaso": -0.9, "desrespeito": -0.9,
    
    # Negativas (intensidade -0.7)
    "ruim": -0.7, "mal": -0.6, "problema": -0.5, "difícil": -0.5,
    "complicado": -0.5, "demora": -0.6, "demorado": -0.6,
    
    # Frustração
    "frustrado": -0.8, "frustrada": -0.8, "frustração": -0.8,
    "cansado": -0.6, "cansada": -0.6, "exausto": -0.7,
    "irritado": -0.8, "irritada": -0.8,
    
    # Reclamação
    "reclamação": -0.6, "reclamo": -0.6, "reclamar": -0.6,
    "insatisfeito": -0.7, "insatisfeita": -0.7,
}

# Padrões de emoções específicas
EMOTION_PATTERNS = {
    Emotion.JOY: [
        r"(muito\s+)?(feliz|contente|alegre|satisfeit[oa])",
        r"(adorei|amei|curti|gostei\s+muito)",
        r"(que\s+)?(legal|massa|show|top|maravilh)",
    ],
    Emotion.GRATITUDE: [
        r"(muito\s+)?(obrigad[oa]|agradec|grat[oa])",
        r"(valeu|vlw|brigadão|brigadao)",
        r"(agradeço|agradecemos)\s+(muito|demais)?",
    ],
    Emotion.HOPE: [
        r"(espero|esperando|tomara|torço|torco)",
        r"(quero\s+acreditar|confio|confiant)",
        r"(vai\s+dar\s+certo|vai\s+melhorar)",
    ],
    Emotion.ANXIETY: [
        r"(preocupad[oa]|ansios[oa]|apreensiv[oa])",
        r"(não\s+sei|nao\s+sei)\s+(o\s+que|como|onde)",
        r"(preciso\s+muito|urgente|urgência|urgencia)",
        r"(medo|receio|tenho\s+medo)",
        r"(nervos[oa]|aflito|aflita)",
    ],
    Emotion.FRUSTRATION: [
        r"(frustrad[oa]|frustração|frustracao)",
        r"(já\s+tentei|ja\s+tentei|várias\s+vezes|varias\s+vezes)",
        r"(não\s+consigo|nao\s+consigo|impossível|impossivel)",
        r"(cansei|cansad[oa]\s+de|desisti)",
        r"(ninguém\s+ajuda|ninguem\s+ajuda|ninguém\s+resolve)",
    ],
    Emotion.ANGER: [
        r"(raiva|ódio|odio|revoltad[oa])",
        r"(absurdo|inaceitável|inaceitavel|vergonha)",
        r"(incompetent|descaso|desrespeito)",
        r"(vou\s+processar|vou\s+denunciar)",
        r"(!{2,})",  # Múltiplas exclamações
    ],
    Emotion.SADNESS: [
        r"(triste|tristeza|chorei|chorando)",
        r"(decepcionad[oa]|desanimad[oa])",
        r"(difícil|dificil)\s+(momento|situação|situacao)",
        r"(perdid[oa]|desamparad[oa])",
    ],
    Emotion.CONFUSION: [
        r"(confus[oa]|perdid[oa]|sem\s+entender)",
        r"(não\s+entendi|nao\s+entendi|como\s+assim)",
        r"(onde|como|quando|qual)\s+(é|que|eu)",
        r"(\?\s*){2,}",  # Múltiplas interrogações
    ],
    Emotion.URGENCY: [
        r"(urgent[e]|emergência|emergencia)",
        r"(agora|hoje|já|ja|imediato)",
        r"(preciso\s+muito|preciso\s+urgente)",
        r"(prazo|vence|vencimento|amanhã|amanha)",
        r"(socorro|ajuda|por\s+favor.*!)",
    ],
}

# Indicadores de vulnerabilidade
VULNERABILITY_PATTERNS = [
    r"(grávida|gravida|gestante)\s+(e\s+)?(não\s+sei|nao\s+sei|perdida|confusa)",
    r"(idos[oa]|velh[oa]|aposentad[oa])\s+(e\s+)?(não\s+sei|nao\s+sei|perdid[oa])",
    r"(sozinha|sozinho)\s+(e\s+)?(não\s+sei|nao\s+sei)",
    r"(deficiente|especial|cadeirante)",
    r"(primeira\s+vez|nunca\s+fiz|não\s+sei\s+por\s+onde)",
    r"(desempregad[oa]|sem\s+renda|passando\s+necessidade)",
    r"(mãe\s+solteira|mae\s+solteira|pai\s+solteiro)",
]


class SentimentAnalyzer:
    """
    Analisador de sentimentos adaptado para atendimento público.
    
    Foco em detectar cidadãos que precisam de atenção especial:
    - Frustrados com burocracia
    - Vulneráveis (idosos, gestantes, desempregados)
    - Confusos (primeira vez, pouca instrução)
    - Urgentes (prazos, emergências)
    """
    
    def analyze(self, text: str) -> SentimentResult:
        """
        Analisa o sentimento e emoção de uma mensagem.
        
        Args:
            text: Texto da mensagem
            
        Returns:
            SentimentResult com análise completa
        """
        text_lower = text.lower()
        
        # 1. Calcula score léxico
        sentiment_score = self._calculate_lexicon_score(text_lower)
        
        # 2. Detecta emoção principal
        emotion = self._detect_emotion(text_lower)
        
        # 3. Detecta vulnerabilidade
        is_vulnerable = self._detect_vulnerability(text_lower)
        
        # 4. Detecta urgência
        is_urgent = any(
            re.search(p, text_lower) 
            for p in EMOTION_PATTERNS[Emotion.URGENCY]
        )
        
        # 5. Detecta frustração
        is_frustrated = emotion == Emotion.FRUSTRATION or any(
            re.search(p, text_lower) 
            for p in EMOTION_PATTERNS[Emotion.FRUSTRATION]
        )
        
        # 6. Determina sentimento geral
        sentiment = self._score_to_sentiment(sentiment_score)
        
        # 7. Calcula intensidade
        intensity = min(abs(sentiment_score), 1.0)
        
        # 8. Determina se precisa de empatia
        needs_empathy = (
            is_vulnerable or 
            is_frustrated or 
            emotion in (Emotion.SADNESS, Emotion.ANXIETY, Emotion.ANGER)
        )
        
        # 9. Sugere tom da resposta
        tone_suggestion = self._suggest_tone(
            sentiment, emotion, is_vulnerable, is_urgent, is_frustrated
        )
        
        return SentimentResult(
            sentiment=sentiment,
            emotion=emotion,
            confidence=0.7 + (intensity * 0.3),  # Maior intensidade = maior confiança
            intensity=intensity,
            is_frustrated=is_frustrated,
            is_urgent=is_urgent,
            is_vulnerable=is_vulnerable,
            needs_empathy=needs_empathy,
            tone_suggestion=tone_suggestion,
        )
    
    def _calculate_lexicon_score(self, text: str) -> float:
        """Calcula score baseado em léxico de palavras."""
        score = 0.0
        word_count = 0
        
        # Palavras positivas
        for word, intensity in POSITIVE_WORDS.items():
            if word in text:
                score += intensity
                word_count += 1
        
        # Palavras negativas
        for word, intensity in NEGATIVE_WORDS.items():
            if word in text:
                score += intensity  # intensity já é negativo
                word_count += 1
        
        # Negação inverte sentimento parcialmente
        negation_patterns = [
            r"\b(não|nao|nunca|jamais|nem)\s+",
        ]
        for pattern in negation_patterns:
            if re.search(pattern, text):
                score *= 0.5  # Atenua o sentimento
        
        # Intensificadores
        intensifiers = [
            r"\b(muito|demais|extremamente|super|mega)\b",
        ]
        for pattern in intensifiers:
            if re.search(pattern, text):
                score *= 1.3  # Intensifica
        
        return max(-1.0, min(1.0, score))  # Normaliza entre -1 e 1
    
    def _detect_emotion(self, text: str) -> Emotion:
        """Detecta a emoção principal na mensagem."""
        emotion_scores = {}
        
        for emotion, patterns in EMOTION_PATTERNS.items():
            matches = sum(
                1 for p in patterns 
                if re.search(p, text, re.IGNORECASE)
            )
            if matches > 0:
                emotion_scores[emotion] = matches
        
        if emotion_scores:
            return max(emotion_scores, key=emotion_scores.get)
        
        return Emotion.NEUTRAL
    
    def _detect_vulnerability(self, text: str) -> bool:
        """Detecta indicadores de vulnerabilidade."""
        return any(
            re.search(p, text, re.IGNORECASE) 
            for p in VULNERABILITY_PATTERNS
        )
    
    def _score_to_sentiment(self, score: float) -> Sentiment:
        """Converte score numérico em sentimento categórico."""
        if score >= 0.7:
            return Sentiment.VERY_POSITIVE
        elif score >= 0.3:
            return Sentiment.POSITIVE
        elif score > -0.3:
            return Sentiment.NEUTRAL
        elif score > -0.7:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.VERY_NEGATIVE
    
    def _suggest_tone(
        self,
        sentiment: Sentiment,
        emotion: Emotion,
        is_vulnerable: bool,
        is_urgent: bool,
        is_frustrated: bool,
    ) -> str:
        """Sugere o tom apropriado para a resposta."""
        
        # Vulnerável sempre precisa de empatia
        if is_vulnerable:
            return "empathetic_supportive"
        
        # Frustrado precisa de empatia e objetividade
        if is_frustrated:
            return "empathetic_solution"
        
        # Urgente precisa ser direto
        if is_urgent:
            return "direct_helpful"
        
        # Por emoção
        tone_map = {
            Emotion.ANGER: "calm_professional",
            Emotion.ANXIETY: "reassuring",
            Emotion.SADNESS: "empathetic_warm",
            Emotion.CONFUSION: "clear_patient",
            Emotion.GRATITUDE: "warm_friendly",
            Emotion.JOY: "warm_friendly",
            Emotion.HOPE: "encouraging",
        }
        
        if emotion in tone_map:
            return tone_map[emotion]
        
        # Por sentimento geral
        if sentiment in (Sentiment.POSITIVE, Sentiment.VERY_POSITIVE):
            return "warm_friendly"
        elif sentiment in (Sentiment.NEGATIVE, Sentiment.VERY_NEGATIVE):
            return "empathetic_professional"
        
        return "neutral_helpful"


# Singleton para uso fácil
_analyzer: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Retorna instância singleton do analisador."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer


def analyze_sentiment(text: str) -> SentimentResult:
    """
    Função de conveniência para análise de sentimento.
    
    Args:
        text: Texto a analisar
        
    Returns:
        SentimentResult
        
    Example:
        >>> result = analyze_sentiment("estou frustrada, já tentei várias vezes")
        >>> result.is_frustrated
        True
        >>> result.tone_suggestion
        "empathetic_solution"
    """
    return get_sentiment_analyzer().analyze(text)
