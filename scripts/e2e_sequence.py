import asyncio
import sys
import json
from pathlib import Path

# Adiciona raiz ao path para importar app
sys.path.append(str(Path(__file__).parent.parent))

from app.orchestrator.service import OrchestratorService
from app.services.drive_watcher import DriveWatcher
from app.contracts.enums import AuditEventType, Channel, Decision, ResponseType, SurfaceType
from app.contracts.dto import ChatRequest


def _has_web_scraper_event(audit_events) -> bool:
    """Valida se a resposta final veio do fallback por web scraper."""
    for event in audit_events:
        if event.event_type != AuditEventType.RESPONSE_SELECTED:
            continue
        if event.data.get("source") == "web_scraper":
            return True
    return False


async def run_e2e_tests():
    print("=== INICIANDO TESTE E2E INTERATIVO (FALLBACK + DRIVE) ===")
    print("")

    orchestrator = OrchestratorService()
    drive_watcher = DriveWatcher()

    # TESTE 1: Web Scraper
    print("\n--- TESTE 1: WEB SCRAPER (SUCESSO ESPERADO) ---")
    print("DICA: termos de legislacao costumam retornar no site.")
    query_found = input(
        "Digite um termo que ESTA no site e tende a nao estar na base "
        "(Enter para default 'decreto'): "
    )
    if not query_found:
        query_found = "decreto"

    probe_scraper = await asyncio.to_thread(orchestrator.scraper.search_site, query_found)
    if probe_scraper:
        print("[OK] Scraper encontrou resultados na busca direta.")
    else:
        print("[WARN] Scraper nao encontrou resultados na busca direta para este termo.")

    print(f"Processando pergunta: '{query_found}'...")
    req = ChatRequest(
        message=query_found,
        channel=Channel.WEB_WIDGET,
        surface_type=SurfaceType.INBOX,
        session_id="test_e2e_scraper"
    )

    # Executa pipeline real (RAG -> Scraper -> Email)
    resp, ctx = await orchestrator.process(req)

    print(f"RESPOSTA IA: {resp.message[:200]}...")
    print(f"DECISÃO FINAL: {resp.decision}")
    print(f"TIPO RESPOSTA: {resp.response_type}")

    scraper_used = _has_web_scraper_event(ctx.audit_events)
    if scraper_used and resp.decision == Decision.ANSWER_RAG:
        print("[OK] Scraper foi fonte principal da resposta.")
    elif resp.decision == Decision.ESCALATE:
        print("[WARN] Scraper nao trouxe resultado util; fluxo seguiu para escalation.")
    else:
        print("[WARN] Resposta veio de outra fonte (RAG ou fallback).")

    # TESTE 2: Escalation (Email)
    print("\n\n--- TESTE 2: ESCALATION (EMAIL ESPERADO) ---")
    print("DICA: use uma pergunta institucional inexistente para cair em ESCALATED.")
    query_not_found = input(
        "Digite sua pergunta de teste "
        "(Enter para default 'qual lei municipal 2743-2026?'): "
    )
    if not query_not_found:
        query_not_found = "qual lei municipal 2743-2026?"

    print(f"Processando pergunta: '{query_not_found}'...")
    req2 = ChatRequest(
        message=query_not_found,
        channel=Channel.WEB_WIDGET,
        surface_type=SurfaceType.INBOX,
        session_id="test_e2e_escalation"
    )

    resp2, ctx2 = await orchestrator.process(req2)

    print(f"RESPOSTA IA: {resp2.message[:200]}...")
    print(f"DECISÃO FINAL: {resp2.decision}")
    print(f"TIPO RESPOSTA: {resp2.response_type}")

    template = ctx2.response_selected.template if ctx2.response_selected else "desconhecido"
    print(f"TEMPLATE FINAL: {template}")

    if resp2.response_type == ResponseType.ESCALATED:
        if template == "escalation_email_sent":
            print("[OK] Escalation por email acionado.")
        else:
            print("[WARN] Escalation acionado, mas via handoff direto (sem email automatico).")
    else:
        print(f"[WARN] Escalation nao acionado. Tipo resposta: {resp2.response_type}")
        print(
            f"       (Motivo provavel: intent {resp2.intent} "
            "foi tratada como OUT_OF_SCOPE/FALLBACK)"
        )

    # TESTE 3: Google Drive Sync
    print("\n\n--- TESTE 3: GOOGLE DRIVE AUTO-UPDATE ---")

    # Limpa estado anterior para garantir que o teste funcione mesmo com arquivo repetido
    state_file = Path("data/drive_state.json")
    if state_file.exists():
        state_file.unlink()
        print("[INFO] Estado local do Drive limpo para forcar nova ingestao.")

    print(f"Pasta monitorada ID: {drive_watcher.folder_id}")
    print("Estado atual: verificando arquivos...")

    drive_result = await asyncio.to_thread(drive_watcher.check_for_updates)
    print(f"STATUS DRIVE: {drive_result.get('status')}")
    print(
        "ARQUIVOS: vistos={seen} atualizados={updated} pastas_varridas={folders}".format(
            seen=drive_result.get("files_seen", 0),
            updated=drive_result.get("files_updated", 0),
            folders=drive_result.get("folders_scanned", 0),
        )
    )

    processed = drive_result.get("files_processed") or []
    if processed:
        print(f"ARQUIVOS INGERIDOS: {', '.join(processed)}")

    errors = drive_result.get("errors") or []
    if errors:
        print("ERROS:")
        for err in errors:
            print(f" - {err}")

    if drive_result.get("files_seen", 0) == 0:
        print(
            "[WARN] A pasta do Drive esta acessivel, mas sem arquivos visiveis. "
            "Nao houve ingestao para confirmar."
        )
    elif drive_result.get("files_updated", 0) > 0:
        print("[OK] Auto-update confirmado: houve ingestao de arquivos do Drive.")
    else:
        print("[INFO] Conexao OK, mas sem novidades para ingerir nesta execucao.")

    if state_file.exists():
        try:
            state_data = json.loads(state_file.read_text(encoding="utf-8"))
            print(f"STATE FILE: {len(state_data)} arquivo(s) rastreado(s).")
        except Exception:
            print("[WARN] State file gerado, mas nao foi possivel ler o JSON.")
    else:
        print("[INFO] Nenhum state file gerado (normal quando nao ha atualizacoes).")

if __name__ == "__main__":
    try:
        asyncio.run(run_e2e_tests())
    except KeyboardInterrupt:
        print("\nTeste cancelado pelo usuário.")
    except Exception as e:
        print(f"\nErro fatal nos testes: {e}")
