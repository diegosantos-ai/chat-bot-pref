# ADR-007 — Promoção e Rollback de Artefatos Versionados

## Status
Aceito

## Contexto

A Fase 2 do Chat Pref introduziu:

- artefatos versionáveis em `ai_artifacts/`;
- `version_id` e `content_hash` comparáveis;
- resolução explícita da versão ativa no runtime;
- integração mínima dessas versões ao tracking experimental local.

Com isso, surgiu uma necessidade de governança operacional que não estava totalmente explícita nas ADRs anteriores:

- o que significa cada `status` de versão;
- quando uma versão pode ser promovida;
- como uma reversão deve ocorrer sem misturar runtime, auditoria e tracking;
- se o `status` deve ou não comandar automaticamente a seleção da versão ativa.

Sem essa definição, o projeto correria risco de:

- tratar `status` como feature flag implícita;
- promover versões sem evidência mínima;
- documentar rollback como se fosse automação já implementada;
- confundir trilha experimental com decisão operacional.

## Decisão

O projeto adota a seguinte convenção:

### 1. `status` é metadado de governança

Os estados `draft`, `candidate`, `promoted` e `rolled_back` existem para governança, documentação e tracking.

Eles **não** determinam sozinhos a versão ativa do runtime.

### 2. A versão ativa continua explícita

Na implementação atual, a ativação de uma versão depende de:

- rótulo de versão configurado;
- catálogo da Fase 2;
- resolvedor ativo do runtime.

Não há seleção automática por `status`.

### 3. Promoção exige evidência mínima

Uma versão só pode ser promovida quando houver, no mínimo:

- sidecar válido;
- `version_id` estável;
- resolução correta no runtime ou no ponto de integração previsto;
- validação local relevante aprovada;
- evidência experimental local quando aplicável;
- documentação da decisão atualizada.

### 4. Rollback é reversão explícita

Rollback significa:

- retirar uma versão do papel de referência ativa;
- repontar o runtime para a última versão estável conhecida;
- registrar a versão revertida como `rolled_back` quando a reversão for formalizada;
- rerodar a validação mínima antes de seguir.

### 5. Auditoria operacional continua separada

Promoção e rollback podem ser correlacionados ao tracking experimental, mas não devem ser persistidos como artifacts experimentais dentro da auditoria operacional do atendimento.

## Consequências

### Positivas

- governança mais clara;
- promoção mais disciplinada;
- rollback explicável;
- menor risco de automação implícita inexistente;
- alinhamento entre runtime, tracking e documentação.

### Negativas / trade-offs

- processo ainda depende de disciplina manual;
- promoção não é instantânea por mudança de `status`;
- rollback continua exigindo reconfiguração explícita da versão ativa.

## Impacto na implementação

Esta decisão confirma que:

- o runtime segue consumindo versões explicitamente configuradas;
- o tracking experimental recebe versões e `version_id` comparáveis;
- a documentação da fase deve registrar promoção e rollback como convenções operacionais, não como automação já implantada.

## Relação com decisões anteriores

Esta ADR complementa:

- `ADR-001 — Separação entre Auditoria Operacional e Experiment Tracking`
- `ADR-002 — MLflow como Stack de Experimentação`
- `ADR-004 — Versionamento de Prompts, Policies e Configurações`

## Referências internas

- `docs-LLMOps/fases/FASE2-LLMOPS.md`
- `docs-LLMOps/PLANEJAMENTO-LLMOps.md`
