"""
Orchestrator Service — Pilot Atendimento MVE
=============================================
Pipeline completo de processamento de mensagens com eventos de auditoria.

Responsabilidades:
- Coordenar Classifier → Policy Guard → RAG → Response
- Gerar eventos de auditoria em cada etapa
- Aplicar regras de decisão por superfície
- Controlar repetição de ACK público
- Analisar sentimento e adaptar tom da resposta
- Expandir queries para melhor recuperação RAG
"""

import hashlib
import asyncio
import logging
from uuid import UUID
from decimal import Decimal
from typing import Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

from app.contracts.enums import (
    Intent,
    Decision,
    ResponseType,
    PolicyDecision,
    PolicyReason,
    FallbackReason,
    SurfaceType,
    Channel,
    AuditEventType,
)
from app.contracts.dto import (
    ChatRequest,
    ChatResponse,
    RequestContext,
    PolicyPreResult,
    RAGRetrieveResult,
    ResponseSelectedResult,
    MessageSentResult,
    PublicAckResult,
)
from app.classifier.service import ClassifierService, get_classifier
from app.policy_guard.service import PolicyGuardService, get_policy_guard
from app.rag.retriever import RAGRetriever, get_retriever
from app.rag.composer import RAGComposer, get_composer
from app.prompts import load_prompt, get_public_ack
from app.settings import settings
from app.services.mailer import mailer
from app.repositories.meta_user_profile_repository import meta_user_profile_repository
from app.integrations.meta.client import get_meta_client
from app.models.meta_user_profile import MetaUserProfileCreate

# NLP - Análise de sentimentos e expansão de queries
from app.nlp.sentiment import analyze_sentiment
from app.nlp.query_expander import expand_query
from app.nlp.normalizer import normalize_text, detect_formality_level

# Analytics - Coleta de dados para melhorar RAG
from app.analytics import QueryAnalytics
from app.audit.repository import audit_repository
from app.audit.models import AuditEventCreate, RAGQueryCreate, ConversaCreate


# Cache de último ACK por thread (memória simples para MVP)
# Em produção, usar Redis ou similar
_last_ack_by_thread: dict[str, str] = {}


class OrchestratorService:
    """
    Orquestrador principal do pipeline de chat.

    Pipeline completo:
    1. Classificar intent
    2. Avaliar policy PRE
    3. Se permitido, executar RAG
    4. Selecionar resposta
    5. Avaliar policy POST
    6. Enviar resposta
    7. Registrar auditoria
    """

    def __init__(
        self,
        classifier: Optional[ClassifierService] = None,
        policy_guard: Optional[PolicyGuardService] = None,
        retriever: Optional[RAGRetriever] = None,
        composer: Optional[RAGComposer] = None,
    ):
        self.classifier = classifier or get_classifier()
        self.policy_guard = policy_guard or get_policy_guard()
        self.retriever = retriever or get_retriever()
        self.composer = composer or get_composer()
        self.mailer = mailer

    async def process(
        self,
        request: ChatRequest,
        thread_id: Optional[str] = None,
        post_id: Optional[str] = None,
        comment_id: Optional[str] = None,
    ) -> tuple[ChatResponse, RequestContext]:
        """
        Processa uma mensagem através do pipeline completo.

        Args:
            request: Requisição de chat
            thread_id: ID do thread (para DMs)
            post_id: ID do post (para comentários)
            comment_id: ID do comentário

        Returns:
            Tupla (ChatResponse, RequestContext) com resposta e contexto de auditoria
        """
        # Inicializa contexto
        ctx = RequestContext(
            request_id=str(uuid4()),
            external_message_id=request.external_message_id,
            session_id=request.session_id,
            surface=request.surface_type,
            channel=request.channel,
            user_message=request.message,
            thread_id=thread_id,
            post_id=post_id,
            comment_id=comment_id,
        )

        # ========================================
        # 0. ANÁLISE NLP (Sentimento + Normalização)
        # ========================================
        # Normaliza mensagem
        normalized_message = normalize_text(request.message)

        # Detecta formalidade do usuário
        formality = detect_formality_level(request.message)
        ctx.user_formality = formality.value

        # Analisa sentimento
        sentiment_result = analyze_sentiment(request.message)
        ctx.sentiment = sentiment_result.sentiment.value
        ctx.emotion = sentiment_result.emotion.value
        ctx.needs_empathy = sentiment_result.needs_empathy
        ctx.is_vulnerable = sentiment_result.is_vulnerable
        ctx.tone_suggestion = sentiment_result.tone_suggestion

        # ========================================
        # 1. CLASSIFICAÇÃO
        # ========================================
        classifier_result = await self.classifier.classify(normalized_message)
        ctx.classifier_result = classifier_result
        ctx.intent = classifier_result.intent
        ctx.confidence = classifier_result.confidence

        ctx.add_event(
            AuditEventType.CLASSIFIER_RESULT,
            {
                "intent": classifier_result.intent.value,
                "confidence": classifier_result.confidence,
                "raw_output": classifier_result.raw_output,
                "sentiment": sentiment_result.sentiment.value,
                "emotion": sentiment_result.emotion.value,
                "formality": formality.value,
                "needs_empathy": sentiment_result.needs_empathy,
            },
        )

        # ========================================
        # 2. POLICY PRE (primeira avaliação sem RAG)
        # ========================================
        policy_pre = self.policy_guard.evaluate_pre(
            message=request.message,
            surface=request.surface_type,
            intent=classifier_result.intent,
            docs_found=None,  # Ainda não sabemos
        )
        ctx.policy_pre = policy_pre
        ctx.policy_decision_pre = policy_pre.policy_decision

        ctx.add_event(
            AuditEventType.POLICY_PRE,
            {
                "policy_decision": policy_pre.policy_decision.value,
                "reason": policy_pre.reason.value,
                "allowed_content": policy_pre.allowed_content,
            },
        )

        # ========================================
        # 3. DECISÃO BASEADA EM POLICY PRE
        # ========================================

        # NO_REPLY: silêncio total
        if policy_pre.policy_decision == PolicyDecision.NO_REPLY:
            return self._build_no_reply_response(ctx)

        # BLOCK: resposta de bloqueio
        if policy_pre.policy_decision == PolicyDecision.BLOCK:
            if policy_pre.reason == PolicyReason.CRISIS_SUICIDE:
                return self._build_crisis_response(ctx, "crisis_suicide")
            if policy_pre.reason == PolicyReason.CRISIS_VIOLENCE:
                return self._build_crisis_response(ctx, "crisis_violence")
            return self._build_blocked_response(ctx)

        # REDIRECT (público): resposta de redirecionamento
        if policy_pre.policy_decision == PolicyDecision.REDIRECT:
            return self._build_redirect_response(ctx)

        # ALLOW_LIMITED (inbox): resposta limitada com contato
        # Usado para saúde clínica em inbox - responde só com direcionamento
        if policy_pre.policy_decision == PolicyDecision.ALLOW_LIMITED:
            return await self._build_health_contact_only_response(ctx)

        # ========================================
        # 4. VERIFICAR INTENTS ESPECIAIS
        # ========================================

        # GREETING: resposta direta
        if classifier_result.intent == Intent.GREETING:
            return self._build_greeting_response(ctx)

        # COMPLIMENT em público: ACK
        if classifier_result.intent == Intent.COMPLIMENT:
            if request.surface_type == SurfaceType.PUBLIC_COMMENT:
                return self._build_public_ack_response(ctx)
            # Em privado, pode agradecer normalmente
            return self._build_direct_response(ctx, load_prompt("greeting"))

        # HUMAN_HANDOFF: escalate
        if classifier_result.intent == Intent.HUMAN_HANDOFF:
            return self._build_escalate_response(ctx)

        # ========================================
        # 5. EXECUTAR RAG (com query expandida)
        # ========================================
        # Expande query com sinônimos para melhor recuperação
        expanded_query = expand_query(request.message)
        ctx.expanded_query = expanded_query

        rag_result = await self._execute_rag(ctx, expanded_query, policy_pre)

        # Se RAG não encontrou docs
        if not rag_result.docs_found:
            # Reavalia policy com docs_found=False
            policy_pre_updated = self.policy_guard.evaluate_pre(
                message=request.message,
                surface=request.surface_type,
                intent=classifier_result.intent,
                docs_found=False,
            )

            if policy_pre_updated.policy_decision == PolicyDecision.REDIRECT:
                return self._build_redirect_response(ctx)

            return await self._build_fallback_response(
                ctx, FallbackReason.NO_DOCS_FOUND
            )

        # ========================================
        # 6. GERAR RESPOSTA RAG
        # ========================================
        # Usa query expandida para melhor recuperação de contexto
        rag_response = await self.composer.compose(expanded_query)

        if self._is_no_answer(rag_response.answer):
            return await self._build_fallback_response(
                ctx, FallbackReason.LOW_CONFIDENCE
            )

        if not rag_response.has_answer:
            return await self._build_fallback_response(
                ctx, FallbackReason.LOW_CONFIDENCE
            )

        # ========================================
        # 7. POLICY POST (valida resposta)
        # ========================================
        policy_post = self.policy_guard.evaluate_post(
            response_text=rag_response.answer,
            policy_pre=policy_pre,
        )
        ctx.policy_post = policy_post

        ctx.add_event(
            AuditEventType.POLICY_POST,
            {
                "no_clinical_advice": policy_post.no_clinical_advice,
                "content_validated": policy_post.content_validated,
            },
        )

        # Se resposta não passou na validação pós
        if not policy_post.content_validated:
            # Saúde clínica: retorna apenas contato
            if policy_pre.policy_decision == PolicyDecision.ALLOW_LIMITED:
                return await self._build_health_contact_only_response(ctx)
            return await self._build_fallback_response(
                ctx, FallbackReason.POLICY_BLOCKED
            )

        # ========================================
        # 8. RESPOSTA RAG SUCCESS
        # ========================================
        response, ctx = self._build_rag_success_response(
            ctx, rag_response.answer, rag_response.sources
        )

        # ========================================
        # 9. REGISTRA ANALYTICS
        # ========================================
        QueryAnalytics.log_query(ctx, response)

        return response, ctx

    async def _execute_rag(
        self,
        ctx: RequestContext,
        query: str,
        policy_pre: PolicyPreResult,
    ) -> RAGRetrieveResult:
        """Executa busca RAG e registra evento."""

        retrieval = await self.retriever.retrieve(query)

        query_hash = hashlib.md5(query.encode()).hexdigest()[:16]

        rag_result = RAGRetrieveResult(
            base_id=settings.RAG_BASE_ID,
            query_id=str(uuid4()),
            query_text_hash=query_hash,
            k=len(retrieval.chunks),
            docs_count=len(retrieval.chunks),
            docs_found=retrieval.has_results,
            doc_ids=[c.id for c in retrieval.chunks],
            source_refs=[f"{c.title} > {c.section}" for c in retrieval.chunks],
            best_score=retrieval.best_score,
        )

        ctx.rag_retrieve = rag_result
        ctx.base_id = rag_result.base_id
        ctx.docs_found = rag_result.docs_found

        ctx.add_event(
            AuditEventType.RAG_RETRIEVE,
            {
                "base_id": rag_result.base_id,
                "query_id": rag_result.query_id,
                "k": rag_result.k,
                "docs_count": rag_result.docs_count,
                "docs_found": rag_result.docs_found,
                "best_score": rag_result.best_score,
            },
        )

        return rag_result

    def _build_no_reply_response(
        self, ctx: RequestContext
    ) -> tuple[ChatResponse, RequestContext]:
        """Constrói resposta NO_REPLY (silêncio)."""
        ctx.final_decision = Decision.NO_REPLY
        ctx.response_type = ResponseType.NO_REPLY

        ctx.response_selected = ResponseSelectedResult(
            template="none",
            decision=Decision.NO_REPLY,
            response_type=ResponseType.NO_REPLY,
        )

        ctx.add_event(
            AuditEventType.RESPONSE_SELECTED,
            {
                "template": "none",
                "decision": Decision.NO_REPLY.value,
                "response_type": ResponseType.NO_REPLY.value,
            },
        )

        # NÃO adiciona MESSAGE_SENT (assert de ausência)
        # Persiste auditoria em background
        ctx.response_message = ""
        asyncio.create_task(self._persist_audit(ctx))

        return ChatResponse(
            session_id=ctx.session_id,
            message="",  # Sem mensagem
            intent=ctx.intent or Intent.OUT_OF_SCOPE,
            decision=Decision.NO_REPLY,
            response_type=ResponseType.NO_REPLY,
            channel=ctx.channel,
            surface_type=ctx.surface,
        ), ctx

    def _build_blocked_response(
        self, ctx: RequestContext
    ) -> tuple[ChatResponse, RequestContext]:
        """
        Constrói resposta BLOCKED.

        Para mensagens privadas com conteúdo proibido, direciona para Ouvidoria.
        Para comentários públicos, redireciona para inbox sem expor contatos.
        """
        if ctx.surface == SurfaceType.PUBLIC_COMMENT:
            message = load_prompt("public_redirect")
            template = "public_redirect.txt"
        else:
            # Em mensagens privadas: direciona para Ouvidoria
            message = load_prompt("ouvidoria_redirect")
            template = "ouvidoria_redirect.txt"

        ctx.final_decision = Decision.BLOCK
        ctx.response_type = ResponseType.BLOCKED

        ctx.response_selected = ResponseSelectedResult(
            template=template,
            decision=Decision.BLOCK,
            response_type=ResponseType.BLOCKED,
        )

        ctx.add_event(
            AuditEventType.RESPONSE_SELECTED,
            {
                "template": template,
                "decision": Decision.BLOCK.value,
            },
        )

        self._add_message_sent_event(ctx, message)
        ctx.response_message = message
        asyncio.create_task(self._persist_audit(ctx))

        return ChatResponse(
            session_id=ctx.session_id,
            message=message,
            intent=ctx.intent or Intent.OUT_OF_SCOPE,
            decision=Decision.BLOCK,
            response_type=ResponseType.BLOCKED,
            channel=ctx.channel,
            surface_type=ctx.surface,
        ), ctx

    def _build_crisis_response(
        self, ctx: RequestContext, template_name: str
    ) -> tuple[ChatResponse, RequestContext]:
        """
        Constrói resposta de CRISE (Suicídio/Violência).
        Usa template estático e registra evento de bloqueio por segurança.
        """
        message = load_prompt(template_name)

        ctx.final_decision = Decision.BLOCK
        ctx.response_type = ResponseType.BLOCKED

        ctx.response_selected = ResponseSelectedResult(
            template=f"{template_name}.txt",
            decision=Decision.BLOCK,
            response_type=ResponseType.BLOCKED,
        )

        ctx.add_event(
            AuditEventType.RESPONSE_SELECTED,
            {
                "template": f"{template_name}.txt",
                "decision": Decision.BLOCK.value,
                "crisis_type": template_name,
            },
        )

        self._add_message_sent_event(ctx, message)
        ctx.response_message = message
        asyncio.create_task(self._persist_audit(ctx))

        return ChatResponse(
            session_id=ctx.session_id,
            message=message,
            intent=ctx.intent or Intent.OUT_OF_SCOPE,
            decision=Decision.BLOCK,
            response_type=ResponseType.BLOCKED,
            channel=ctx.channel,
            surface_type=ctx.surface,
        ), ctx

    def _build_redirect_response(
        self, ctx: RequestContext
    ) -> tuple[ChatResponse, RequestContext]:
        """Constrói resposta PUBLIC_REDIRECT."""
        message = load_prompt("public_redirect")

        ctx.final_decision = Decision.PUBLIC_REDIRECT
        ctx.response_type = ResponseType.SUCCESS

        ctx.response_selected = ResponseSelectedResult(
            template="public_redirect.txt",
            decision=Decision.PUBLIC_REDIRECT,
            response_type=ResponseType.SUCCESS,
        )

        ctx.add_event(
            AuditEventType.RESPONSE_SELECTED,
            {
                "template": "public_redirect.txt",
                "decision": Decision.PUBLIC_REDIRECT.value,
            },
        )

        self._add_message_sent_event(ctx, message)
        ctx.response_message = message
        asyncio.create_task(self._persist_audit(ctx))

        return ChatResponse(
            session_id=ctx.session_id,
            message=message,
            intent=ctx.intent or Intent.OUT_OF_SCOPE,
            decision=Decision.PUBLIC_REDIRECT,
            response_type=ResponseType.SUCCESS,
            channel=ctx.channel,
            surface_type=ctx.surface,
        ), ctx

    def _build_greeting_response(
        self, ctx: RequestContext
    ) -> tuple[ChatResponse, RequestContext]:
        """Constrói resposta de saudação."""
        message = load_prompt("greeting")

        ctx.final_decision = Decision.ANSWER_DIRECT
        ctx.response_type = ResponseType.SUCCESS

        ctx.response_selected = ResponseSelectedResult(
            template="greeting.txt",
            decision=Decision.ANSWER_DIRECT,
            response_type=ResponseType.SUCCESS,
        )

        ctx.add_event(
            AuditEventType.RESPONSE_SELECTED,
            {
                "template": "greeting.txt",
                "decision": Decision.ANSWER_DIRECT.value,
            },
        )

        self._add_message_sent_event(ctx, message)
        ctx.response_message = message
        asyncio.create_task(self._persist_audit(ctx))

        return ChatResponse(
            session_id=ctx.session_id,
            message=message,
            intent=Intent.GREETING,
            decision=Decision.ANSWER_DIRECT,
            response_type=ResponseType.SUCCESS,
            channel=ctx.channel,
            surface_type=ctx.surface,
        ), ctx

    def _build_public_ack_response(
        self, ctx: RequestContext
    ) -> tuple[ChatResponse, RequestContext]:
        """Constrói resposta PUBLIC_ACK com controle de não-repetição."""

        # Chave para controle de repetição
        thread_key = ctx.thread_id or ctx.post_id or ctx.session_id

        # Obtém ACK evitando repetição
        message, choice_id = get_public_ack(thread_key)

        ctx.final_decision = Decision.PUBLIC_ACK
        ctx.response_type = ResponseType.SUCCESS

        ctx.public_ack = PublicAckResult(
            choice_id=choice_id,
            thread_id=ctx.thread_id,
            post_id=ctx.post_id,
        )

        ctx.response_selected = ResponseSelectedResult(
            template="public_ack.txt",
            decision=Decision.PUBLIC_ACK,
            response_type=ResponseType.SUCCESS,
        )

        ctx.add_event(
            AuditEventType.RESPONSE_SELECTED,
            {
                "template": "public_ack.txt",
                "decision": Decision.PUBLIC_ACK.value,
            },
        )

        ctx.add_event(
            AuditEventType.PUBLIC_ACK,
            {
                "choice_id": choice_id,
                "thread_id": ctx.thread_id,
                "post_id": ctx.post_id,
            },
        )

        self._add_message_sent_event(ctx, message)
        ctx.response_message = message
        asyncio.create_task(self._persist_audit(ctx))

        return ChatResponse(
            session_id=ctx.session_id,
            message=message,
            intent=Intent.COMPLIMENT,
            decision=Decision.PUBLIC_ACK,
            response_type=ResponseType.SUCCESS,
            channel=ctx.channel,
            surface_type=ctx.surface,
        ), ctx

    def _build_escalate_response(
        self, ctx: RequestContext
    ) -> tuple[ChatResponse, RequestContext]:
        """Constrói resposta ESCALATE."""
        message = load_prompt("escalate")

        ctx.final_decision = Decision.ESCALATE
        ctx.response_type = ResponseType.ESCALATED

        ctx.response_selected = ResponseSelectedResult(
            template="escalate.txt",
            decision=Decision.ESCALATE,
            response_type=ResponseType.ESCALATED,
        )

        ctx.add_event(
            AuditEventType.RESPONSE_SELECTED,
            {
                "template": "escalate.txt",
                "decision": Decision.ESCALATE.value,
            },
        )

        self._add_message_sent_event(ctx, message)
        ctx.response_message = message
        asyncio.create_task(self._persist_audit(ctx))

        return ChatResponse(
            session_id=ctx.session_id,
            message=message,
            intent=Intent.HUMAN_HANDOFF,
            decision=Decision.ESCALATE,
            response_type=ResponseType.ESCALATED,
            channel=ctx.channel,
            surface_type=ctx.surface,
        ), ctx

    async def _execute_hybrid_web_fallback(self, ctx: RequestContext, reason: FallbackReason) -> Optional[tuple[ChatResponse, RequestContext]]:
        """Tenta responder à pergunta raspando o site de fallback."""
        import os
        import re
        from google import genai
        from google.genai.errors import APIError
        from app.scraper.service import get_scraper_service
        
        try:
            scraper = get_scraper_service()
            
            # Executa com timeout rigoroso para não parar a resposta do usuário
            try:
                result = await asyncio.wait_for(
                    scraper.preview_url(settings.FALLBACK_TARGET_URL), 
                    timeout=settings.FALLBACK_WEB_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                logger.warning(f"Fallback Web timeout excedido ({settings.FALLBACK_WEB_TIMEOUT_SECONDS}s). Escalonando.")
                return None
                
            body_html = result.get('body_html', '')
            texto_limpo = re.sub('<.*?>', ' ', body_html)
            texto_limpo = ' '.join(texto_limpo.split())
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("No API KEY for Fallback Web")
                return None
                
            client = genai.Client(api_key=api_key)
            prompt = f"""Você é o "Robot", assistente de atendimento da Prefeitura.
Leia o texto raspado do site abaixo e responda APENAS SE a resposta estiver EXPLICITAMENTE lá.
Se a informação não estiver no texto, responda EXATAMENTE com a palavra: INCONCLUSIVO
Não invente, não deduza e não use conhecimentos externos. Seja breve e direto.

--- TEXTO DO SITE DA PREFEITURA ---
Título: {result.get('title', 'Sem título')}
Conteúdo Extraído:
{texto_limpo[:80000]}
---

Pergunta do cidadão: "{ctx.user_message}"
Sua resposta (ou a palavra INCONCLUSIVO):
"""
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
            
            if response.text and response.text.strip().upper() != "INCONCLUSIVO":
                message = response.text.strip()
                
                ctx.final_decision = Decision.ANSWER_RAG
                ctx.response_type = ResponseType.SUCCESS
                ctx.fallback_used = True
                
                ctx.response_selected = ResponseSelectedResult(
                    template="web_fallback",
                    decision=Decision.ANSWER_RAG,
                    response_type=ResponseType.SUCCESS,
                    fallback_reason=reason
                )

                ctx.add_event(
                    AuditEventType.RESPONSE_SELECTED,
                    {
                        "template": "web_fallback",
                        "decision": Decision.ANSWER_RAG.value,
                        "fallback_reason": reason.value,
                    },
                )
                
                self._add_message_sent_event(ctx, message)
                ctx.response_message = message
                asyncio.create_task(self._persist_audit(ctx))
                
                return ChatResponse(
                    session_id=ctx.session_id,
                    message=message,
                    intent=ctx.intent or Intent.INFO_REQUEST,
                    decision=Decision.ANSWER_RAG,
                    response_type=ResponseType.SUCCESS,
                    channel=ctx.channel,
                    surface_type=ctx.surface,
                    base_id="WEB_SCRAPER",
                    docs_found=True,
                    sources=[settings.FALLBACK_TARGET_URL],
                    fallback_used=True,
                    fallback_reason=reason
                ), ctx
                
        except Exception as e:
            logger.error(f"Error in hybrid web fallback: {e}")
            
        return None

    async def _build_fallback_response(
        self,
        ctx: RequestContext,
        reason: FallbackReason,
    ) -> tuple[ChatResponse, RequestContext]:
        """Constrói resposta FALLBACK com tentativa de Scraping e Escalation."""

        # 1. PUBLIC_COMMENT: Redireciona para inbox (não expõe que não sabe)
        if ctx.surface == SurfaceType.PUBLIC_COMMENT:
            message = load_prompt("public_redirect")
            ctx.final_decision = Decision.PUBLIC_REDIRECT
            ctx.response_type = ResponseType.SUCCESS

            ctx.response_selected = ResponseSelectedResult(
                template="public_redirect.txt",
                decision=Decision.PUBLIC_REDIRECT,
                response_type=ResponseType.SUCCESS,
            )

            ctx.add_event(
                AuditEventType.RESPONSE_SELECTED,
                {
                    "template": "public_redirect.txt",
                    "decision": Decision.PUBLIC_REDIRECT.value,
                },
            )

            self._add_message_sent_event(ctx, message)
            ctx.response_message = message
            asyncio.create_task(self._persist_audit(ctx))

            return ChatResponse(
                session_id=ctx.session_id,
                message=message,
                intent=ctx.intent or Intent.OUT_OF_SCOPE,
                decision=Decision.PUBLIC_REDIRECT,
                response_type=ResponseType.SUCCESS,
                channel=ctx.channel,
                surface_type=ctx.surface,
                fallback_used=True,
                fallback_reason=reason,
            ), ctx

        # 1.5. Tentativa de Resposta via Web Scraping (Fallback Hybrid)
        if (
            settings.FALLBACK_HYBRID_ENABLED
            and reason != FallbackReason.POLICY_BLOCKED
            and ctx.intent != Intent.OUT_OF_SCOPE
            and ctx.surface != SurfaceType.PUBLIC_COMMENT
        ):
            hybrid_response = await self._execute_hybrid_web_fallback(ctx, reason)
            if hybrid_response:
                return hybrid_response

        # 2. Escalation por Email (apenas se não for bloqueio de policy e não for OUT_OF_SCOPE)
        # Apenas se não for OUT_OF_SCOPE e não for POLICY_BLOCKED
        if (
            reason != FallbackReason.POLICY_BLOCKED
            and ctx.intent != Intent.OUT_OF_SCOPE
        ):
            # Determina a plataforma e o ID do usuário
            platform = "web"
            user_id = ctx.session_id

            if (
                ctx.channel == Channel.INSTAGRAM_DM
                or ctx.channel == Channel.INSTAGRAM_COMMENT
            ):
                platform = "instagram"
                # Extrai o sender_id do session_id (formato: sender_id ou sender_id_comment_id)
                user_id = ctx.session_id.split("_")[0]
            elif (
                ctx.channel == Channel.FACEBOOK_DM
                or ctx.channel == Channel.FACEBOOK_COMMENT
            ):
                platform = "facebook"
                user_id = ctx.session_id.split("_")[0]

            # Busca perfil cacheado ou na API (apenas para Instagram/Facebook)
            profile = None
            if platform in ["instagram", "facebook"]:
                # Tenta buscar do cache primeiro
                profile = await meta_user_profile_repository.get_cached_profile(
                    user_id, platform
                )

                if not profile:
                    logger.info(
                        f"Perfil não encontrado no cache, buscando na API {platform}"
                    )
                    # Busca na API da Meta
                    try:
                        meta_client = get_meta_client(platform=platform)
                        profile_data = await meta_client.get_user_profile(user_id)

                        if profile_data:
                            # Salva no cache
                            create_data = MetaUserProfileCreate(
                                platform_user_id=user_id,
                                platform=platform,
                                username=profile_data.get("username"),
                                name=profile_data.get("name"),
                                profile_picture_url=profile_data.get(
                                    "profile_picture_url"
                                ),
                            )
                            profile = await meta_user_profile_repository.cache_profile(
                                create_data
                            )
                    except Exception as e:
                        logger.error(f"Erro ao buscar perfil na API: {e}")

            # Prepara informações de contato para o email
            if profile:
                user_contact = profile.contact_info
                user_name = profile.name
            else:
                user_contact = f"ID: {user_id}"
                user_name = None

            # Envia email em background com informações do perfil
            asyncio.create_task(
                asyncio.to_thread(
                    self.mailer.send_escalation_email,
                    ctx.user_message,
                    user_contact,
                    platform=platform.upper(),
                    user_name=user_name,
                )
            )

            message = "Não encontrei essa informação na minha base nem no site da Prefeitura. Já notifiquei um atendente humano sobre sua dúvida e eles entrarão em contato em breve."

            ctx.final_decision = Decision.ESCALATE
            ctx.response_type = ResponseType.ESCALATED

            ctx.response_selected = ResponseSelectedResult(
                template="escalation_email_sent",
                decision=Decision.ESCALATE,
                response_type=ResponseType.ESCALATED,
            )

            ctx.add_event(
                AuditEventType.RESPONSE_SELECTED,
                {
                    "template": "escalation_email_sent",
                    "decision": Decision.ESCALATE.value,
                },
            )

            self._add_message_sent_event(ctx, message)
            ctx.response_message = message
            asyncio.create_task(self._persist_audit(ctx))

            return ChatResponse(
                session_id=ctx.session_id,
                message=message,
                intent=ctx.intent,
                decision=Decision.ESCALATE,
                response_type=ResponseType.ESCALATED,
                channel=ctx.channel,
                surface_type=ctx.surface,
            ), ctx

        # 4. Fallback Padrão (Out of scope ou Policy Blocked)
        if ctx.intent == Intent.OUT_OF_SCOPE:
            message = load_prompt("fallback")
        else:
            # Fallback generico
            message = load_prompt("fallback_private")

        ctx.final_decision = Decision.FALLBACK
        ctx.response_type = ResponseType.FALLBACK
        ctx.fallback_used = True

        ctx.response_selected = ResponseSelectedResult(
            template="fallback.txt",
            decision=Decision.FALLBACK,
            response_type=ResponseType.FALLBACK,
            fallback_reason=reason,
        )

        ctx.add_event(
            AuditEventType.RESPONSE_SELECTED,
            {
                "template": "fallback.txt",
                "decision": Decision.FALLBACK.value,
                "fallback_reason": reason.value,
            },
        )

        self._add_message_sent_event(ctx, message)
        ctx.response_message = message
        asyncio.create_task(self._persist_audit(ctx))

        return ChatResponse(
            session_id=ctx.session_id,
            message=message,
            intent=ctx.intent or Intent.OUT_OF_SCOPE,
            decision=Decision.FALLBACK,
            response_type=ResponseType.FALLBACK,
            channel=ctx.channel,
            surface_type=ctx.surface,
            fallback_used=True,
            fallback_reason=reason,
        ), ctx

    def _build_direct_response(
        self,
        ctx: RequestContext,
        message: str,
    ) -> tuple[ChatResponse, RequestContext]:
        """Constrói resposta direta (template)."""
        ctx.final_decision = Decision.ANSWER_DIRECT
        ctx.response_type = ResponseType.SUCCESS

        ctx.response_selected = ResponseSelectedResult(
            template="direct",
            decision=Decision.ANSWER_DIRECT,
            response_type=ResponseType.SUCCESS,
        )

        ctx.add_event(
            AuditEventType.RESPONSE_SELECTED,
            {
                "template": "direct",
                "decision": Decision.ANSWER_DIRECT.value,
            },
        )

        self._add_message_sent_event(ctx, message)
        ctx.response_message = message
        asyncio.create_task(self._persist_audit(ctx))

        return ChatResponse(
            session_id=ctx.session_id,
            message=message,
            intent=ctx.intent or Intent.INFO_REQUEST,
            decision=Decision.ANSWER_DIRECT,
            response_type=ResponseType.SUCCESS,
            channel=ctx.channel,
            surface_type=ctx.surface,
        ), ctx

    async def _build_health_contact_only_response(
        self,
        ctx: RequestContext,
    ) -> tuple[ChatResponse, RequestContext]:
        """Constroi resposta limitada para saude clinica (apenas contato)."""

        message = """Para atendimento de saude, entre em contato com a Central de Saude:

Saude (Central): (45) 3124-1020 | Av. Brasilia, 525

Em caso de emergencia, ligue 192 (SAMU).

Sou uma IA em treinamento. Informacoes baseadas na base oficial. Para decisoes legais, consulte o Diario Oficial."""

        ctx.final_decision = Decision.ANSWER_RAG
        ctx.response_type = ResponseType.SUCCESS

        ctx.response_selected = ResponseSelectedResult(
            template="health_contact_only",
            decision=Decision.ANSWER_RAG,
            response_type=ResponseType.SUCCESS,
        )

        ctx.add_event(
            AuditEventType.RESPONSE_SELECTED,
            {
                "template": "health_contact_only",
                "decision": Decision.ANSWER_RAG.value,
                "health_limited": True,
            },
        )

        self._add_message_sent_event(ctx, message)
        ctx.response_message = message
        asyncio.create_task(self._persist_audit(ctx))

        return ChatResponse(
            session_id=ctx.session_id,
            message=message,
            intent=ctx.intent or Intent.INFO_REQUEST,
            decision=Decision.ANSWER_RAG,
            response_type=ResponseType.SUCCESS,
            channel=ctx.channel,
            surface_type=ctx.surface,
            base_id=settings.RAG_BASE_ID,
            docs_found=True,
        ), ctx

    def _build_rag_success_response(
        self,
        ctx: RequestContext,
        message: str,
        sources: list[str],
    ) -> tuple[ChatResponse, RequestContext]:
        """Constrói resposta RAG SUCCESS."""
        ctx.final_decision = Decision.ANSWER_RAG
        ctx.response_type = ResponseType.SUCCESS

        ctx.response_selected = ResponseSelectedResult(
            template="rag_answer.txt",
            decision=Decision.ANSWER_RAG,
            response_type=ResponseType.SUCCESS,
        )

        ctx.add_event(
            AuditEventType.RESPONSE_SELECTED,
            {
                "template": "rag_answer.txt",
                "decision": Decision.ANSWER_RAG.value,
            },
        )

        self._add_message_sent_event(ctx, message)
        ctx.response_message = message
        asyncio.create_task(self._persist_audit(ctx))

        return ChatResponse(
            session_id=ctx.session_id,
            message=message,
            intent=ctx.intent or Intent.INFO_REQUEST,
            decision=Decision.ANSWER_RAG,
            response_type=ResponseType.SUCCESS,
            channel=ctx.channel,
            surface_type=ctx.surface,
            base_id=settings.RAG_BASE_ID,
            docs_found=True,
            sources=sources,
        ), ctx

    def _add_message_sent_event(self, ctx: RequestContext, message: str) -> None:
        """Adiciona evento MESSAGE_SENT."""
        from datetime import datetime

        ctx.message_sent = MessageSentResult(
            surface=ctx.surface,
            channel=ctx.channel,
            message_length=len(message),
            sent_at=datetime.utcnow(),
        )

        ctx.add_event(
            AuditEventType.MESSAGE_SENT,
            {
                "surface": ctx.surface.value,
                "channel": ctx.channel.value,
                "message_length": len(message),
            },
        )

    def _is_no_answer(self, text: str) -> bool:
        """Detecta respostas vazias/negativas para acionar fallback."""
        if not text:
            return True
        lowered = text.lower()
        patterns = [
            "nao encontrei",
            "não encontrei",
            "nao tenho essa informacao",
            "não tenho essa informação",
            "nao foi possivel encontrar",
            "não foi possível encontrar",
            "nao localizei",
            "não localizei",
        ]
        return any(p in lowered for p in patterns)

    async def _persist_audit(self, ctx: RequestContext) -> None:
        """Persiste auditoria (audit_events e rag_queries) no PostgreSQL."""
        try:
            # Monta evento principal
            fallback_reason = None
            if ctx.response_selected and ctx.response_selected.fallback_reason:
                fallback_reason = ctx.response_selected.fallback_reason

            block_reason = None
            if ctx.policy_pre and ctx.policy_decision_pre in {
                PolicyDecision.BLOCK,
                PolicyDecision.NO_REPLY,
            }:
                block_reason = ctx.policy_pre.reason.value

            user_id = await audit_repository.get_or_create_user_id(ctx.session_id)

            event = AuditEventCreate(
                id_requisicao=UUID(ctx.request_id),
                id_sessao=ctx.session_id,
                id_usuario=user_id,
                canal=ctx.channel,
                tipo_superficie=ctx.surface,
                id_mensagem_externa=ctx.external_message_id,
                id_thread=ctx.thread_id,
                id_post=ctx.post_id,
                id_comentario=ctx.comment_id,
                id_autor_plataforma=None,
                intencao=ctx.intent or Intent.OUT_OF_SCOPE,
                confianca_classificador=Decimal(str(ctx.confidence))
                if ctx.confidence is not None
                else None,
                decisao_politica=ctx.policy_decision_pre or PolicyDecision.ALLOW,
                motivo_bloqueio=block_reason,
                id_regra_bloqueio=None,
                decisao=ctx.final_decision or Decision.FALLBACK,
                tipo_resposta=ctx.response_type or ResponseType.SUCCESS,
                motivo_fallback=fallback_reason,
                id_base=ctx.base_id,
                modelo=settings.GEMINI_MODEL,
                temperatura=Decimal(str(settings.GEMINI_TEMPERATURE))
                if settings.GEMINI_TEMPERATURE is not None
                else None,
                versao_prompt=None,
                tempo_resposta_ms=None,
                codigo_erro=None,
                tipo_excecao=None,
                versao_app=settings.VERSION,
            )

            rag_q = None
            if ctx.rag_retrieve is not None:
                rr = ctx.rag_retrieve
                rag_q = RAGQueryCreate(
                    id_requisicao=UUID(ctx.request_id),
                    id_base=rr.base_id,
                    tipo_superficie=ctx.surface,
                    texto_consulta=ctx.expanded_query or ctx.user_message,
                    modelo_embedding=None,
                    top_k=rr.k,
                    documentos_recuperados=None,
                    quantidade_documentos=rr.docs_count,
                    melhor_score=Decimal(str(rr.best_score))
                    if rr.best_score is not None
                    else None,
                    sem_documentos=not rr.docs_found,
                    tempo_busca_ms=None,
                )

            conversa = ConversaCreate(
                id_requisicao=UUID(ctx.request_id),
                id_usuario=user_id,
                canal=ctx.channel,
                tipo_superficie=ctx.surface,
                mensagem_usuario=ctx.user_message,
                mensagem_resposta=ctx.response_message,
                tamanho_mensagem=len(ctx.user_message) if ctx.user_message else None,
                tamanho_resposta=len(ctx.response_message)
                if ctx.response_message
                else None,
                intencao=ctx.intent or Intent.OUT_OF_SCOPE,
                decisao=ctx.final_decision or Decision.FALLBACK,
                tipo_resposta=ctx.response_type or ResponseType.SUCCESS,
                motivo_fallback=fallback_reason,
                motivo_politica=ctx.policy_pre.reason.value if ctx.policy_pre else None,
                sentimento=ctx.sentiment,
                emocao=ctx.emotion,
                formalidade=ctx.user_formality,
                consulta_expandida=ctx.expanded_query,
                encontrou_docs=ctx.rag_retrieve.docs_found
                if ctx.rag_retrieve
                else None,
                melhor_score=Decimal(str(ctx.rag_retrieve.best_score))
                if ctx.rag_retrieve and ctx.rag_retrieve.best_score is not None
                else None,
                fontes=ctx.rag_retrieve.source_refs if ctx.rag_retrieve else None,
                modelo=settings.GEMINI_MODEL,
                temperatura=Decimal(str(settings.GEMINI_TEMPERATURE))
                if settings.GEMINI_TEMPERATURE is not None
                else None,
            )

            await audit_repository.insert_audit_with_rag(event, rag_q, conversa)
        except Exception as e:
            # Evita quebrar o fluxo principal por erro de auditoria
            import logging

            logging.getLogger(__name__).warning(f"Falha ao persistir auditoria: {e}")


# Instância padrão
_default_orchestrator: Optional[OrchestratorService] = None


def get_orchestrator() -> OrchestratorService:
    """Retorna instância padrão do orchestrator."""
    global _default_orchestrator
    if _default_orchestrator is None:
        _default_orchestrator = OrchestratorService()
    return _default_orchestrator


async def process(
    request: ChatRequest, **kwargs
) -> tuple[ChatResponse, RequestContext]:
    """Atalho para processamento."""
    return await get_orchestrator().process(request, **kwargs)
