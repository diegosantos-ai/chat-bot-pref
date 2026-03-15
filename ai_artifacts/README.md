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

Nesta etapa, a pasta `ai_artifacts/` registra a convenção estrutural adotada.

O runtime atual **ainda não** carrega esses arquivos diretamente.

O comportamento ativo do chat permanece preservado nas fontes já validadas da Fundação Operacional e da Fase 1, especialmente:

- `app/prompts/`
- `app/storage/chroma_repository.py`
- `app/services/rag_service.py`
- `app/policy_guard/service.py`

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
