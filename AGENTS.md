# AGENTS.md

## 1. Propósito

Este arquivo define as regras operacionais para agentes de IA que atuam neste repositório.

Ele não substitui:

- `README.md`
- `docs/contexto.md`
- `docs/arquitetura.md`
- `docs/planejamento_fases.md`

Sua função é orientar como agentes devem ler o projeto, planejar mudanças, executar alterações e validar resultados.

## 2. Objetivo atual do projeto

O projeto está em reconstrução controlada sobre uma base mínima já validada.

O runtime ativo atual tem foco em:

- FastAPI com `GET /`, `GET /health`, `POST /api/chat`, `POST /api/webhook` e endpoints `RAG`
- contrato explícito de `tenant_id`
- contexto de tenant por request
- persistência local por tenant
- auditoria mínima por tenant
- RAG tenant-aware com ingest limpa
- tenant demonstrativo versionado
- execução local e via Docker com smoke tests

Os itens abaixo ainda não fazem parte do núcleo validado atual:

- canal Telegram operando como demonstração ponta a ponta
- composição generativa ativa com provedor LLM
- `PolicyDecision` e `AuditEvent` versionado
- logs estruturados, `/metrics` e traces
- CI ativa no GitHub Actions
- deploy em AWS com Terraform

## 3. Documentos obrigatórios antes de alterar

Antes de propor ou executar mudanças, o agente deve ler:

- `README.md`
- `docs/contexto.md`
- `docs/arquitetura.md`
- `docs/planejamento_fases.md`

Se a alteração tocar as Fases 9 a 12, o agente também deve ler:

- `docs/guardrail_rastreavel.md`
- `docs/genai_com_metodo.md`

Se a alteração tocar as Fases 10 a 12, o agente também deve considerar:

- `docs/matriz_cenarios_validacao.md`
- `docs/rubrica_qualidade_resposta.md`

Se a alteração estiver ligada a uma fase específica, o agente deve identificar:

- fase atual
- task relacionada
- critério de aceite
- forma de validação

## 4. Fonte de verdade

- contexto do projeto: `docs/contexto.md`
- arquitetura real: `docs/arquitetura.md`
- planejamento por fases: `docs/planejamento_fases.md`
- setup e uso atual: `README.md`
- eixo de guardrail e correlação: `docs/guardrail_rastreavel.md`
- definição do requisito: `docs/genai_com_metodo.md`
- matriz de cenários: `docs/matriz_cenarios_validacao.md`
- rubrica de qualidade: `docs/rubrica_qualidade_resposta.md`
- instruções do Copilot: `.github/copilot-instructions.md`
- agentes especializados: `.github/agents/`
- skills e workflows: `.ai/`

## 5. Regras obrigatórias

### Antes de alterar

O agente deve:

1. identificar a fase e a task
2. entender o impacto da mudança
3. listar arquivos ou áreas afetadas
4. definir como a alteração será validada
5. evitar mudanças paralelas fora do escopo
6. distinguir o que é runtime ativo, o que é contrato planejado e o que é apenas stack-alvo do case

### Durante a alteração

O agente deve:

- fazer mudanças mínimas e rastreáveis
- preservar o comportamento funcional que já foi validado
- preferir contrato explícito a fallback implícito
- tratar `tenant_id` como contrato arquitetural
- evitar reintroduzir estrutura ou naming removidos
- manter coerência entre código, runtime, documentação e critérios de aceite da fase
- usar `request_id` como contrato em evolução nos fluxos críticos tocados pelas Fases 9 a 12

### Depois da alteração

O agente deve registrar:

- o que foi alterado
- como validou
- o estado atual
- o próximo passo lógico

## 6. O que agentes nunca devem fazer

Agentes não devem:

- introduzir hardcodes de tenant, path, domínio ou base
- criar fallback silencioso para `tenant_id`
- documentar Telegram operacional, composição generativa, guardrails rastreáveis, logs estruturados, métricas, traces, CI ou deploy como ativos se ainda não estiverem implementados na base atual
- reintroduzir resíduos históricos removidos do repositório
- editar ou criar credenciais reais
- manter segredos em arquivos versionados
- expandir o escopo sem relação com a fase atual

## 7. Regras específicas do projeto

### Multi-tenant

- `tenant_id` deve ser explícito nos fluxos críticos
- ausência de tenant deve gerar erro controlado
- contexto, persistência e auditoria devem respeitar segregação por tenant
- qualquer novo canal deve preservar o mesmo contrato tenant-aware do chat direto

### GenAI com método

- RAG, policy, composição e resposta devem permanecer separáveis quando a camada generativa entrar
- `request_id` deve evoluir como contrato transversal nas Fases 9 a 12
- prompts, políticas e configurações de comportamento devem ser versionados quando forem introduzidos
- matriz de cenários e rubrica de qualidade devem orientar validações das Fases 10 a 12

### Persistência atual

- o runtime atual usa persistência local em arquivo
- histórico e auditoria são segregados por tenant
- qualquer evolução de storage deve preservar esse contrato lógico
- o repositório ativo de auditoria hoje é `app/storage/audit_repository.py`

### Docker

- o ambiente local deve continuar simples e reproduzível
- não inflar o Compose com serviços ainda não necessários

### Documentação

- toda documentação deve refletir o estado real do código
- arquitetura desejada futura deve ser marcada como futura, não como presente
- `README.md` mantém a stack-alvo do case; `docs/arquitetura.md` e `docs/contexto.md` definem o runtime real da branch
- nas Fases 9 a 12, `docs/guardrail_rastreavel.md` e `docs/genai_com_metodo.md` devem ser tratados como contratos documentais ativos

## 8. Estrutura de saída esperada

Toda resposta operacional do agente deve terminar com:

- arquivos alterados
- validação executada
- status atual
- próximo passo

## 9. Se houver bloqueio

O agente deve informar:

- onde está o bloqueio
- por que ele existe
- qual dependência falta
- qual o menor próximo passo ainda válido

## 10. Estrutura recomendada de agentes

Os agentes ativos do projeto devem continuar poucos e claros:

- `backend-architect.agent.md`
- `rag-ml.agent.md`
- `devops-platform.agent.md`
- `qa-validation.agent.md`
- `docs-operator.agent.md`

## 11. Estratégia mínima de validação

Toda alteração relevante deve indicar pelo menos uma destas validações:

- startup do backend
- validação de `/`, `/health` e `/api/chat`
- validação de `/api/webhook`
- validação de `/api/rag/status`
- validação do fluxo de tenant
- validação da persistência por tenant
- validação da auditoria por tenant
- validação de smoke tests quando a task tocar tenant demonstrativo, RAG ou canal
- `pytest`
- `docker compose config`
- `docker compose up`

## 12. Regra final

Este projeto deve evoluir com:

- menos improviso
- mais contrato
- menos herança implícita
- mais evidência
- menos promessa
- mais coerência entre código, runtime e documentação

Se houver conflito entre fazer rápido e manter o sistema explicável, a prioridade é manter o sistema explicável.
