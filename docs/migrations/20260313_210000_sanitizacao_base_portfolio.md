# Migração: Sanitização da Base para Portfólio

Data: 2026-03-13 21:00:00
Tipo: Refatoração estrutural + limpeza de identidade legada

## Resumo
Esta migração transforma o repositório em base independente para portfólio, removendo acoplamentos com o projeto original e limpando dados históricos legados.

## Alterações aplicadas

### 1. Runtime e backend
- `app/api/deploy.py`
  - Remove caminho fixo absoluto de projeto legado.
  - Usa diretório do próprio projeto em tempo de execução.
  - `pip install` passa a usar `sys.executable -m pip`.
- `app/api/admin.py`
  - Remove hardcodes para base RAG legada.
  - `IngestRequest.base_path` agora é opcional.
  - Base padrão vem de `settings.RAG_BASE_ID` (`data/knowledge_base/<RAG_BASE_ID>`).
- `app/services/web_scraper.py`
  - Remove `BASE_URL` legado fixo.
  - Passa a usar URL configurável via `settings.FALLBACK_TARGET_URL`.
  - Não executa scraping se URL não estiver configurada.

### 2. Admin panel
- `admin-panel/src/services/api.ts`
  - `rag.ingest` não força mais base legada por padrão.
- `admin-panel/src/pages/RAGManager.tsx`
  - Ingest passa a usar base padrão do backend (sem hardcode).

### 3. Scripts e operação de servidor
- `scripts/systemd/terezia-api.service`
  - Passa a usar placeholders `__PROJECT_DIR__` e `__VENV_BIN__`.
- `scripts/systemd/terezia-grafana.service`
  - Remove paths legados e usa `docker compose` com placeholder.
- `scripts/systemd/setup_systemd.sh`
  - Descobre `PROJECT_DIR` dinamicamente.
  - Detecta virtualenv em `.venv` ou `venv`.
  - Materializa units finais com `sed`.
- `scripts/setup_grafana.py`
  - Dashboard path passa a ser relativo ao projeto.
- `logging/import_dashboards.py`, `logging/import-dashboards.sh`, `logging/setup_loki_datasource.sh`
  - Remove paths absolutos legados.
  - Usa caminho relativo ao projeto.
  - Senha do Grafana parametrizável (`GRAFANA_PASS`, default `admin`).
- `logging/docker-compose-loki.yml` e `logging/install-loki.sh`
  - Rede externa passa a usar `CHATBOT_NETWORK` (default `chat-bot-pref_default`).
  - Remove dependência fixa da rede/volume do projeto antigo.

### 4. Reset de base RAG
- Criação da base mínima limpa:
  - `data/knowledge_base/default/manifest.json`
  - `data/knowledge_base/default/items/.gitkeep`
- Scripts ajustados para defaults neutros:
  - `scripts/chroma_ingest_base.sh` -> `data/knowledge_base/default`
  - `scripts/chroma_count_collection.sh` -> `default_knowledge_base`

### 5. Limpeza de identidade e exemplos
- Atualizados exemplos e metadados legados em:
  - `prompts/v1/manifest.json`
  - `prompts/v1/ouvidoria_redirect.txt`
  - `app/models/meta_user_profile.py`
  - `app/integrations/meta/client.py`
  - `app/contracts/dto.py`
  - `app/rag/ingest.py`
  - `tests/test_verify_fix.py`
  - `tests/test_embedding_ab.py`
  - `db/schema.sql`
  - `db/migrations/20260214_220000_add_meta_user_profiles_cache.sql`
  - `implementation_plan.md`
  - `documentos/relatorio_exec_tecnico_execucao_observabilidade.md`
  - `.vscode/settings.json`

### 6. Limpeza de dados/artefatos históricos
- Removidos artefatos e outputs legados de `artifacts/`, `data/datasets/`, `data/evaluation/`, `data/results/`.
- Mantida estrutura vazia com `.gitkeep` para novo ciclo.
- Removidos arquivos de contexto histórico não necessários (`pr58.diff`, `pr_info.json`, `session.md`, `test_output.txt`, `report.xml`, `TESTE A-B - EMBEDDING PROVIDERS.txt`).

### 7. Virtualenv versionado
- Removidos diretórios versionados `.venv/` e `venv/` para evitar vazamento de caminhos locais antigos.

## Impacto operacional
- Pode exigir reprovisionamento local do ambiente virtual.
- Units systemd antigas baseadas em paths fixos devem ser reinstaladas com o script atualizado.
- Scripts de logging passam a depender de variáveis opcionais (`CHATBOT_NETWORK`, `GRAFANA_PASS`).

## Ações necessárias no servidor após deploy
1. Recriar ambiente virtual no diretório atual do projeto.
2. Reinstalar serviços systemd:
   - `sudo bash scripts/systemd/setup_systemd.sh`
3. Validar logging/Loki com a rede correta:
   - `export CHATBOT_NETWORK=<rede_docker_do_projeto>` (se necessário)
4. Confirmar URL de fallback web por tenant (`FALLBACK_TARGET_URL`) antes de usar scraping.

## Verificação recomendada
- Buscar termos proibidos no repo (exceto `docs_ref/`) conforme checklist de sanitização do portfólio.
- Validar endpoints admin de RAG e ingest com base `default`.
- Validar scripts de systemd/logging em ambiente Linux.
