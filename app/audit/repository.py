"""
Audit Repository — Nexo Basis Governador SaaS
=========================================
Versão: v2.0
Escopo: SAAS_MULTI_TENANT

Repository async para operações de auditoria usando asyncpg.
Isolamento de dados por tenant via Row-Level Security (PostgreSQL).
O tenant ativo é lido via `app.tenant_context.require_tenant()` e injetado
através de `SET LOCAL app.tenant_id` em cada conexão antes das queries.
"""

import json
import logging
import hashlib
from typing import Optional
from uuid import UUID
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Pool, Connection

from app.settings import settings
from app.audit.models import AuditEventCreate, RAGQueryCreate, ConversaCreate
from app import tenant_context

logger = logging.getLogger(__name__)


class AuditRepository:
    """
    Repository para operações de auditoria.
    Gerencia conexões e persistência de eventos.
    """
    
    def __init__(self):
        self._pool: Optional[Pool] = None
    
    async def connect(self) -> None:
        """Inicializa o pool de conexões."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=2,
                max_size=settings.DATABASE_POOL_SIZE,
                max_inactive_connection_lifetime=300,
            )
            logger.info("Pool de conexões PostgreSQL criado")
    
    async def disconnect(self) -> None:
        """Fecha o pool de conexões."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Pool de conexões PostgreSQL fechado")
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager que obtém conexão do pool e injeta tenant_id via SET LOCAL."""
        if self._pool is None:
            await self.connect()

        # Obtém o tenant ativo do contexto assync (definido pelo middleware)
        current_tenant = tenant_context.require_tenant()

        async with self._pool.acquire() as conn:
            # Injeta o tenant na sessão PostgreSQL para ativar a RLS
            await conn.execute(
                f"SET LOCAL app.tenant_id = '{current_tenant}'"
            )
            yield conn
    
    async def check_idempotency(
        self,
        external_message_id: str,
        conn: Optional[Connection] = None,
    ) -> bool:
        """
        Verifica se mensagem já foi processada (idempotência).
        
        Args:
            external_message_id: ID da mensagem na plataforma externa
            conn: Conexão opcional
            
        Returns:
            True se já existe, False caso contrário
        """
        query = """
            SELECT 1 FROM audit_events 
            WHERE id_mensagem_externa = $1 
            LIMIT 1
        """
        
        if conn:
            row = await conn.fetchrow(query, external_message_id)
        else:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(query, external_message_id)
        
        return row is not None

    def _hash_user(self, session_id: str) -> str:
        salt = settings.USER_HASH_SALT or ""
        raw = f"{salt}{session_id}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def _get_or_create_user_id(
        self,
        session_id: str,
        conn: Connection,
    ) -> int:
        hash_usuario = self._hash_user(session_id)
        current_tenant = tenant_context.require_tenant()
        row = await conn.fetchrow(
            "SELECT id_usuario FROM usuarios_anonimos WHERE hash_usuario = $1 AND tenant_id = $2",
            hash_usuario, current_tenant,
        )
        if row:
            return row["id_usuario"]

        row = await conn.fetchrow(
            "INSERT INTO usuarios_anonimos (hash_usuario, tenant_id) VALUES ($1, $2) RETURNING id_usuario",
            hash_usuario, current_tenant,
        )
        return row["id_usuario"]

    async def get_or_create_user_id(self, session_id: str) -> int:
        async with self.get_connection() as conn:
            return await self._get_or_create_user_id(session_id, conn)
    
    async def insert_audit_event(
        self,
        event: AuditEventCreate,
        conn: Optional[Connection] = None,
    ) -> UUID:
        """
        Insere um evento de auditoria.
        
        Args:
            event: Dados do evento
            conn: Conexão opcional (para transações)
            
        Returns:
            UUID do evento criado
        """
        query = """
            INSERT INTO audit_events (
                id_requisicao, id_sessao, id_usuario,
                canal, tipo_superficie, id_mensagem_externa,
                id_thread, id_post, id_comentario, id_autor_plataforma,
                intencao, confianca_classificador,
                decisao_politica, motivo_bloqueio, id_regra_bloqueio,
                decisao, tipo_resposta, motivo_fallback,
                id_base,
                modelo, temperatura, versao_prompt,
                tempo_resposta_ms,
                codigo_erro, tipo_excecao,
                versao_app, tenant_id
            ) VALUES (
                $1, $2, $3,
                $4, $5, $6,
                $7, $8, $9, $10,
                $11, $12,
                $13, $14, $15,
                $16, $17, $18,
                $19,
                $20, $21, $22,
                $23,
                $24, $25,
                $26, $27
            )
            RETURNING id_evento
        """

        # Normalizações para enums do banco
        surface_db = (event.tipo_superficie.value.lower() if event.tipo_superficie else "inbox")
        policy_db = event.decisao_politica.value
        response_db = event.tipo_resposta.value

        async def _execute(conn: Connection) -> UUID:
            user_id = event.id_usuario
            if user_id is None:
                user_id = await self._get_or_create_user_id(event.id_sessao, conn)

            params = (
                event.id_requisicao,
                event.id_sessao,
                user_id,
                event.canal.value,
                surface_db,
                event.id_mensagem_externa,
                event.id_thread,
                event.id_post,
                event.id_comentario,
                event.id_autor_plataforma,
                event.intencao.value,
                event.confianca_classificador,
                policy_db,
                event.motivo_bloqueio,
                event.id_regra_bloqueio,
                event.decisao.value,
                response_db,
                event.motivo_fallback.value if event.motivo_fallback else None,
                event.id_base,
                event.modelo,
                event.temperatura,
                event.versao_prompt,
                event.tempo_resposta_ms,
                event.codigo_erro,
                event.tipo_excecao,
                event.versao_app,
                tenant_context.require_tenant(),  # sempre fornecido pelo context
            )

            row = await conn.fetchrow(query, *params)
            return row["id_evento"]

        if conn:
            event_id = await _execute(conn)
        else:
            async with self.get_connection() as conn:
                event_id = await _execute(conn)

        logger.debug(f"Audit event criado: {event_id}")
        return event_id
    
    async def insert_rag_query(
        self,
        rag_query: RAGQueryCreate,
        conn: Optional[Connection] = None,
    ) -> UUID:
        """
        Insere uma consulta RAG.
        
        Args:
            rag_query: Dados da consulta
            conn: Conexão opcional (para transações)
            
        Returns:
            UUID da query criada
        """
        # Serializa documentos para JSONB
        docs_json = None
        if rag_query.documentos_recuperados:
            docs_json = json.dumps(
                [doc.model_dump(mode="json") for doc in rag_query.documentos_recuperados]
            )
        
        query = """
            INSERT INTO rag_queries (
                id_requisicao, id_base, tipo_superficie,
                texto_consulta, modelo_embedding,
                top_k,
                documentos_recuperados, quantidade_documentos, melhor_score, sem_documentos,
                tempo_busca_ms
            ) VALUES (
                $1, $2, $3,
                $4, $5,
                $6,
                $7, $8, $9, $10,
                $11
            )
            RETURNING id_consulta
        """
        
        params = (
            rag_query.id_requisicao,
            rag_query.id_base,
            rag_query.tipo_superficie.value.lower() if rag_query.tipo_superficie else None,
            rag_query.texto_consulta,
            rag_query.modelo_embedding,
            rag_query.top_k,
            docs_json,
            rag_query.quantidade_documentos,
            rag_query.melhor_score,
            rag_query.sem_documentos,
            rag_query.tempo_busca_ms,
        )
        
        if conn:
            row = await conn.fetchrow(query, *params)
        else:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(query, *params)
        
        id_consulta = row["id_consulta"]
        logger.debug(f"RAG query criada: {id_consulta}")
        return id_consulta

    async def insert_conversa(
        self,
        conversa: ConversaCreate,
        conn: Optional[Connection] = None,
    ) -> int:
        query = """
            INSERT INTO conversas (
                id_requisicao, id_usuario,
                canal, tipo_superficie,
                mensagem_usuario, mensagem_resposta,
                tamanho_mensagem, tamanho_resposta,
                intencao, decisao, tipo_resposta,
                motivo_fallback, motivo_politica,
                sentimento, emocao, formalidade,
                consulta_expandida, encontrou_docs, melhor_score, fontes,
                modelo, temperatura
            ) VALUES (
                $1, $2,
                $3, $4,
                $5, $6,
                $7, $8,
                $9, $10, $11,
                $12, $13,
                $14, $15, $16,
                $17, $18, $19, $20,
                $21, $22
            )
            RETURNING id_conversa
        """

        params = (
            conversa.id_requisicao,
            conversa.id_usuario,
            conversa.canal.value,
            conversa.tipo_superficie.value.lower(),
            conversa.mensagem_usuario,
            conversa.mensagem_resposta,
            conversa.tamanho_mensagem,
            conversa.tamanho_resposta,
            conversa.intencao.value,
            conversa.decisao.value,
            conversa.tipo_resposta.value,
            conversa.motivo_fallback.value if conversa.motivo_fallback else None,
            conversa.motivo_politica,
            conversa.sentimento,
            conversa.emocao,
            conversa.formalidade,
            conversa.consulta_expandida,
            conversa.encontrou_docs,
            conversa.melhor_score,
            conversa.fontes,
            conversa.modelo,
            conversa.temperatura,
        )

        if conn:
            row = await conn.fetchrow(query, *params)
        else:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(query, *params)

        return row["id_conversa"]
    
    async def insert_audit_with_rag(
        self,
        event: AuditEventCreate,
        rag_query: Optional[RAGQueryCreate] = None,
        conversa: Optional[ConversaCreate] = None,
    ) -> tuple[UUID, Optional[UUID], Optional[int]]:
        """
        Insere evento de auditoria e consulta RAG em uma transação.
        
        Args:
            event: Dados do evento
            rag_query: Dados da consulta RAG (opcional)
            
        Returns:
            Tuple (event_id, query_id ou None)
        """
        async with self.get_connection() as conn:
            async with conn.transaction():
                event_id = await self.insert_audit_event(event, conn)
                
                query_id = None
                if rag_query:
                    query_id = await self.insert_rag_query(rag_query, conn)
                
                conversa_id = None
                if conversa:
                    conversa_id = await self.insert_conversa(conversa, conn)

                return event_id, query_id, conversa_id


# Instância singleton do repository
audit_repository = AuditRepository()
