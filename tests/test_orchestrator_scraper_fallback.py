import asyncio
import os
import sys
from dotenv import load_dotenv

# Configura o path para encontrar o app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from app.contracts.dto import ChatRequest  # noqa: E402
from app.contracts.enums import SurfaceType, Channel  # noqa: E402
from app.orchestrator.service import get_orchestrator  # noqa: E402
from app.settings import settings  # noqa: E402

async def main():
    print("=============================================")
    print("   TESTE DE FALLBACK WEB (Scraping) MVP    ")
    print("=============================================")
    
    # Configura para forçar o fallback web via script (se já não estiver True no .env)
    settings.FALLBACK_HYBRID_ENABLED = True
    
    # 1. Pede a pergunta ao usuário
    pergunta = input("\nDigite uma pergunta (tente algo que SÓ tenha no mural de notícias da Prefeitura, ex: 'Quando é a festa do milho?'):\n> ").strip()
    
    if not pergunta:
        print("Pergunta vazia. Fim.")
        return

    # 2. Cria o Request 
    # Usamos uma Intent que normalmente ativaria RAG, como INFO_REQUEST
    # Mas se a base não tiver, o Orchestrator service fará Fallback -> Web Scraping
    request = ChatRequest(
        pergunta=pergunta,
        sessao_id="test_scraper_fallback_001",
        canal="whatsapp",
        origem="script_teste"
    )
    
    # Aqui precisamos simular que RAG e Intent falharam ou passaram direto
    # Como rodar `process()` completo exige banco e chaves OpenAI/etc configurados para RAG
    # Nós vamos "Injetar" um contexto para testar APENAS o Call de Fallback
    from app.contracts.dto import RequestContext
    from app.contracts.enums import Intent, FallbackReason
    from uuid import uuid4
    
    ctx = RequestContext(
        session_id=request.sessao_id,
        user_message=request.pergunta,
        channel=Channel.WHATSAPP,
        surface=SurfaceType.PRIVATE_DM,
        intent=Intent.INFO_REQUEST,  # Simula que é uma dúvida genérica
        request_id=str(uuid4())
    )
    
    orchestrator = get_orchestrator()
    print("\nExecutando Fallback Híbrido Web...")
    print(f"URL Alvo: {settings.FALLBACK_TARGET_URL}")
    print(f"Timeout: {settings.FALLBACK_WEB_TIMEOUT_SECONDS}s")
    
    # Teste direto do método protegido para pular o pipeline de segurança que exige banco
    try:
        response_tuple = await orchestrator._execute_hybrid_web_fallback(ctx, FallbackReason.LOW_CONFIDENCE)
        
        if response_tuple:
            chat_resp, out_ctx = response_tuple
            print("\n================ RESULTADO ================")
            print("[SUCESSO] O Bot Respondeu usando Web Scraping!")
            print(f"Decisão: {out_ctx.final_decision}")
            print(f"Texto da Resposta:\n{chat_resp.message}")
            print("===========================================")
        else:
            print("\n================ RESULTADO ================")
            print("[FALHA] O Bot retornou None. O Scraping falhou ou o Gemini respondeu 'INCONCLUSIVO'.")
            print("Neste cenário, o Orchestrator encaminhará para Escalation Humano.")
            print("===========================================")
            
    except Exception as e:
        print(f"\n[ERRO FATAL] Algo deu errado no teste:\n{str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
