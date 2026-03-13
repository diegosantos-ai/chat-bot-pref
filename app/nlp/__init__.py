"""
Módulo NLP - Processamento de Linguagem Natural

Componentes:
- synonyms: Dicionário de sinônimos populares vs técnicos
- normalizer: Normalização de texto (acentos, gírias, abreviações)
- sentiment: Análise de sentimentos
- query_expander: Expansão de queries para busca RAG
"""

from app.nlp.synonyms import SYNONYMS, expand_terms
from app.nlp.normalizer import normalize_text, detect_formality_level
from app.nlp.sentiment import SentimentAnalyzer, SentimentResult
from app.nlp.query_expander import QueryExpander

__all__ = [
    "SYNONYMS",
    "expand_terms",
    "normalize_text",
    "detect_formality_level",
    "SentimentAnalyzer",
    "SentimentResult",
    "QueryExpander",
]
