import os
import argparse
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description="Kiro Session Management")
    parser.add_argument("action", choices=["start", "handoff"], help="Action to execute")
    parser.add_argument("--prompt", action="store_true", help="Generate the AI prompt payload")
    parser.add_argument("--dir", default=".", help="Target project directory")
    return parser.parse_args()

def handle_start(args):
    progresso_file = os.path.join(args.dir, "progresso.md")
    if not os.path.exists(progresso_file):
        print("[SESSION_CONTEXT]")
        print("STATUS: NOVO PROJETO")
        print("O arquivo progresso.md não foi encontrado nesta pasta.")
        print("DIRETRIZ KIRO: Construa as especificações (design.md, requirements.md, task.md) lendo os templates em d:\Projetos\Desenvolvendo\agent-farm\templates.")
        print("Após a criação das specs, crie o progresso.md base contendo Fase Atual, Último Marco e Próxima Tarefa P0.")
        return

    with open(progresso_file, "r", encoding="utf-8") as f:
        content = f.read()

    if args.prompt:
        print("[SESSION_CONTEXT]\n")
        print(content)
        print("\n---")
        print("DIRETRIZ KIRO: Leia o contexto acima. O que falta no 'Próxima Tarefa P0'? Guie a sessão focando apenas nisso.")
    else:
        print("Session context read successfully. Enable --prompt to view payload.")

def handle_handoff(args):
    progresso_file = os.path.join(args.dir, "progresso.md")
    hoje = datetime.now().strftime('%d/%m/%Y')
    print(f"[HANDOFF GATE]")
    if not os.path.exists(progresso_file):
        print("ERRO: O projeto não possui progresso.md. Crie-o imediatamente baseando-se nas specs criadas.")
        return

    print("Kiro, por favor ATUALIZE o arquivo progresso.md com as seguintes diretrizes:")
    print(f"1. Adicione uma entrada sob '## Histórico de Handoffs (Sessões)' com a data de hoje: {hoje}")
    print("2. Resuma em 1 a 2 linhas curtas o que foi consolidado.")
    print("3. Atualize o campo 'Último Marco Atingido'")
    print("4. DEFINA a 'Próxima Tarefa P0 (Imediata)' para a IA que irá assumir a sessão de amanhã.")

if __name__ == "__main__":
    args = parse_args()
    if args.action == "start":
        handle_start(args)
    elif args.action == "handoff":
        handle_handoff(args)
