"""
RAG Composer - Monta o contexto e gera resposta usando LLM.

Responsabilidades:
- Receber query e chunks do retriever
- Montar prompt com contexto estruturado
- Chamar LLM para gerar resposta
- Aplicar políticas de resposta (tamanho, formato)
"""

from dataclasses import dataclass
from typing import Optional

from google import genai
from google.genai import types

from app.prompts import load_prompt
from app.rag.retriever import RAGRetriever, RetrievalResult, get_retriever
from app.settings import settings


@dataclass
class RAGResponse:
    """Resposta gerada pelo RAG."""

    answer: str
    query: str
    retrieval: RetrievalResult
    model: str
    tokens_used: int
    confidence: str  # "high", "medium", "low", "none"
    sources: list[str]

    @property
    def has_answer(self) -> bool:
        return self.confidence != "none" and bool(self.answer)

    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "query": self.query,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "confidence": self.confidence,
            "sources": self.sources,
            "retrieval": self.retrieval.to_dict(),
        }


class RAGComposer:
    """
    Compositor RAG que orquestra retrieval + LLM.

    Pipeline:
    1. Recebe query do usuário
    2. Busca chunks relevantes via Retriever
    3. Monta prompt com contexto
    4. Chama LLM para gerar resposta
    5. Avalia confiança e retorna resultado
    """

    def __init__(
        self,
        retriever: Optional[RAGRetriever] = None,
        model: Optional[str] = None,
        max_context_chunks: int = 5,
        min_confidence_score: float = 0.4,
    ):
        """
        Args:
            retriever: Instância do retriever (usa padrão se None)
            model: Modelo Gemini a usar (usa config admin se None)
            max_context_chunks: Máximo de chunks no contexto
            min_confidence_score: Score mínimo para considerar confiável
        """
        self.retriever = retriever or get_retriever()

        # Use effective config (from admin panel) or fallback to settings
        if model is None:
            from app.settings import get_effective_rag_config

            effective_config = get_effective_rag_config()
            self.model = effective_config.get("model", settings.GEMINI_MODEL)
        else:
            self.model = model

        self.max_context_chunks = max_context_chunks
        self.min_confidence_score = min_confidence_score
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        """Obtém cliente Gemini."""
        if self._client is None:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def _evaluate_confidence(self, retrieval: RetrievalResult) -> str:
        """
        Avalia nível de confiança baseado nos resultados do retrieval.

        Thresholds ajustados para assertividade (v0.7.1):
        - Score > 0.6 com múltiplos chunks = high
        - Score > 0.4 = medium (suficiente para responder)
        - Score > min_confidence = low (ainda usável)

        Returns:
            "high": Score > 0.6, múltiplos chunks relevantes
            "medium": Score > 0.4, pelo menos 1 chunk bom
            "low": Score > min_confidence, resultados marginais
            "none": Sem resultados úteis
        """
        if not retrieval.has_results:
            return "none"

        best = retrieval.best_score
        num_good = sum(1 for c in retrieval.chunks if c.score > 0.4)

        if best > 0.6 and num_good >= 2:
            return "high"
        elif best > 0.4:
            return "medium"
        elif best > self.min_confidence_score:
            return "low"
        else:
            return "none"

    def _build_context(self, retrieval: RetrievalResult) -> str:
        """Monta contexto a partir dos chunks recuperados."""
        if not retrieval.has_results:
            return "Nenhuma informação relevante encontrada na base de conhecimento."

        return retrieval.context_text

    def _extract_sources(self, retrieval: RetrievalResult) -> list[str]:
        """Extrai lista de fontes únicas dos chunks."""
        sources = set()
        for chunk in retrieval.chunks:
            source = chunk.title
            if chunk.section:
                source = f"{chunk.title} > {chunk.section}"
            sources.add(source)
        return sorted(sources)

    async def compose(
        self,
        query: str,
        filter_tags: Optional[list[str]] = None,
        system_context: Optional[str] = None,
    ) -> RAGResponse:
        """
        Executa pipeline RAG completo.

        Args:
            query: Pergunta do usuário
            filter_tags: Tags para filtrar busca
            system_context: Contexto adicional do sistema

        Returns:
            RAGResponse com resposta e metadados
        """
        # 1. Busca chunks relevantes
        retrieval = await self.retriever.retrieve(
            query=query,
            top_k=self.max_context_chunks,
            filter_tags=filter_tags,
        )

        # 2. Avalia confiança
        confidence = self._evaluate_confidence(retrieval)

        # 3. Se não há contexto útil, retorna resposta vazia
        if confidence == "none":
            return RAGResponse(
                answer="",
                query=query,
                retrieval=retrieval,
                model=self.model,
                tokens_used=0,
                confidence=confidence,
                sources=[],
            )

        # 4. Monta contexto
        context = self._build_context(retrieval)
        sources = self._extract_sources(retrieval)

        # 5. Carrega prompts
        system_prompt = load_prompt("system")
        rag_prompt = load_prompt("rag_answer")

        # 6. Monta conteúdo para o LLM
        content_parts = [types.Part.from_text(text=system_prompt)]
        if system_context:
            content_parts.append(
                types.Part.from_text(f"Contexto adicional: {system_context}")
            )
        user_message = rag_prompt.format(
            contexto=context,
            pergunta=query,
        )
        content_parts.append(types.Part.from_text(text=user_message))

        client = self._get_client()
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=[types.Content(role="user", parts=content_parts)],
            config=types.GenerateContentConfig(
                temperature=settings.GEMINI_TEMPERATURE,
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
            ),
        )

        answer = response.text or ""
        tokens_used = (
            response.usage_metadata.total_token_count if response.usage_metadata else 0
        )

        return RAGResponse(
            answer=answer.strip(),
            query=query,
            retrieval=retrieval,
            model=self.model,
            tokens_used=tokens_used,
            confidence=confidence,
            sources=sources,
        )

    async def compose_with_history(
        self,
        query: str,
        history: list[dict],
        filter_tags: Optional[list[str]] = None,
    ) -> RAGResponse:
        """
        Executa RAG considerando histórico de conversa.

        Args:
            query: Pergunta atual
            history: Lista de mensagens anteriores [{"role": "user/assistant", "content": "..."}]
            filter_tags: Tags para filtrar busca
        """
        # Para contexto conversacional, inclui última mensagem no query de busca
        enhanced_query = query
        if history:
            last_exchange = history[-2:] if len(history) >= 2 else history
            context_parts = [m["content"] for m in last_exchange if m["role"] == "user"]
            if context_parts:
                enhanced_query = f"{' '.join(context_parts)} {query}"

        # 1. Busca com query expandida
        retrieval = await self.retriever.retrieve(
            query=enhanced_query,
            top_k=self.max_context_chunks,
            filter_tags=filter_tags,
        )

        # 2. Avalia confiança
        confidence = self._evaluate_confidence(retrieval)

        if confidence == "none":
            return RAGResponse(
                answer="",
                query=query,
                retrieval=retrieval,
                model=self.model,
                tokens_used=0,
                confidence=confidence,
                sources=[],
            )

        # 3. Monta contexto e mensagens
        context = self._build_context(retrieval)
        sources = self._extract_sources(retrieval)

        system_prompt = load_prompt("system")
        rag_prompt = load_prompt("rag_answer")

        # Constrói conteúdo para Gemini
        content_parts = [types.Part.from_text(text=system_prompt)]
        content_parts.append(types.Part.from_text(f"Base de conhecimento:\n{context}"))

        # Adiciona histórico (limitado)
        max_history = 6  # 3 trocas
        for msg in history[-max_history:]:
            role = msg.get("role", "user")
            text = msg.get("content", "")
            if role == "user":
                content_parts.append(types.Part.from_text(f"Usuário: {text}"))
            elif role == "assistant":
                content_parts.append(types.Part.from_text(f"Assistente: {text}"))

        # Query atual formatada
        user_message = rag_prompt.format(
            contexto="(já fornecido acima)",
            pergunta=query,
        )
        content_parts.append(types.Part.from_text(text=user_message))

        client = self._get_client()
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=[types.Content(role="user", parts=content_parts)],
            config=types.GenerateContentConfig(
                temperature=settings.GEMINI_TEMPERATURE,
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
            ),
        )

        answer = response.text or ""
        tokens_used = (
            response.usage_metadata.total_token_count if response.usage_metadata else 0
        )

        return RAGResponse(
            answer=answer.strip(),
            query=query,
            retrieval=retrieval,
            model=self.model,
            tokens_used=tokens_used,
            confidence=confidence,
            sources=sources,
        )


# Instância padrão
_default_composer: Optional[RAGComposer] = None


def get_composer() -> RAGComposer:
    """Retorna instância padrão do composer."""
    global _default_composer
    if _default_composer is None:
        _default_composer = RAGComposer()
    return _default_composer


async def compose(query: str, **kwargs) -> RAGResponse:
    """Atalho para composição rápida."""
    return await get_composer().compose(query, **kwargs)


# CLI para testes
if __name__ == "__main__":
    import asyncio
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("Uso: python -m app.rag.composer '<query>'")
            print(
                "Exemplo: python -m app.rag.composer 'qual o horário de funcionamento?'"
            )
            sys.exit(1)

        query = sys.argv[1]

        print(f"\n🤖 Pergunta: '{query}'")
        print("-" * 50)

        result = await compose(query)

        print(f"📊 Confiança: {result.confidence}")
        print(f"   Modelo: {result.model}")
        print(f"   Tokens: {result.tokens_used}")
        print(f"   Fontes: {result.sources}")
        print()
        print("📝 Resposta:")
        print(result.answer)
        print()
        print("🔍 Chunks utilizados:")
        for i, chunk in enumerate(result.retrieval.chunks, 1):
            print(f"   {i}. {chunk.title} > {chunk.section} (score: {chunk.score:.3f})")

    asyncio.run(main())
