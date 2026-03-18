import os
import re
import sys

def check_file_exists(filepath):
    if not os.path.exists(filepath):
        print(f"❌ FAIL: Arquivo esperado não encontrado -> {filepath}")
        return False
    print(f"✅ OK: Arquivo encontrado -> {filepath}")
    return True

def scan_file_for_keywords(filepath, keywords):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            missing = [kw for kw in keywords if kw not in content]
            if missing:
                print(f"❌ FAIL: Keywords faltando no {filepath}: {missing}")
                return False
            print(f"✅ OK: Keywords encontradas no {filepath}")
            return True
    except Exception as e:
        print(f"❌ FAIL ao ler {filepath}: {e}")
        return False

def main():
    print("--- Verificando Evidências de Alinhamento (Fase 12) ---")

    docs_to_check = [
        "docs-fundacao-operacional/alinhamento_vaga.md",
        "README.md",
        "docs-fundacao-operacional/arquitetura.md",
        "docs-fundacao-operacional/evidencias_case.md"
    ]

    all_passed = True

    # 1. Verifica se os documentos centrais existem
    for doc in docs_to_check:
        if not check_file_exists(doc):
            all_passed = False

    if all_passed:
        # 2. Verifica a matriz de aderência
        if not scan_file_for_keywords("docs-fundacao-operacional/alinhamento_vaga.md", [
            "Matriz de Aderência", "FastAPI", "policy_pre", "ChromaDB", "tenant-aware", "Terraform", "OpenTelemetry"
        ]):
            all_passed = False

        # 3. Verifica coerência do README refletindo a separação "operacional" e "experimental"
        if not scan_file_for_keywords("README.md", [
            "LLMOps", "Fundação Operacional", "experimentação"
        ]):
            all_passed = False

    if all_passed:
        print("\n🚀 SUCESSO: Todos os artefatos de aderência à vaga estão presentes e coerentes.")
        sys.exit(0)
    else:
        print("\n❌ FALHA: Faltou atualizar algo. Revise as saídas acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()
