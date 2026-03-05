# 20260207_163000_atualizacao_rag_prompts.md

## Resumo
- Ajuste de respostas de fallback (out-of-scope e privado) para reduzir respostas genéricas.
- Inclusão de disclaimer nos prompts de crise (suicídio e violência).
- Expansão de sinônimos para CMEI/CEMEI e matrícula (melhor recuperação no RAG).
- Ajustes de conteúdo RAG para IPTU (anos anteriores/futuros), fila de espera do CMEI e prazos de obras.
- Ajuste de detecção de ofensas (pluralização).

## Impacto
- Melhora a qualidade de resposta para IPTU, CMEI e obras.
- Mensagens ofensivas passam a resultar em NO_REPLY.
- Prompts atualizados exigem reinício para limpar cache de prompts.

## Passos de aplicação no servidor
1. Atualizar o código (git pull).
2. Reingerir a base RAG:
   - `python -m app.rag.ingest data/knowledge_base/BA-RAG-PILOTO-2026.01.v1 --force`
3. Reiniciar a API (para recarregar prompts em cache).
   - Se Docker: `docker-compose restart terezia`
   - Se systemd: `sudo systemctl restart terezia-api`

## Validação
- Testar perguntas:
  - "Como matriculo meu filho no cemei"
  - "Nao tem vagas para meu filho no cemei"
  - "Quero pagar meu IPTU de 2022"
  - "Quero pagar meu IPTU de 2026"
  - "Quando vai se encerrar as obras do asfalto novo Vida Nova"
  - "Voce sao uns bandidos"

## Rollback
- Reverter commit e reingerir base anterior (sem --force) ou restaurar backup do ChromaDB.
