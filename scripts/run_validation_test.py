import asyncio
import os
import sys

# Adiciona o diretório raiz ao path para importar módulos da app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.orchestrator.service import OrchestratorService
from app.contracts.dto import ChatRequest
from app.contracts.enums import Channel, SurfaceType

# Caminho do dataset
DATASET_PATH = "data/datasets/validation_v1.txt"

async def run_tests():
    print("🚀 Iniciando teste de validação...")
    
    # Inicializa orquestrador
    orchestrator = OrchestratorService()
    
    # Lê as perguntas do arquivo
    inbox_questions = []
    public_questions = []
    current_list = None # None antes do primeiro cabeçalho

    try:
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Detecta cabeçalhos/separadores
                if line.lower().startswith("### dataset") or line.lower().startswith("###dataset"):
                    if current_list is None:
                        current_list = inbox_questions # Primeiro bloco -> Inbox
                    else:
                        current_list = public_questions # Segundo bloco -> Público
                    continue
                
                if current_list is not None:
                    current_list.append(line)
                    
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {DATASET_PATH}")
        return

    print(f"📋 Total de perguntas carregadas: {len(inbox_questions) + len(public_questions)}")
    print(f"🔹 Inbox: {len(inbox_questions)} perguntas")
    print(f"🔸 Público: {len(public_questions)} perguntas")
    
    results = []

    # Processa INBOX
    print("\n--- Processando INBOX ---")
    for i, q in enumerate(inbox_questions):
        print(f"[{i+1}/{len(inbox_questions)}] {q}")
        req = ChatRequest(
            session_id=f"test_inbox_{i}",
            message=q,
            channel=Channel.FACEBOOK_DM, # Simulando DM
            surface_type=SurfaceType.INBOX,
            external_message_id=f"msg_inbox_{i}"
        )
        resp, ctx = await orchestrator.process(req)
        results.append({
            "tipo": "INBOX",
            "pergunta": q,
            "resposta": resp.message,
            "decisao": resp.decision.value,
            "tipo_resposta": resp.response_type.value,
            "fallback": resp.fallback_reason.value if resp.fallback_reason else "N/A"
        })
        # Pequeno delay para não sobrecarregar logs
        await asyncio.sleep(0.1)

    # Processa PÚBLICO
    print("\n--- Processando PÚBLICO ---")
    for i, q in enumerate(public_questions):
        print(f"[{i+1}/{len(public_questions)}] {q}")
        req = ChatRequest(
            session_id=f"test_public_{i}",
            message=q,
            channel=Channel.FACEBOOK_COMMENT, # Simulando Comentário
            surface_type=SurfaceType.PUBLIC_COMMENT,
            external_message_id=f"msg_public_{i}"
        )
        resp, ctx = await orchestrator.process(req, post_id="post_123", comment_id=f"comment_{i}")
        results.append({
            "tipo": "PUBLIC",
            "pergunta": q,
            "resposta": resp.message,
            "decisao": resp.decision.value,
            "tipo_resposta": resp.response_type.value,
            "fallback": resp.fallback_reason.value if resp.fallback_reason else "N/A"
        })
        await asyncio.sleep(0.1)

    # Resumo final
    print("\n📊 Resumo do Teste:")
    fallback_count = sum(1 for r in results if r['tipo_resposta'] == 'FALLBACK')
    blocked_count = sum(1 for r in results if r['tipo_resposta'] == 'BLOCKED')
    success_count = sum(1 for r in results if r['tipo_resposta'] == 'SUCCESS')
    
    print(f"✅ Sucesso: {success_count}")
    print(f"⚠️ Fallback: {fallback_count}")
    print(f"🚫 Bloqueado: {blocked_count}")
    
    # Salva relatório simples
    with open("test_output.txt", "w", encoding="utf-8") as f:
        f.write("RELATORIO DE TESTE\n==================\n")
        for r in results:
            f.write(f"[{r['tipo']}] P: {r['pergunta']}\n")
            f.write(f"    R: {r['resposta']}\n")
            f.write(f"    Decisão: {r['decisao']} | Tipo: {r['tipo_resposta']} | Fallback: {r['fallback']}\n")
            f.write("-" * 40 + "\n")
            
    print("\n📄 Relatório salvo em test_output.txt")
    # Aguarda persistência de logs
    print("⏳ Aguardando persistência de logs...")
    await asyncio.sleep(5)
    
    print("\n📄 Relatório salvo em test_output.txt")

if __name__ == "__main__":
    asyncio.run(run_tests())
