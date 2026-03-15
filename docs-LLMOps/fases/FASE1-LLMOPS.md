# Fase 1 — Fundação de LLMOps e Rastreabilidade Experimental

## Objetivo deste documento

Registrar o resumo executivo e técnico da execução da Fase 1 de LLMOps no Chat Pref, preservando a distinção entre:

- base operacional já validada;
- contratos mínimos da Fase 1 efetivamente implementados;
- capacidades futuras ainda não ativadas no runtime principal.

Este documento descreve o estado real validado na branch `setup/fundacao-llmops` em **15 de março de 2026**.

## Resumo executivo

A Fase 1 foi concluída no escopo previsto em `docs-LLMOps/PLANEJAMENTO-LLMOps.md`.

O projeto passou a ter:

- ambiente base e ambiente de desenvolvimento instalados e validados;
- estratégia de experiment tracking com MLflow formalizada para smoke local;
- segregação experimental por `tenant_id` e correlação por `request_id` definidas como contrato;
- separação explícita entre auditoria operacional e tracking experimental;
- contrato mínimo de `runs`, `params`, `metrics` e `artifacts` executado com evidência local;
- versionamento inicial de `prompt`, `retriever` e `embeddings` explícito;
- mapeamento mínimo de instrumentação em `app/audit` e `app/rag`;
- evidência executável local suficiente para marcar `CPPX-F1-T1` até `CPPX-F1-T12` como `OK`.

## Status da fase

| Item | Estado |
|---|---|
| Ciclo | Fase 1 — LLMOps, Avaliação e Governança |
| Card macro | Fundação de LLMOps e Rastreabilidade Experimental |
| Status | Concluída neste escopo |
| Branch validada | `setup/fundacao-llmops` |
| Critério de aceite | Atendido com evidência local |

## Resumo técnico da execução

### 1. Ambiente e dependências

Foram validados:

- `requirements.txt`
- `requirements-dev.txt`
- imports do ambiente base;
- imports do ambiente de desenvolvimento;
- execução do smoke oficial da fase no `.venv`.

O relatório de verificação da fase registrou ambiente base e ambiente dev como `OK`.

### 2. Tracking experimental

O MLflow foi adotado como stack de tracking experimental da fase, mas **apenas para smoke local e evidência técnica**, sem integração ao runtime transacional principal.

O smoke oficial passou a usar:

- backend SQLite local;
- artifact store local em `artifacts/llmops/smoke_fase1/`;
- criação de `run`;
- registro de `tags`, `params`, `metrics` e `artifact`;
- recuperação da `run` com `MlflowClient`.

Campos mínimos validados no smoke:

- `tenant_id`
- `request_id`
- `prompt_version`
- `policy_version`
- `retriever_version`
- `embedding_version`
- `dataset_version`
- `model_provider`
- `model_name`
- `top_k`
- `latency_ms`
- `estimated_cost`

### 3. Separação entre operação e experimento

A persistência operacional atual permaneceu inalterada em:

- `app/storage/audit_repository.py`

Os contratos mínimos da fase foram explicitados em:

- `app/audit/contracts.py`
- `app/rag/contracts.py`

Com isso, a branch passou a registrar de forma explícita:

- fronteira operacional;
- fronteira experimental;
- regra mínima de segregação por `tenant_id` e `request_id`;
- versão inicial de `retriever` e `embeddings`;
- pontos mínimos de instrumentação de auditoria e RAG.

### 4. Versionamento inicial

O versionamento inicial da fase ficou representado por:

- `PROMPT_BASE_VERSION`
- `PROMPT_FALLBACK_VERSION`
- `POLICY_TEXT_VERSION`
- `RAG_RETRIEVER_VERSION`
- `RAG_EMBEDDING_VERSION`

As versões de `retriever` e `embeddings` foram centralizadas em `app/settings.py` e refletidas nos contratos da fase.

### 5. Instrumentação mínima da fase

O mapeamento mínimo da fase foi formalizado em dois blocos:

#### Auditoria

- emissão de eventos operacionais correlacionáveis;
- persistência da trilha operacional por tenant.

#### RAG

- resolução da collection por tenant;
- execução da query de retrieval com contexto mínimo;
- resumo técnico dos resultados da retrieval.

Esse mapeamento foi validado no checker da fase e refletido no artifact do smoke.

## Evidências executadas

As execuções locais que sustentam o fechamento desta fase foram:

```bash
source .venv/bin/activate
python scripts/smoke_fase1_llmops.py
./scripts/check_fase1_llmops.sh .
pytest tests -q
```

Resultados observados:

- smoke oficial da fase: `PASS`, com 33 checks aprovadas;
- checker da fase: `PASS=32`, `WARN=0`, `FAIL=0`;
- suíte local: `32 passed`.

Artefatos de evidência gerados:

- `artifacts/llmops/smoke_fase1/smoke_report.json`
- `reports/fase1_llmops/report_20260315_102837.md`
- `reports/fase1_llmops/report_20260315_102837.json`

## Status por task da Fase 1

| Task | Estado |
|---|---|
| `CPPX-F1-T1` | `OK` |
| `CPPX-F1-T2` | `OK` |
| `CPPX-F1-T3` | `OK` |
| `CPPX-F1-T4` | `OK` |
| `CPPX-F1-T5` | `OK` |
| `CPPX-F1-T6` | `OK` |
| `CPPX-F1-T7` | `OK` |
| `CPPX-F1-T8` | `OK` |
| `CPPX-F1-T9` | `OK` |
| `CPPX-F1-T10` | `OK` |
| `CPPX-F1-T11` | `OK` |
| `CPPX-F1-T12` | `OK` |

## Limites do que foi validado nesta fase

Esta execução **não** ativa no runtime principal:

- logging de MLflow no caminho síncrono de request;
- benchmark reproduzível já operando como contrato ativo;
- avaliação formal de RAG já consolidada;
- Airflow como camada offline ativa;
- observabilidade avançada de qualidade e custo no runtime transacional.

Esses pontos permanecem como evolução das fases seguintes.

## Conclusão

A Fase 1 passou a ter contrato mínimo executável, evidência local reproduzível e validação objetiva do ambiente e dos artefatos essenciais de LLMOps.

O fechamento desta fase não transforma MLflow em componente ativo do runtime principal. O que foi validado foi a fundação técnica necessária para avançar para o versionamento mais amplo de artefatos e para as fases seguintes de benchmark e avaliação formal.

## Próximo passo lógico

Iniciar a **Fase 2 — Versionamento de Prompts, Policies e Configuração de RAG**, preservando:

- `tenant_id` como contrato estrutural;
- `request_id` como contrato transversal;
- separação entre auditoria operacional e tracking experimental;
- distinção entre runtime ativo e arquitetura-alvo da fase LLMOps.
