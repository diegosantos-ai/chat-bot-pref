"""
Modelos de Auditoria — Pilot Atendimento MVE
=============================================
Versão: v1.1
Escopo: MVE_PILOT
Atualizado: Suporte a Instagram/Facebook

Modelos Pydantic que espelham as tabelas de auditoria.
Usados para validação e serialização de dados.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

from app.contracts.enums import (
    Intent,
    Decision,
    ResponseType,
    PolicyDecision,
    FallbackReason,
    Channel,
    SurfaceType,
)


class RAGDocumentResult(BaseModel):
    """Documento retornado pelo RAG."""
    
    doc_id: str
    title: Optional[str] = None
    score: Decimal
    snippet: Optional[str] = None


class AuditEventCreate(BaseModel):
    """
    Dados para criar um evento de auditoria.
    Corresponde à tabela audit_events.
    """
    
    # Identificação
    id_requisicao: UUID
    id_sessao: str
    id_usuario: Optional[int] = None
    
    # Canal e Superfície (Meta: IG/FB)
    canal: Channel = Channel.WEB_WIDGET
    tipo_superficie: SurfaceType = SurfaceType.INBOX
    id_mensagem_externa: Optional[str] = None
    id_thread: Optional[str] = None
    id_post: Optional[str] = None
    id_comentario: Optional[str] = None
    id_autor_plataforma: Optional[str] = None
    
    # Classificação
    intencao: Intent
    confianca_classificador: Optional[Decimal] = None
    
    # Policy Guard
    decisao_politica: PolicyDecision
    motivo_bloqueio: Optional[str] = None
    id_regra_bloqueio: Optional[str] = None
    
    # Decisão e Resposta
    decisao: Decision
    tipo_resposta: ResponseType
    motivo_fallback: Optional[FallbackReason] = None
    
    # RAG
    id_base: Optional[str] = None
    
    # Modelo/LLM
    modelo: Optional[str] = None
    temperatura: Optional[Decimal] = None
    versao_prompt: Optional[str] = None
    
    # Performance
    tempo_resposta_ms: Optional[int] = None
    
    # Erros
    codigo_erro: Optional[str] = None
    tipo_excecao: Optional[str] = None
    
    # Versionamento
    versao_app: Optional[str] = None


class AuditEvent(AuditEventCreate):
    """Evento de auditoria completo (com campos do banco)."""
    
    id_evento: UUID
    criado_em: datetime


class RAGQueryCreate(BaseModel):
    """
    Dados para registrar uma consulta RAG.
    Corresponde à tabela rag_queries.
    """
    
    id_requisicao: UUID
    
    # Base de conhecimento
    id_base: Optional[str] = None
    
    # Superfície (afeta modo de resposta)
    tipo_superficie: Optional[SurfaceType] = None
    
    # Query
    texto_consulta: str
    modelo_embedding: Optional[str] = None
    
    # Parâmetros da busca
    top_k: Optional[int] = None
    
    # Resultados
    documentos_recuperados: Optional[List[RAGDocumentResult]] = None
    quantidade_documentos: int = 0
    melhor_score: Optional[Decimal] = None
    sem_documentos: bool = False
    
    # Performance
    tempo_busca_ms: Optional[int] = None


class RAGQuery(RAGQueryCreate):
    """Consulta RAG completa (com campos do banco)."""
    
    id_consulta: UUID
    criado_em: datetime


class ConversaCreate(BaseModel):
    """Dados para registrar uma conversa (pergunta e resposta)."""

    id_requisicao: UUID
    id_usuario: int
    canal: Channel
    tipo_superficie: SurfaceType
    mensagem_usuario: str
    mensagem_resposta: Optional[str] = None
    tamanho_mensagem: Optional[int] = None
    tamanho_resposta: Optional[int] = None
    intencao: Intent
    decisao: Decision
    tipo_resposta: ResponseType
    motivo_fallback: Optional[FallbackReason] = None
    motivo_politica: Optional[str] = None
    sentimento: Optional[str] = None
    emocao: Optional[str] = None
    formalidade: Optional[str] = None
    consulta_expandida: Optional[str] = None
    encontrou_docs: Optional[bool] = None
    melhor_score: Optional[Decimal] = None
    fontes: Optional[List[str]] = None
    modelo: Optional[str] = None
    temperatura: Optional[Decimal] = None


class Conversa(ConversaCreate):
    id_conversa: int
    criado_em: datetime
