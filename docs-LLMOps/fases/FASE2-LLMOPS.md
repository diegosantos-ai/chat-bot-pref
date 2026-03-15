# Fase 2 — Versionamento de Prompts, Policies e Configuração de RAG

## Objetivo deste documento

Consolidar o resumo executivo, a política operacional e o checklist final da Fase 2 de LLMOps no Chat Pref.

Este documento descreve o estado real validado na branch `feat/fase2-rag-prompts`, preservando a distinção entre:

- artefatos, contratos e integrações já implementados;
- governança operacional definida para promoção e rollback;
- capacidades futuras ainda não ativadas no runtime transacional.

## Resumo executivo

No escopo atual, a Fase 2 foi consolidada com:

- estrutura explícita de artefatos versionáveis em `ai_artifacts/`;
- identificadores comparáveis e sidecars mínimos de metadados por versão;
- resolução explícita da versão ativa para prompts, policy, retrieval e chunking;
- integração mínima dessas versões ao tracking experimental local já definido na Fase 1;
- política operacional documentada para estados, promoção, rollback e validação;
- checklist final de aceite da fase.

O resultado prático é que o projeto agora consegue:

- distinguir artefato de IA de código de aplicação;
- reconstruir localmente qual versão está ativa no runtime;
- correlacionar versões ativas com o tracking experimental local;
- manter a separação entre auditoria operacional e tracking experimental.

## Status da fase

| Item | Estado |
|---|---|
| Ciclo | Fase LLMOps |
| Card macro | Fase 2 — Versionamento de Prompts, Policies e Configuração de RAG |
| Branch validada | `feat/fase2-rag-prompts` |
| Status | Consolidada neste escopo |
| Critério de aceite | Atendido com evidência local e documentação operacional |

## Escopo implementado

### 1. Artefatos versionáveis

Foram estruturados artefatos versionáveis para:

- prompt base/composer;
- prompt de fallback;
- policy textual;
- configuração de retrieval;
- configuração de chunking.

Referência técnica:

- `docs-LLMOps/fases/FASE2-ARTEFATOS-VERSIONAVEIS.md`

### 2. IDs e metadados

Cada artefato relevante passou a ter:

- `artifact_type`;
- `artifact_name`;
- `version_label`;
- `version_id`;
- `content_hash`;
- `status`;
- `created_at`;
- `notes`.

O identificador comparável é estável e calculado a partir do conteúdo relevante do artefato.

### 3. Integração ao runtime

O runtime atual passou a resolver explicitamente:

- prompt principal ativo;
- prompt de fallback ativo;
- policy textual ativa;
- `top_k` ativo;
- chunking ativo;
- `retriever_version` e `embedding_version` ativos.

Essa resolução foi mantida mínima, tenant-aware e sem mudança funcional relevante no chat.

### 4. Integração ao tracking experimental

O tracking experimental local passou a registrar, no smoke de MLflow:

- versões lógicas de prompt, policy, retrieval, embedding e chunking;
- `version_id` comparáveis de prompt, policy, retrieval e chunking;
- `tenant_id` e `request_id` como correlação mínima;
- métricas técnicas básicas da run experimental.

Essa integração continua fora da auditoria operacional e fora do caminho síncrono principal do runtime.

## Estado atual vs. limite da fase

### Estado atual validado

- os sidecars de versão existem e são válidos;
- o runtime resolve a versão ativa com base em rótulos explícitos de versão;
- o tracking experimental local recebe as versões e `version_id` dos artefatos ativos;
- o contrato mínimo da Fase 1 segue preservado;
- a política de promoção e rollback está definida documentalmente.

### O que ainda não é comportamento ativo

- promoção automática por mudança de `status`;
- rollback automático guiado por tracking;
- benchmark formal obrigatório para toda promoção;
- integração de MLflow ao runtime transacional;
- seleção dinâmica de artefato ativo por `status` em vez de configuração explícita.

## Estados de versão adotados

Os estados reconhecidos para um artefato versionável são:

- `draft`
- `candidate`
- `promoted`
- `rolled_back`

### Significado operacional

`draft`

- versão ainda em construção ou sem evidência mínima;
- não deve ser tratada como base de comparação confiável;
- não deve ser apontada como ativa no runtime.

`candidate`

- versão completa o suficiente para comparação;
- sidecar e `version_id` já são válidos;
- pode participar de testes locais, smoke e tracking experimental;
- é o estado esperado para artefatos prontos para avaliação.

`promoted`

- versão aprovada como referência operacional da fase;
- deve ter passado pelo critério mínimo de promoção;
- pode ser usada como base para futuras comparações e regressões;
- sua ativação no runtime depende de configuração explícita, não apenas do `status`.

`rolled_back`

- versão revertida por risco, regressão ou decisão técnica;
- não deve permanecer como referência ativa;
- deve conservar trilha documental e experimental da reversão.

## Política de promoção

### Regra estrutural

Na implementação atual, `status` é metadado de governança. Ele **não** troca sozinho a versão ativa do runtime.

A versão ativa continua sendo escolhida por:

- rótulos explícitos de versão em `settings`;
- catálogo da Fase 2;
- resolvedor ativo em `app/llmops/active_artifacts.py`.

### Critério mínimo de promoção

Uma versão só deve sair de `candidate` para `promoted` quando atender, no mínimo:

1. sidecar `.meta.json` válido e consistente com `content_hash` e `version_id`;
2. artefato resolvido corretamente no runtime ou no ponto de integração previsto;
3. testes locais relevantes aprovados;
4. evidência de tracking experimental local disponível quando a versão impactar comportamento comparável;
5. ausência de regressão funcional conhecida no fluxo atual;
6. documentação da mudança e do racional atualizadas.

### Relação entre comparação experimental e promoção

A promoção não deve ser feita apenas por inspeção visual do arquivo.

A convenção adotada é:

- a comparação experimental fornece a evidência técnica;
- a promoção registra a decisão operacional sobre essa evidência.

Enquanto não houver benchmark formal maduro para um determinado tipo de artefato, a fase admite comparação mínima por smoke, regressão local e tracking experimental local. Nesses casos, a promoção deve ser tratada como controlada e explicitamente documentada.

### Estado real da branch nesta etapa

No estado atual desta branch, os artefatos versionados existentes permanecem como `candidate` nos sidecars publicados.

Isso não invalida o fechamento da Fase 2. Significa apenas que a fase entrega a governança e o mecanismo de comparação, sem declarar promoção operacional automática já executada.

## Política de rollback

### Regra estrutural

Rollback é uma decisão operacional explícita, não um efeito colateral do tracking.

### Procedimento mínimo de rollback

Quando uma versão ativa precisar ser revertida:

1. identificar a última versão estável conhecida para aquele tipo de artefato;
2. repontar explicitamente o runtime para essa versão por configuração ou seleção equivalente;
3. marcar a versão revertida como `rolled_back` quando houver decisão formal de reversão;
4. rerodar as validações mínimas locais da fase;
5. registrar a reversão na documentação da fase ou na trilha de mudança correspondente.

### Observação importante

Se uma versão ainda não chegou a ser usada como referência ativa e falhou apenas em avaliação preliminar, ela pode permanecer em `candidate` e ser descartada da comparação sem ser necessariamente marcada como `rolled_back`.

## Responsabilidade por camada

| Camada | Responsabilidade |
|---|---|
| Runtime | Resolver e consumir a versão ativa explicitamente configurada |
| Tracking experimental | Registrar metadados comparativos, params, metrics e artifacts por tenant |
| Auditoria operacional | Registrar fatos do atendimento e decisões operacionais, sem artifacts experimentais |
| Documentação | Registrar convenção, estado atual, critérios de promoção/rollback e checklist da fase |

## Status por task da Fase 2

| Task | Estado |
|---|---|
| `CPPX-F2-T1` | `OK` |
| `CPPX-F2-T2` | `OK` |
| `CPPX-F2-T3` | `OK` |
| `CPPX-F2-T4` | `OK` |
| `CPPX-F2-T5` | `OK` |
| `CPPX-F2-T6` | `OK` |
| `CPPX-F2-T7` | `OK` |

## Checklist final de aceite da Fase 2

- [ ] `ai_artifacts/` contém prompts, policy, retrieval e chunking separados do código de aplicação
- [ ] cada artefato principal possui sidecar `.meta.json` válido
- [ ] `version_id` e `content_hash` são reproduzíveis localmente
- [ ] o runtime resolve a versão ativa de prompt, policy, retrieval e chunking sem hardcodes dispersos
- [ ] `top_k` ativo é resolvido a partir da configuração versionada de retrieval
- [ ] `retriever_version` e `embedding_version` permanecem explícitos e tenant-aware
- [ ] o tracking experimental local registra `tenant_id`, `request_id`, versões lógicas e `version_id` comparáveis dos artefatos
- [ ] a auditoria operacional continua separada do tracking experimental
- [ ] a política de promoção e rollback está documentada sem prometer automação inexistente
- [ ] as validações finais da fase foram executadas com sucesso

## Validações finais recomendadas

```bash
source .venv/bin/activate
pytest tests/test_phase2_artifact_catalog.py tests/test_phase2_artifact_versioning.py tests/test_phase2_active_artifacts.py tests/test_phase2_tracking_integration.py -q
pytest tests -q
python scripts/smoke_fase1_llmops.py
```

## Evidência mínima esperada

Para encerrar a fase manualmente, a validação final deve produzir pelo menos:

- testes da Fase 2 aprovados;
- smoke local de MLflow em `PASS`;
- artifact recente em `artifacts/llmops/smoke_fase1/req-smoke-*_artifact.json` contendo:
  - `prompt_version`
  - `policy_version`
  - `retriever_version`
  - `embedding_version`
  - `chunking_version`
  - `prompt_version_id`
  - `policy_version_id`
  - `retriever_version_id`
  - `chunking_version_id`

## Próximo passo lógico

Encerrar a Fase 2 e avançar para a **Fase 3 — Dataset de Avaliação e Benchmark Reproduzível**, usando a governança de artefatos da Fase 2 como base para comparação experimental mais forte.
