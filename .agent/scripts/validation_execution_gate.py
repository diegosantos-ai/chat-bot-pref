import os
import sys
import argparse

def validate_project(directory="."):
    required_files = ["design.md", "requirements.md", "task.md"]
    missing = []

    for f in required_files:
        if not os.path.exists(os.path.join(directory, f)):
            missing.append(f)

    if missing:
        print("[ EXECUTION GATE : FAIL ]")
        print("Faltam os seguintes documentos fundamentais de especificação (Specs):")
        for m in missing:
            print(f"  ❌ {m}")
        print("\nREGRA DE OURO KIRO: Nenhum código de produção deve ser escrito ou alterado antes destas especificações existirem no projeto.")
        sys.exit(1)
    else:
        print("[ EXECUTION GATE : PASS ]")
        print("Os 3 pilares de especificação estão presentes na raiz do projeto. O(s) Agente(s) Dev estão liberados para codificar.")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kiro Execution Gate")
    parser.add_argument("--dir", default=".", help="Target project directory")
    args = parser.parse_args()
    validate_project(args.dir)
