with open("docs-LLMOps/ARQUITETURA-LLMOps.md", "r") as f:
    content = f.read()

content = content.replace(
    "## Bloco 8 — Orquestração offline\n\n### Papel\n\nExecutar processos que não pertencem ao fluxo síncrono da requisição.\n\n### Responsabilidades\n\n* ingestão de documentos;\n* reindexação da base vetorial;\n* execução de benchmark recorrente;\n* análise assíncrona de logs.\n\n### Situação\n\n**Arquitetura-alvo da fase.**",
    "## Bloco 8 — Orquestração offline\n\n### Papel\n\nExecutar processos que não pertencem ao fluxo síncrono da requisição, viabilizando workflows analíticos e pipelines reprodutíveis.\n\n### Responsabilidades\n\n* ingestão de documentos (configurada via DAGs);\n* reindexação da base vetorial;\n* execução de benchmark recorrente;\n* análise assíncrona de logs.\n\n### Situação\n\n**Fase 8 consolidada no âmbito de infraestrutura MLOps**. Estabelecido ambiente dedicado Apache Airflow parametrizado por tenant para as execuções prioritárias, desvinculado do runtime de produção."
)

content = content.replace(
    "## Bloco 9 — Monitoramento de deriva semântica\n\n### Papel\n\nDetectar sinais de deterioração da qualidade semântica da base de conhecimento por tenant.\n\n### Responsabilidades\n\n* comparar desempenho entre versões de base vetorial;\n* identificar queda de relevância ou aumento de fallback;\n* sinalizar degradações associáveis a base, retrieval ou modelo;\n* sustentar reavaliação de ingest, chunking e configuração.\n\n### Situação\n\n**Arquitetura-alvo da fase.**",
    "## Bloco 9 — Monitoramento de deriva semântica\n\n### Papel\n\nDetectar sinais de deterioração da qualidade semântica da base de conhecimento por tenant.\n\n### Responsabilidades\n\n* protocolar método e critério comparativo de desempenho entre versões de base vetorial;\n* estabelecer indicadores de queda de relevância ou aumento de recusa;\n* compor matriz diagnóstica de degradações associáveis a base, retrieval ou modelo.\n\n### Situação\n\n**Fase 9 consolidada no modo fundação-diagnóstica**. Processo protocolado nas fronteiras de avaliação offline em conjunto funcional com rastreabilidade, sem impacto no código do runtime de produção e apto para gatilhos operacionais."
)

with open("docs-LLMOps/ARQUITETURA-LLMOps.md", "w") as f:
    f.write(content)
