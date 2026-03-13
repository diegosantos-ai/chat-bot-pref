# README - scripts (chat-bot-pref)

Este README descreve os scripts disponiveis em `chat-bot-pref/scripts/` e como usarlos.

Observacoes importantes
- Muitos scripts interagem com ChromaDB e com o ambiente Python do projeto; execute-os como o usuario `pilot` (na maior parte dos casos) para evitar problemas de permissao.
- Verifique se a virtualenv esta disponivel em `.venv` no raiz do projeto.
- Se os scripts nao estiverem executaveis, rode: `chmod +x /home/ec2-user/chat-bot-pref/scripts/*.sh`.
- As operacoes que alteram arquivos do sistema (systemd, copia para /var) podem necessitar de `sudo`.

Scripts e uso

- `chroma_list_collections.sh`
  - O que faz: lista collections presentes na instancia Chroma persistente.
  - Uso recomendado (executa como usuario pilot):
    sudo -u pilot bash -lc 'cd /home/ec2-user/chat-bot-pref && ./scripts/chroma_list_collections.sh'

- `chroma_count_collection.sh`
  - O que faz: conta o numero de documentos/chunks em uma collection (usa RAG_COLLECTION_NAME ou recebe argumento).
  - Uso:
    sudo -u pilot bash -lc 'cd /home/ec2-user/chat-bot-pref && ./scripts/chroma_count_collection.sh [collection_name]'

- `chroma_ingest_base.sh`
  - O que faz: roda o processo de ingest (cria chunks, persiste em Chroma). Aceita path para o base e opcao `force`.
  - Uso exemplo:
    sudo -u pilot bash -lc 'cd /home/ec2-user/chat-bot-pref && ./scripts/chroma_ingest_base.sh base/SEU_BASE_ID true'

- `chroma_backup.sh`
  - O que faz: cria um backup do diretorio `chroma_data` (compacta e salva com timestamp). Use para snapshot antes de operar.
  - Uso (root ou usuario com permissao para ler `chroma_data`):
    /home/ec2-user/chat-bot-pref/scripts/chroma_backup.sh

- `retriever_query.sh`
  - O que faz: executa uma consulta de teste contra o retriever e imprime os resultados (usa o ambiente do projeto).
  - Uso exemplo:
    sudo -u pilot bash -lc 'cd /home/ec2-user/chat-bot-pref && ./scripts/retriever_query.sh "qual o horario de funcionamento?"'

Dicas de troubleshooting
- Se receber erros de permissao em `chroma_data` ou ao baixar modelos ONNX: verifique dono/permissoes com `ls -la /home/ec2-user/chat-bot-pref/chroma_data` e corrija com `sudo chown -R pilot:pilot /home/ec2-user/chat-bot-pref/chroma_data`.
- Se o service systemd `pilot_atendimento` estiver em uso, pare/compile logs com:
  - `sudo systemctl status pilot_atendimento --no-pager -l`
  - `sudo journalctl -u pilot_atendimento -f`

Contato rapido
- Se quiser que eu rode uma bateria de consultas de diagnostico contra a collection, colecione 5-15 perguntas representativas e eu executo como `pilot` e reporto cobertura/resultados.
