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

## Limite desta entrega

Esta etapa não:

- integra MLflow ao runtime;
- muda a carga ativa de prompts ou policy;
- troca a origem funcional da configuração RAG;
- grava metadados em banco;
- altera comportamento do chat.

## Próximo passo lógico

Usar essa estrutura como base para:

- integrar versões e seus metadados ao tracking experimental offline;
- definir política explícita de promoção e rollback;
- conectar a convenção de artefatos às tasks seguintes da Fase 2 sem acoplar o runtime principal.
