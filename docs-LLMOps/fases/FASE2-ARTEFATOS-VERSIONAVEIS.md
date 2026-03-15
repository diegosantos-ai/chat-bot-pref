# Fase 2 — Estrutura Base de Artefatos Versionáveis

## Objetivo

Registrar a convenção estrutural e o contrato técnico mínimo adotados para separar artefatos versionáveis de IA do código de aplicação durante a Fase 2.

## Diretriz

Nesta etapa, a estrutura foi criada sem alterar o comportamento funcional do chat e sem integrar os artefatos novos ao runtime principal.

O objetivo deste bloco é organizar a base para evolução futura de:

- prompts de composição;
- prompts de fallback;
- guardrails e policies textuais;
- configuração de retrieval;
- configuração de chunking.

## Estrutura adotada

```text
ai_artifacts/
├── prompts/
│   ├── composer/
│   │   └── base_v1.txt
│   └── fallback/
│       └── fallback_v1.txt
├── guardrails/
│   └── policies/
│       └── policy_v1.md
└── rag/
    ├── retrieval/
    │   └── tenant_chroma_hash_v1.json
    └── chunking/
        └── paragraph_split_v1.json
```

## Convenção nominal inicial

- prompts: `<nome>_vN.txt`
- policies textuais: `<nome>_vN.md`
- configuração RAG: `<nome>_vN.json`
- metadados da versão: `<nome>_vN.<ext>.meta.json`

## Regra operacional desta fase

Os arquivos em `ai_artifacts/` representam a estrutura versionável preparada para a Fase 2.

O runtime ativo continua preservado nas fontes já validadas:

- `app/prompts/`
- `app/storage/chroma_repository.py`
- `app/services/rag_service.py`
- `app/policy_guard/service.py`

Isso evita acoplamento prematuro e mantém a distinção entre:

- artefato de IA versionável;
- código de aplicação;
- integração futura ainda não ativada.

## Catálogo mínimo em código

O catálogo técnico da estrutura foi registrado em:

- `app/llmops/artifact_catalog.py`
- `app/llmops/versioning.py`

Esse catálogo não altera o runtime atual. Ele apenas descreve:

- categorias;
- versões iniciais;
- caminhos dos artefatos;
- fontes ativas atuais do runtime;
- contrato mínimo de metadados;
- geração local de `content_hash` e `version_id`.

## Contrato mínimo de metadados por versão

Cada artefato versionável pode carregar um sidecar JSON próprio com os campos obrigatórios:

- `artifact_type`
- `artifact_name`
- `version_label`
- `version_id`
- `content_hash`
- `status`
- `created_at`
- `notes`

Os estados aceitos nesta fase são:

- `draft`
- `candidate`
- `promoted`
- `rolled_back`

Exemplo resumido:

```json
{
  "artifact_type": "prompt",
  "artifact_name": "composer_base",
  "version_label": "base_v1",
  "version_id": "prompt.composer_base.base_v1.4183563896f8",
  "content_hash": "f4e0f46451e4d650b973fe5152b09d6e8204fd1b02e95a608d96b769a862b975",
  "status": "candidate",
  "created_at": "2026-03-15T00:00:00Z",
  "notes": "Versao inicial da estrutura versionavel do prompt base de composicao."
}
```

## Algoritmo de identificação comparável

O identificador foi definido para ser estável, local e reproduzível sem depender de banco, MLflow ou serviço externo.

Regra adotada:

1. ler apenas o conteúdo relevante do artefato;
2. canonizar o conteúdo antes do hash;
3. gerar `content_hash` com SHA-256;
4. gerar `version_id` a partir de `artifact_type`, `artifact_name`, `version_label` e `content_hash`.

Canonização nesta fase:

- arquivos `.json`: serialização ordenada por chave, sem whitespace irrelevante;
- arquivos de texto: normalização de quebras de linha e remoção de whitespace apenas no final de cada linha.

Formato do identificador:

```text
<artifact_type>.<artifact_name>.<version_label>.<sha12>
```

Exemplos aplicados:

- `prompt.composer_base.base_v1.4183563896f8`
- `policy.institutional_policy.policy_v1.2803a9fb52c4`
- `retrieval_config.tenant_chroma_hash.tenant_chroma_hash_v1.7bf24a6405b0`
- `chunking_config.paragraph_split.paragraph_split_v1.38126ab04c99`

## Aplicação inicial nesta fase

O contrato foi aplicado aos artefatos iniciais já criados no bloco anterior:

- `ai_artifacts/prompts/composer/base_v1.txt`
- `ai_artifacts/prompts/fallback/fallback_v1.txt`
- `ai_artifacts/guardrails/policies/policy_v1.md`
- `ai_artifacts/rag/retrieval/tenant_chroma_hash_v1.json`
- `ai_artifacts/rag/chunking/paragraph_split_v1.json`

Cada um possui agora um sidecar `.meta.json` comparável localmente.

## Pontos de integração atuais no runtime

Nesta etapa, a resolução da versão ativa foi conectada de forma mínima aos componentes já existentes:

- `app/services/prompt_service.py` resolve por padrão o prompt base, o prompt de fallback e a policy textual ativos diretamente em `ai_artifacts/`, validando o sidecar antes do uso;
- `app/policy_guard/service.py` passa a derivar `policy_version` da policy textual ativa, mesmo mantendo a lógica de guardrail em código Python;
- `app/services/chat_service.py` resolve o `top_k` ativo do fluxo principal a partir da configuração versionada de retrieval;
- `app/services/rag_service.py` resolve a estratégia de chunking, o template de `section_id` e o fallback de conteúdo vazio a partir do artefato versionado;
- `app/storage/chroma_repository.py` expõe `retriever_version` e `embedding_version` a partir da configuração ativa de retrieval.

Esses pontos mantêm o runtime atual funcional, tenant-aware e sem dependência de banco ou MLflow.

## Resolução da versão ativa

O carregamento explícito foi centralizado em:

- `app/llmops/active_artifacts.py`

Esse resolvedor:

- usa o catálogo mínimo da Fase 2;
- resolve o caminho ativo do artefato em `ai_artifacts/`;
- carrega o sidecar `.meta.json`;
- valida `artifact_type`, `artifact_name`, `version_label` e `content_hash`;
- entrega o conteúdo textual ou o payload JSON já validado para o runtime.

O fallback local desta etapa permanece controlado e explícito:

- `PromptService` ainda suporta `prompts_dir` alternativo quando houver uso de diretório customizado em teste;
- `top_k_default` cai para `settings.LLM_CONTEXT_TOP_K` apenas se a chave não existir no JSON ativo;
- chunking aceita apenas a estratégia atualmente suportada pelo runtime (`double_newline_paragraphs`), falhando de forma explícita para variações ainda não implementadas.

## Integração com tracking experimental

Nesta etapa, a integração entre versionamento e tracking experimental foi mantida fora da auditoria operacional e fora do caminho transacional principal.

O contrato técnico mínimo foi centralizado em:

- `app/llmops/tracking_integration.py`

Esse contrato:

- reutiliza `ExperimentalRunContract` da Fase 1 como base mínima de `runs`, `params`, `metrics` e `artifacts`;
- resolve as versões ativas via `ActiveArtifactResolver`;
- preserva `tenant_id` e `request_id` como tags mínimas de correlação;
- acrescenta ao tracking os metadados comparativos da Fase 2 sem gravá-los na auditoria operacional.

Campos emitidos no tracking local desta etapa:

- tags: `tenant_id`, `request_id`, `prompt_version_id`, `policy_version_id`, `retriever_version_id`, `chunking_version_id`
- params: `prompt_version`, `policy_version`, `retriever_version`, `embedding_version`, `dataset_version`, `model_provider`, `model_name`, `top_k`, `chunking_version`
- metrics: `latency_ms`, `estimated_cost`
- artifact payload: combinação do contrato mínimo da Fase 1 com `prompt_version_id`, `policy_version_id`, `retriever_version_id`, `chunking_version` e `chunking_version_id`

Pontos de instrumentação usados para montar esse payload:

- prompt efetivamente usado: `app/services/prompt_service.py`
- policy ativa: `app/policy_guard/service.py`
- retrieval e embedding ativos: `app/storage/chroma_repository.py`
- chunking e `top_k` ativos: `app/llmops/active_artifacts.py` e `app/services/chat_service.py`

O caminho mínimo de evidência local foi ligado ao smoke de MLflow já existente em:

- `scripts/smoke_fase1_llmops.py`

Esse smoke continua local e offline, mas agora registra também o vínculo entre as versões ativas de artefato e a run experimental.

## Limite desta entrega

Esta etapa não:

- integra MLflow ao runtime;
- grava metadados em banco;
- altera o comportamento funcional já validado do chat;
- introduz nova estratégia de retrieval além da já existente;

## Débitos técnicos explícitos

Os pontos abaixo continuam intencionalmente fora do escopo deste bloco:

- a semântica de `policy_pre` e `policy_post` ainda permanece codificada em Python; o arquivo textual versionado identifica a versão ativa, mas ainda não dirige a lógica do guardrail;
- o endpoint público `POST /api/rag/query` mantém seu schema próprio de entrada e não promove `top_k_default` automaticamente quando o cliente envia um valor explícito;
- a emissão em MLflow continua restrita ao caminho offline/local de smoke e scripts experimentais, não ao runtime transacional;
- `embedding_version` continua sendo emitido como versão lógica do runtime, ainda sem sidecar versionado próprio;
- convenção de promoção/rollback permanece para as próximas tasks da Fase 2.

## Próximo passo lógico

Usar essa estrutura como base para:

- integrar versões e seus metadados ao tracking experimental offline;
- definir política explícita de promoção e rollback;
- conectar a convenção de artefatos às tasks seguintes da Fase 2 sem acoplar o runtime principal.
