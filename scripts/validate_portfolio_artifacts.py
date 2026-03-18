import os
import sys

def verify_files_and_keywords():
    print("--- Verificação Mínima de Artefatos Finais ---")

    files_to_check = {
        "docs-fundacao-operacional/estudo_de_caso.md": ["Artefatos para Exploração", "Resumo Executivo"],
        "docs-fundacao-operacional/tradeoffs_decisoes.md": ["Decisões de Engenharia", "Trade-off:"],
        "docs-fundacao-operacional/roteiro_demonstracao.md": ["Roteiro de Demonstração Técnico" if False else "Roteiro de Demonstração Técnica".replace("Técnico", "Técnica"), "docker compose up"],
        "docs-fundacao-operacional/matriz_capacidades.md": ["Padrões de Mercado", "Requisito de Indústria"]
    }

    all_passed = True

    for filepath, keywords in files_to_check.items():
        if not os.path.exists(filepath):
            print(f"❌ ERRO: Faltando {filepath}")
            all_passed = False
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            for kw in keywords:
                if kw not in content:
                    print(f"❌ ERRO: Faltando palavra-chave '{kw}' em {filepath}")
                    all_passed = False

        # Garantir ausência de tom explícito de "venda de vaga"
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().lower()
            if "vaga " in content or "entrevista" in content:
                print(f"❌ ERRO: Tom explícito de recrutamento encontrado no arquivo {filepath}")
                all_passed = False

    if all_passed:
        print("\n✅ SUCESSO: Todos os artefatos de portfólio verificados e alinhados profissionalmente.")
        sys.exit(0)
    else:
        print("\n❌ FALHA: Faltou atualizar ou estruturar algum arquivo de demonstração.")
        sys.exit(1)

if __name__ == "__main__":
    verify_files_and_keywords()
