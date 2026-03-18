with open("docs-LLMOps/README.md", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if "10. `fases/FASE7-CI-GENAI-REGRESSAO.md`" in line:
        new_lines.append("11. `fases/FASE8-ORQUESTRACAO-AIRFLOW.md`\n")
        new_lines.append("12. `fases/FASE9-DERIVA-SEMANTICA-BASE-VETORIAL.md`\n")
    if "preservando fronteiras limpas de experimento e transacional." in line:
        new_lines.append("Na branch `feat/orquestracao-airflow`, a Fase 8 foi fechada estabelecendo a fronteira offline via Apache Airflow isolado do runtime principal. Foram validadas a instalacao dedicada (Python 3.13 e Airflow 2.11.2) e o mapeamento das DAGs prioritarias iniciais (ingest, avaliacao e reindexacao) suportadas pelo tracking estrutural, deixando o schedule produtivo robusto como passo futuro.\n")
        new_lines.append("Na branch `feat/semantica-base-vetorial`, a Fase 9 foi entregue com a fundacao diagnostica documental. Foram estabelecidos indicadores de saude semantica da base, matriz diagnostica de sintomas por tenant, e definido um protocolo experimental de comparacao reproduzivel entre versoes da base (corpus + configuracao), permitindo respostas claras sobre regressao que poderao ser consumidas no Airflow futuramente.\n")

with open("docs-LLMOps/README.md", "w") as f:
    f.writelines(new_lines)
