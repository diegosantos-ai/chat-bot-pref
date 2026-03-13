# AGENTS.md

## 1. Propósito deste arquivo
Este arquivo define as regras operacionais para agentes de IA que atuam neste repositório.

Ele **não** é changelog, não é documentação completa de arquitetura e não substitui os documentos de contexto do projeto.

A função deste arquivo é orientar como agentes devem:
- entender o projeto
- planejar alterações
- executar mudanças com segurança
- validar resultados
- manter coerência entre código, runtime e documentação

---

## 2. Objetivo atual do projeto
Este repositório mantém a evolução do **Chat Pref**, uma plataforma de atendimento digital com IA aplicada ao setor público, com foco em:

- backend FastAPI
- arquitetura tenant-aware
- RAG com base documental por tenant
- guardrails e auditoria
- operação local reproduzível com Docker
- demonstração funcional via tenant fictício
- canal real de demonstração via Telegram
- observabilidade, CI/CD e futura publicação em AWS com Terraform

O objetivo atual não é expandir escopo indiscriminadamente.  
O foco é **refatorar, estabilizar, operacionalizar e demonstrar** o sistema com clareza arquitetural e evidências reais.

---

## 3. Documentos obrigatórios antes de qualquer alteração
Antes de propor ou executar mudanças, o agente deve ler os arquivos abaixo:

- `contexto.md`
- `arquitetura.md`
- `planejamento_fases.md` ou documento equivalente de planejamento por fases
- `README.md`

Se a alteração impactar uma fase específica, o agente deve identificar:
- fase atual
- task relacionada
- critério de aceite
- forma de validação

---

## 4. Fonte de verdade por tipo de assunto
- **Contexto do projeto:** `contexto.md`
- **Arquitetura real:** `arquitetura.md`
- **Planejamento e execução:** `planejamento-trello.md`
- **Setup e uso geral:** `README.md`
- **Instruções do Copilot:** `.github/copilot-instructions.md`
- **Perfis especializados de agente:** `.github/agents/`
- **Skills reutilizáveis:** `.ai/skills/`
- **Workflows operacionais:** `.ai/workflows/`

Este arquivo deve permanecer curto e estável.

---

## 5. Regras obrigatórias para agentes

### 5.1. Antes de alterar qualquer coisa
O agente deve:
1. identificar a fase e a task relacionadas
2. entender o impacto da mudança
3. listar arquivos ou áreas afetadas
4. definir como a alteração será validada
5. evitar mudanças paralelas fora do escopo

### 5.2. Durante a alteração
O agente deve:
- fazer mudanças mínimas e rastreáveis
- preservar o comportamento funcional sempre que possível
- evitar refatorações oportunistas fora da task
- preferir configuração explícita a default implícito
- tratar `tenant_id` como contrato arquitetural, não como detalhe incidental

### 5.3. Depois da alteração
O agente deve registrar:
- o que foi alterado
- como validou
- o estado atual
- o próximo passo lógico

---

## 6. O que agentes nunca devem fazer
Agentes **não devem**:

- introduzir hardcodes de path, domínio, base ou tenant
- criar fallback silencioso para `tenant_id`
- mascarar erro estrutural com comportamento “neutro”
- alterar documentação para prometer algo ainda não validado
- editar ou criar credenciais reais no repositório
- manter segredos em arquivos versionados
- modificar várias frentes ao mesmo tempo sem necessidade
- expandir o escopo do projeto sem relação com a fase atual
- tratar a demo como produto final enterprise
- reintroduzir identidade, contatos ou resíduos históricos do projeto legado

---

## 7. Regras específicas do projeto

### 7.1. Multi-tenant
- `tenant_id` deve ser explícito nos fluxos críticos
- nenhuma operação crítica deve depender de tenant implícito
- RAG, auditoria e persistência devem respeitar o contexto de tenant
- ausência de tenant deve gerar erro controlado ou tratamento explícito

### 7.2. RAG
- não usar base legada ou collection hardcoded
- ingest deve ser tenant-aware
- ausência de base deve ser tratada de forma segura e rastreável
- respostas devem respeitar escopo institucional e contexto recuperado

### 7.3. Demo
- a prefeitura demonstrativa deve ser fictícia
- os dados devem ser fictícios e plausíveis
- o escopo do assistente é estritamente informativo
- Telegram é canal de demonstração, não produto final obrigatório

### 7.4. Docker / CI / AWS
- ambiente local deve ser reproduzível com Docker
- CI deve validar o que já é confiável, sem teatro
- AWS/Terraform devem seguir arquitetura mínima e explicável
- não criar infraestrutura excessiva para um case demonstrativo

---

## 8. Convenções de trabalho para agentes

### 8.1. Estrutura de saída esperada ao final de uma tarefa
Toda resposta operacional do agente deve terminar com algo equivalente a:

- arquivos alterados
- validação executada
- status atual
- próximo passo

### 8.2. Se houver bloqueio
O agente deve informar:
- onde está o bloqueio
- por que ele existe
- qual dependência falta
- qual menor próximo passo possível continua válido

### 8.3. Se a mudança for estrutural
Sempre atualizar os documentos correspondentes quando houver impacto real em:
- arquitetura
- contrato de tenant
- ingest
- Docker
- GitHub Actions
- Terraform/AWS
- fluxo operacional da demo

---

## 9. Estrutura recomendada de agentes neste repositório
Os agentes ativos deste projeto devem ser poucos e com função clara:

- `backend-architect.agent.md`
- `rag-ml.agent.md`
- `devops-platform.agent.md`
- `qa-validation.agent.md`
- `docs-operator.agent.md`

Não criar novos agentes sem necessidade real.

---

## 10. Estratégia de validação mínima
Toda alteração relevante deve indicar pelo menos uma destas validações:

- subida do backend
- validação de endpoints principais
- validação do fluxo de tenant
- validação do retrieval/RAG
- validação da demo via Telegram
- validação de logs/métricas
- build Docker
- execução de testes automatizados
- execução da pipeline de CI

---

## 11. Segurança e segredos
Nunca manter no repositório:
- `.env` real
- tokens de API
- credenciais OAuth reais
- chaves privadas
- arquivos de credenciais em áreas ativas do projeto

Se forem encontrados arquivos desse tipo:
- remover da estrutura ativa
- sugerir rotação de segredo
- substituir por exemplo seguro, quando necessário

---

## 12. Regra final
Este projeto deve evoluir com:
- menos improviso
- mais contrato
- menos agente genérico
- mais evidência
- menos contexto espalhado
- mais governança por arquivos claros e versionados

Se houver conflito entre “fazer rápido” e “manter o sistema explicável”, a prioridade é manter o sistema explicável.