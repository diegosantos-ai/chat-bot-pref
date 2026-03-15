# AGENTS.md

## 1. Propósito

Este arquivo define as regras operacionais para agentes de IA que atuam neste repositório.

Ele não substitui:

- `README.md`
- `docs-fundacao-operacional/`
- `docs-LLMOps/`

Sua função é orientar como agentes devem ler o projeto, localizar o ciclo correto, planejar mudanças, executar alterações e validar resultados com coerência entre código, runtime, arquitetura e documentação.

---

## 2. Estrutura atual do projeto

O projeto passa a ser organizado em dois ciclos documentais complementares:

### Fundação Operacional
Documenta a base funcional já validada do sistema, incluindo runtime principal, contratos ativos, observabilidade mínima, auditoria, CI e deploy remoto demonstrativo.

Documentação principal:
- `docs-fundacao-operacional/`

### Fase 1 — LLMOps, Avaliação e Governança
Documenta a nova etapa de evolução do projeto, focada em:
- rastreabilidade experimental por tenant;
- versionamento formal de prompts, policies e configurações de RAG;
- benchmark reproduzível;
- avaliação formal de RAG;
- observabilidade de qualidade, latência e custo;
- orquestração offline;
- deriva semântica;
- governança e explicabilidade técnica.

Documentação principal:
- `docs-LLMOps/`

---

## 3. Objetivo atual do projeto

O projeto possui uma **Fundação Operacional concluída e validada** e passa agora por uma nova fase de evolução técnica orientada a **LLMOps, avaliação formal, governança e observabilidade avançada**.

### Base validada atual
O runtime ativo atual tem foco em:

- FastAPI com `GET /`, `GET /health`, `POST /api/chat`, `POST /api/webhook` e endpoints RAG
- webhook demonstrativo do Telegram em `POST /api/telegram/webhook`
- contrato explícito de `tenant_id`
- contrato mínimo de `request_id` nos fluxos HTTP críticos
- contexto de tenant por request
- persistência local por tenant
- auditoria versionada `audit.v1` por tenant
- RAG tenant-aware com ingest limpa
- composição generativa mínima com adaptador LLM isolado
- prompts e política textual versionados
- `PolicyDecision` ativo em `policy_pre` e `policy_post`
- logs estruturados correlacionados
- `/metrics` exposto
- traces OpenTelemetry persistidos por `request_id`
- tenant demonstrativo versionado
- execução local e via Docker com smoke tests
- workflow de CI versionado com quality gates, build Docker e smoke mínimo
- deploy remoto mínimo validado em AWS com Terraform, EC2 única, Docker e smoke remoto
- endpoint HTTPS público estável validado no ambiente remoto demonstrativo
- bot Telegram com webhook HTTPS ativo no ambiente remoto demonstrativo

### Itens ainda não pertencentes ao núcleo plenamente validado da nova fase
Os itens abaixo não devem ser tratados como ativos no runtime apenas por estarem planejados ou documentados na fase LLMOps:

- experiment tracking plenamente integrado ao runtime
- benchmark reproduzível já operando como contrato ativo
- avaliação formal de RAG já consolidada
- Airflow operando como camada offline ativa
- monitoramento de deriva semântica em produção
- multi-LLM validado como caminho padrão reproduzível
- deploy remoto endurecido com domínio próprio, secrets gerenciados e CD completo

---

## 4. Documentos obrigatórios antes de alterar

Antes de propor ou executar mudanças, o agente deve ler:

- `README.md`

### Se a alteração tocar a base validada do runtime
Ler também:
- `docs-fundacao-operacional/contexto.md`
- `docs-fundacao-operacional/arquitetura.md`
- `docs-fundacao-operacional/planejamento_fases.md`

### Se a alteração tocar a nova fase de LLMOps
Ler também:
- `docs-LLMOps/README.md`
- `docs-LLMOps/CONTEXTO-LLMOps.md`
- `docs-LLMOps/ARQUITETURA-LLMOps.md`
- `docs-LLMOps/PLANEJAMENTO_LLMOps.md`

### Se a alteração tocar decisões arquiteturais da fase LLMOps
Ler também os ADRs aplicáveis em:
- `docs-LLMOps/adrs/`

### Se a alteração tocar setup, avaliação ou operação offline
Ler também os runbooks aplicáveis em:
- `docs-LLMOps/runbooks/`

### Se a alteração tocar as fases finais da Fundação Operacional
O agente também deve considerar:
- `docs-fundacao-operacional/guardrail_rastreavel.md`
- `docs-fundacao-operacional/genai_com_metodo.md`

### Se a alteração tocar validação de resposta e cenários da Fundação Operacional
O agente também deve considerar:
- `docs-fundacao-operacional/matriz_cenarios_validacao.md`
- `docs-fundacao-operacional/rubrica_qualidade_resposta.md`

### Se a alteração tocar infraestrutura, evidências ou narrativa técnica da Fundação Operacional
O agente também deve considerar:
- `docs-fundacao-operacional/fase_13_aws_deploy.md`
- `docs-fundacao-operacional/evidencias_case.md`
- `docs-fundacao-operacional/diario_bordo.md`

Se a alteração estiver ligada a uma fase específica, o agente deve identificar:

- ciclo atual
- fase atual
- task relacionada
- critério de aceite
- forma de validação

---

## 5. Fonte de verdade

### Navegação principal
- setup e visão geral: `README.md`

### Fundação Operacional
- contexto do ciclo validado: `docs-fundacao-operacional/contexto.md`
- arquitetura real da base validada: `docs-fundacao-operacional/arquitetura.md`
- planejamento do ciclo operacional: `docs-fundacao-operacional/planejamento_fases.md`
- eixo de guardrail e correlação: `docs-fundacao-operacional/guardrail_rastreavel.md`
- definição do requisito: `docs-fundacao-operacional/genai_com_metodo.md`
- matriz de cenários: `docs-fundacao-operacional/matriz_cenarios_validacao.md`
- rubrica de qualidade: `docs-fundacao-operacional/rubrica_qualidade_resposta.md`

### Fase LLMOps
- visão geral da fase: `docs-LLMOps/README.md`
- contexto da fase: `docs-LLMOps/CONTEXTO-LLMOps.md`
- arquitetura-alvo da fase: `docs-LLMOps/ARQUITETURA-LLMOps.md`
- planejamento da fase: `docs-LLMOps/PLANEJAMENTO_LLMOps.md`
- decisões arquiteturais: `docs-LLMOps/adrs/`
- runbooks operacionais: `docs-LLMOps/runbooks/`

### Governança auxiliar
- instruções do Copilot: `.github/copilot-instructions.md`
- skills nativas do Codex: `.codex/skills/`
- agentes especializados: `.github/agents/`
- skills e workflows: `.ai/`

---

## 6. Regras obrigatórias

### Antes de alterar

O agente deve:

1. identificar o ciclo e a fase
2. entender o impacto da mudança
3. listar arquivos ou áreas afetadas
4. definir como a alteração será validada
5. evitar mudanças paralelas fora do escopo
6. distinguir o que é:
   - runtime ativo validado;
   - contrato já consolidado;
   - arquitetura-alvo da fase LLMOps;
   - item apenas planejado

### Durante a alteração

O agente deve:

- fazer mudanças mínimas e rastreáveis
- preservar o comportamento funcional já validado
- preferir contrato explícito a fallback implícito
- tratar `tenant_id` como contrato arquitetural
- evitar reintroduzir estrutura ou naming removidos
- manter coerência entre código, runtime, documentação e critérios de aceite
- usar `request_id` como contrato transversal consolidado
- preservar a separação entre:
  - operação;
  - experimentação;
  - benchmark;
  - orquestração offline

### Depois da alteração

O agente deve registrar:

- o que foi alterado
- como validou
- o estado atual
- o próximo passo lógico

---

## 7. O que agentes nunca devem fazer

Agentes não devem:

- introduzir hardcodes de tenant, path, domínio ou base
- criar fallback silencioso para `tenant_id`
- documentar como ativo algo que ainda esteja apenas na arquitetura-alvo da fase LLMOps
- confundir auditoria operacional com experiment tracking
- reintroduzir resíduos históricos removidos do repositório
- editar ou criar credenciais reais
- manter segredos em arquivos versionados
- expandir o escopo sem relação com a fase atual
- tratar stack-alvo como runtime ativo sem validação correspondente

---

## 8. Regras específicas do projeto

### Multi-tenant

- `tenant_id` deve ser explícito nos fluxos críticos
- ausência de tenant deve gerar erro controlado
- contexto, persistência, avaliação e auditoria devem respeitar segregação por tenant
- qualquer novo canal deve preservar o mesmo contrato tenant-aware do chat direto
- qualquer nova camada de tracking ou benchmark deve manter leitura isolável por tenant

### GenAI com método

- RAG, policy, composição e resposta devem permanecer separáveis
- `request_id` deve permanecer como contrato transversal
- prompts, políticas e configurações críticas devem permanecer versionáveis
- benchmark e avaliação formal devem ser tratados como contratos da fase LLMOps, não como adição cosmética
- mudanças em comportamento relevante devem ser comparáveis e justificáveis

### Auditoria vs. experimentação

- auditoria operacional e experiment tracking devem permanecer separados
- auditoria registra fatos operacionais do atendimento
- tracking experimental registra comparação técnica entre versões, métricas e artifacts
- nenhuma alteração deve fundir essas camadas por conveniência

### Persistência atual

- o runtime atual usa persistência local em arquivo para a base operacional validada
- histórico e auditoria são segregados por tenant
- qualquer evolução de storage deve preservar esse contrato lógico
- o repositório ativo de auditoria hoje é `app/storage/audit_repository.py`

### Docker

- o ambiente local deve continuar simples e reproduzível
- não inflar o Compose com serviços ainda não necessários
- Airflow e demais componentes offline devem permanecer fora do runtime principal até a fase apropriada

### Documentação

- toda documentação deve refletir o estado real do código
- arquitetura desejada futura deve ser marcada como futura, não como presente
- `README.md` posiciona o projeto como ponte entre Fundação Operacional e Fase 1
- `docs-fundacao-operacional/` registra a base validada
- `docs-LLMOps/` registra a nova fase de evolução
- nas decisões e runbooks da fase LLMOps, preservar distinção entre:
  - estado atual;
  - arquitetura-alvo;
  - capacidade ainda não implantada

---

## 9. Estrutura de saída esperada

Toda resposta operacional do agente deve terminar com:

- arquivos alterados
- validação executada
- status atual
- próximo passo

---

## 10. Se houver bloqueio

O agente deve informar:

- onde está o bloqueio
- por que ele existe
- qual dependência falta
- qual o menor próximo passo ainda válido

---

## 11. Estrutura recomendada de agentes

Os agentes ativos do projeto devem continuar poucos e claros:

- `backend-architect.agent.md`
- `rag-ml.agent.md`
- `devops-platform.agent.md`
- `qa-validation.agent.md`
- `docs-operator.agent.md`

---

## 12. Estratégia mínima de validação

Toda alteração relevante deve indicar pelo menos uma destas validações:

### Runtime principal
- startup do backend
- validação de `/`, `/health` e `/api/chat`
- validação de `/api/webhook`
- validação de `/api/rag/status`
- validação do fluxo de tenant
- validação da persistência por tenant
- validação da auditoria por tenant

### Base operacional e integração
- validação de smoke tests quando a task tocar tenant demonstrativo, RAG ou canal
- `scripts/lint_runtime.py`
- `scripts/check_runtime_residues.py`
- `pytest`
- `docker build`
- `docker compose config`
- `docker compose up`

### Nova fase de LLMOps
Quando aplicável:
- validação do ambiente base e dev
- validação de imports das dependências da fase
- validação de benchmark
- validação de tracking experimental
- validação de versionamento de artefatos
- validação de ambiente offline
- validação de correlação entre contexto operacional e execução experimental

---

## 13. Regra final

Este projeto deve evoluir com:

- menos improviso
- mais contrato
- menos herança implícita
- mais evidência
- menos promessa
- mais coerência entre código, runtime e documentação

Se houver conflito entre fazer rápido e manter o sistema explicável, a prioridade é manter o sistema explicável.
