"""
Repositório de Cache de Perfis Meta — Pilot Atendimento MVE
============================================================
Versão: v1.0
Escopo: Acesso ao cache de perfis Instagram/Facebook

Repository pattern para acessar e gerenciar o cache de perfis
de usuários do Instagram/Facebook no PostgreSQL.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

import asyncpg

from app.models.meta_user_profile import MetaUserProfile, MetaUserProfileCreate
from app.settings import settings

logger = logging.getLogger(__name__)


class MetaUserProfileRepository:
    """
    Repositório para cache de perfis Meta.

    Responsabilidades:
    - Buscar perfis cacheados
    - Salvar/atualizar perfis no cache
    - Limpar entradas antigas (TTL)
    """

    def __init__(self):
        self.database_url = settings.DATABASE_URL
        self.ttl_days = 30  # Tempo de vida do cache em dias

    async def _get_connection(self) -> asyncpg.Connection:
        """Obtém conexão com o banco de dados."""
        return await asyncpg.connect(self.database_url)

    async def get_cached_profile(
        self, platform_user_id: str, platform: str
    ) -> Optional[MetaUserProfile]:
        """
        Busca um perfil cacheado.

        Args:
            platform_user_id: ID do usuário na plataforma
            platform: 'instagram' ou 'facebook'

        Returns:
            MetaUserProfile se encontrado e válido, None caso contrário
        """
        try:
            conn = await self._get_connection()
            try:
                # Calcula data limite (TTL)
                ttl_date = datetime.utcnow() - timedelta(days=self.ttl_days)

                row = await conn.fetchrow(
                    """
                    SELECT id, platform_user_id, platform, username, name, 
                           profile_picture_url, created_at, updated_at
                    FROM meta_user_profiles
                    WHERE platform_user_id = $1 
                      AND platform = $2
                      AND updated_at > $3
                    """,
                    platform_user_id,
                    platform,
                    ttl_date,
                )

                if row:
                    logger.debug(
                        f"Perfil cacheado encontrado: {platform_user_id} ({platform})"
                    )
                    return MetaUserProfile(**dict(row))

                return None

            finally:
                await conn.close()

        except Exception as e:
            logger.error(f"Erro ao buscar perfil cacheado: {e}")
            return None

    async def cache_profile(
        self, profile_data: MetaUserProfileCreate
    ) -> Optional[MetaUserProfile]:
        """
        Salva ou atualiza um perfil no cache.

        Args:
            profile_data: Dados do perfil a ser cacheado

        Returns:
            MetaUserProfile salvo, ou None em caso de erro
        """
        try:
            conn = await self._get_connection()
            try:
                row = await conn.fetchrow(
                    """
                    INSERT INTO meta_user_profiles 
                        (platform_user_id, platform, username, name, profile_picture_url)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (platform_user_id, platform) 
                    DO UPDATE SET
                        username = EXCLUDED.username,
                        name = EXCLUDED.name,
                        profile_picture_url = EXCLUDED.profile_picture_url,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id, platform_user_id, platform, username, name, 
                              profile_picture_url, created_at, updated_at
                    """,
                    profile_data.platform_user_id,
                    profile_data.platform,
                    profile_data.username,
                    profile_data.name,
                    profile_data.profile_picture_url,
                )

                if row:
                    logger.info(
                        f"Perfil cacheado: {profile_data.platform_user_id} "
                        f"({profile_data.platform}) - @{profile_data.username or 'N/A'}"
                    )
                    return MetaUserProfile(**dict(row))

                return None

            finally:
                await conn.close()

        except Exception as e:
            logger.error(f"Erro ao salvar perfil no cache: {e}")
            return None

    async def get_or_fetch_profile(
        self, platform_user_id: str, platform: str, fetch_func
    ) -> Optional[MetaUserProfile]:
        """
        Busca no cache ou executa função para obter perfil.

        Args:
            platform_user_id: ID do usuário na plataforma
            platform: 'instagram' ou 'facebook'
            fetch_func: Função async que busca o perfil na API

        Returns:
            MetaUserProfile do cache ou da API
        """
        # Tenta buscar do cache primeiro
        cached = await self.get_cached_profile(platform_user_id, platform)
        if cached:
            return cached

        # Se não está no cache, busca via API
        try:
            profile_data = await fetch_func(platform_user_id)
            if profile_data:
                # Salva no cache
                create_data = MetaUserProfileCreate(
                    platform_user_id=platform_user_id,
                    platform=platform,
                    username=profile_data.get("username"),
                    name=profile_data.get("name"),
                    profile_picture_url=profile_data.get("profile_picture_url"),
                )
                return await self.cache_profile(create_data)
        except Exception as e:
            logger.error(f"Erro ao buscar perfil na API: {e}")

        return None

    async def cleanup_old_entries(self) -> int:
        """
        Remove entradas antigas do cache (mais de 30 dias).

        Returns:
            Número de registros removidos
        """
        try:
            conn = await self._get_connection()
            try:
                ttl_date = datetime.utcnow() - timedelta(days=self.ttl_days)

                result = await conn.execute(
                    """
                    DELETE FROM meta_user_profiles
                    WHERE updated_at < $1
                    """,
                    ttl_date,
                )

                # Extrai número de registros afetados
                # Formato do resultado: "DELETE N"
                count = int(result.split()[1]) if result else 0

                if count > 0:
                    logger.info(f"Cache limpo: {count} registros antigos removidos")

                return count

            finally:
                await conn.close()

        except Exception as e:
            logger.error(f"Erro ao limpar cache antigo: {e}")
            return 0


# Instância singleton do repositório
meta_user_profile_repository = MetaUserProfileRepository()
