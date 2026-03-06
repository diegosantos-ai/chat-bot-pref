"""
Boost Configurável - Sistema de boost para RAG

Este arquivo contém a lógica de boost que substitui o sistema
hardcoded em acronyms.py.

Tipos de Boost:
- sigla: matching exato de sigla (REFIS, IPTU, etc)
- palavra_chave: termos a buscar (separados por vírgula)
- categoria: boost por tags/categorias dos documentos

用法:
    from app.rag.boosts import get_total_boost, load_boost_configs

    # Calcular boost total
    boost = get_total_boost(query, chunk_text, chunk_tags)
"""

import unicodedata
import logging
from dataclasses import dataclass
from typing import List, Optional

import asyncpg

from app.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class BoostConfig:
    """Configuração de um boost."""

    id: str
    nome: str
    tipo: str  # 'sigla' | 'palavra_chave' | 'categoria'
    valor: str
    boost_value: float
    prioridade: int
    ativo: bool


# Cache em memória dos boosts
_boosts_cache: Optional[List[BoostConfig]] = None


def normalize_text(text: str) -> str:
    """
    Normaliza texto: remove acentos e converte para lowercase.

    Example:
        >>> normalize_text("Vacinação")
        'vacinacao'
        >>> normalize_text("ação")
        'acao'
    """
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def extract_acronyms(query: str) -> List[str]:
    """
    Extrai siglas de uma query.

    Example:
        >>> extract_acronyms("quero saber sobre o REFIS 2025")
        ['REFIS']
    """
    from app.rag.acronyms import extract_acronyms_from_query as _extract

    return _extract(query)


async def load_boost_configs() -> List[BoostConfig]:
    """
    Carrega configurações de boost do banco de dados.
    Usa cache em memória para performance.
    """
    global _boosts_cache

    if _boosts_cache is not None:
        return _boosts_cache

    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        rows = await conn.fetch("""
            SELECT id, nome, tipo, valor, boost_value, prioridade, ativo
            FROM boost_configs
            WHERE ativo = TRUE
            ORDER BY prioridade DESC
        """)
        await conn.close()

        _boosts_cache = [
            BoostConfig(
                id=str(row["id"]),
                nome=row["nome"],
                tipo=row["tipo"],
                valor=row["valor"],
                boost_value=row["boost_value"],
                prioridade=row["prioridade"],
                ativo=row["ativo"],
            )
            for row in rows
        ]

        logger.info(f"Loaded {len(_boosts_cache)} boost configs from database")
        return _boosts_cache

    except Exception as e:
        logger.error(f"Error loading boost configs: {e}")
        # Fallback: retorna lista vazia
        return []


def invalidate_cache():
    """Invalidar o cache de boosts."""
    global _boosts_cache
    _boosts_cache = None


async def get_total_boost(
    query: str, chunk_text: str, chunk_tags: Optional[List[str]] = None
) -> float:
    """
    Calcula o boost total (soma de todos os boosts aplicáveis).

    Args:
        query: Query do usuário
        chunk_text: Texto do chunk recuperado
        chunk_tags: Tags/categorias do documento (opcional)

    Returns:
        Soma de todos os boosts aplicáveis (0.0 a 1.0 max)
    """
    if chunk_tags is None:
        chunk_tags = []

    boosts = await load_boost_configs()

    if not boosts:
        return 0.0

    total_boost = 0.0

    query_upper = query.upper()
    query_normalized = normalize_text(query)
    chunk_normalized = normalize_text(chunk_text)

    # Extrair siglas da query para matching
    query_acronyms = extract_acronyms(query)

    for boost in boosts:
        if not boost.ativo:
            continue

        try:
            if boost.tipo == "sigla":
                # Boost por sigla: verificar se a sigla está na query E no chunk
                if boost.valor in query_acronyms:
                    # Verificar se a sigla aparece no chunk
                    if boost.valor in chunk_text.upper():
                        total_boost += boost.boost_value

            elif boost.tipo == "palavra_chave":
                # Boost por palavra-chave: verificar termos no chunk
                termos = [normalize_text(t.strip()) for t in boost.valor.split(",")]
                for termo in termos:
                    if termo in chunk_normalized or termo in query_normalized:
                        total_boost += boost.boost_value
                        break  # Um boost por config

            elif boost.tipo == "categoria":
                # Boost por categoria: verificar tags do documento
                for tag in chunk_tags:
                    tag_normalized = normalize_text(tag)
                    valor_normalized = normalize_text(boost.valor)
                    if tag_normalized == valor_normalized:
                        total_boost += boost.boost_value
                        break

        except Exception as e:
            logger.warning(f"Error applying boost {boost.nome}: {e}")
            continue

    # Limita o boost máximo em 1.0
    return min(total_boost, 1.0)


async def get_acronym_boost(query: str, chunk_text: str) -> float:
    """
    Função de compatibilidade com a API anterior.
    Mantida para não quebrar referências existentes.

    Agora usa o sistema configurável de boosts.
    """
    return await get_total_boost(query, chunk_text)


async def get_boosts_by_type(tipo: str) -> List[BoostConfig]:
    """Retorna boosts de um tipo específico."""
    boosts = await load_boost_configs()
    return [b for b in boosts if b.tipo == tipo]


async def get_active_boost_count() -> int:
    """Retorna a contagem de boosts ativos."""
    boosts = await load_boost_configs()
    return len([b for b in boosts if b.ativo])
