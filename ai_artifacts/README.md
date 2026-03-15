# ai_artifacts

Esta pasta separa **artefatos versionáveis de IA** do código de aplicação.

## Objetivo

Estabelecer a estrutura base da Fase 2 para:

- prompts de composição;
- prompts de fallback;
- guardrails e policies textuais;
- configuração de retrieval;
- configuração de chunking.
- sidecars de metadados por versão.

## Regra atual

O runtime atual **já consome** os artefatos de `ai_artifacts/` para prompts, policies, retrieval e chunking.

A resolução ativa desses artefatos é feita via `ActiveArtifactResolver` e serviços do runtime, como:

- `app/services/prompt_service.py`
- `app/services/rag_service.py`
- `app/policy_guard/service.py`
- `app/storage/tenant_chroma_repository.py`

A pasta `ai_artifacts/` deixa de ser apenas convenção estrutural e passa a fazer parte do contrato ativo do runtime: alterações nesses arquivos impactam diretamente o comportamento do chat, dentro do escopo e versionamento definidos aqui.

## Convenção nominal inicial

- prompts: `<nome>_vN.txt`
- policies textuais: `<nome>_vN.md`
- configuração RAG: `<nome>_vN.json`
- metadados: `<nome>_vN.<ext>.meta.json`

## Estrutura inicial

```text
ai_artifacts/
├── prompts/
│   ├── composer/
│   └── fallback/
├── guardrails/
│   └── policies/
└── rag/
    ├── retrieval/
    └── chunking/
```

Cada artefato versionável pode carregar um sidecar JSON com o contrato mínimo de identificação da versão, sem depender de banco, MLflow ou serviço externo.
