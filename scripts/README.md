# README - scripts (chat-bot-pref)

Este README descreve os scripts disponiveis em `chat-bot-pref/scripts/` e como usarlos.

Observacoes importantes
- Parte desta pasta ainda contem scripts legados de operacao e diagnostico. Revise o contexto do script antes de usalo em ambiente atual.
- Scripts de `systemd` estao congelados como legado e nao devem ser usados como caminho ativo de deploy.
- Verifique se a virtualenv esta disponivel em `.venv` no raiz do projeto.
- Se os scripts nao estiverem executaveis, rode: `chmod +x ./scripts/*.sh`.
- As operacoes que alteram arquivos do sistema (systemd, copia para /var) podem necessitar de `sudo`.

Scripts e uso

- `chroma_list_collections.sh`
  - O que faz: lista collections presentes na instancia Chroma persistente.
  - Uso recomendado:
    `./scripts/chroma_list_collections.sh`

- `chroma_count_collection.sh`
  - O que faz: conta o numero de documentos/chunks em uma collection (usa RAG_COLLECTION_NAME ou recebe argumento).
  - Uso:
    `./scripts/chroma_count_collection.sh [collection_name]`

- `chroma_ingest_base.sh`
  - O que faz: roda o processo de ingest (cria chunks, persiste em Chroma). Aceita path para o base e opcao `force`.
  - Uso exemplo:
    `./scripts/chroma_ingest_base.sh data/knowledge_base/SEU_BASE_ID true`

- `chroma_backup.sh`
  - O que faz: cria um backup do diretorio `chroma_data` (compacta e salva com timestamp). Use para snapshot antes de operar.
  - Uso:
    `./scripts/chroma_backup.sh`

- `retriever_query.sh`
  - O que faz: executa uma consulta de teste contra o retriever e imprime os resultados (usa o ambiente do projeto).
  - Uso exemplo:
    `./scripts/retriever_query.sh "qual o horario de funcionamento?"`

Dicas de troubleshooting
- Se receber erros de permissao em `chroma_data` ou ao baixar modelos ONNX, confira as permissoes do diretorio local usado pelo projeto.
- Se ainda existir algum service manager legado ativo na sua maquina, pare-o antes de validar a stack local via Docker Compose.

Contato rapido
- Se quiser rodar uma bateria de consultas de diagnostico contra a collection, separe 5-15 perguntas representativas e use os scripts de consulta a partir da raiz do projeto.
