# Trello — Cards Macros e Tasks

## Card Macro — Fase 1 — Diagnóstico e Inventário do Legado

### Objetivo da fase
Mapear resíduos mono-tenant, hardcodes, defaults antigos, acoplamentos invisíveis e inconsistências entre código, documentação e operação.

### Resultado esperado
Inventário confiável do que precisa ser removido, substituído ou reestruturado antes da evolução arquitetural.

### Critério de aceite
- termos legados identificados
- áreas críticas mapeadas
- arquivos de maior risco listados
- próximos cortes definidos com prioridade
- componentes críticos classificados por impacto em runtime

### Riscos
- análise superficial
- deixar resíduo oculto em scripts auxiliares
- ignorar acoplamentos operacionais
- não separar resíduo cosmético de resíduo funcional

### Dependências
- acesso ao repositório completo
- leitura inicial da estrutura e dos arquivos críticos

### Observações
Nenhuma limpeza ampla deve ocorrer antes do fechamento do inventário. O foco desta fase é distinguir o que é problema de apresentação do que realmente quebra operação.

#### Andamento do planejamento
Registro da execução da fase, guia de evolução do projeto. Caso conclúida `[x]`
seguir para a próxima fase.

- [x] Fase 1 — Diagnóstico e Inventário do Legado
- [x] Fase 2 — Sanitização Funcional do Runtime
- [x] Fase 3 — Consolidação do Contrato Multi-Tenant
- [x] Fase 4 — Reset da Base RAG e Reingestão Limpa
- [x] Fase 5 — Containerização e Ambiente Local Reproduzível
- [x] Fase 6 — Validação Estrutural da Base Refatorada
- [x] Fase 7 — Construção do Tenant Demonstrativo Fictício
- [x] Fase 8 — Construção da Base Documental Fictícia e Ingest Limpa
- [x] Fase 9 — Operacionalização do Chat via Telegram
- [x] Fase 10 — Composição Generativa, Guardrails e Evidências
- [x] Fase 11 — Observabilidade Aplicada e Fechamento Técnico do Case
- [x] Fase 12 — Automação de Qualidade com GitHub Actions
- [x] Fase 13 — Infraestrutura como Código e Deploy em AWS
- [ ] Fase 14 — Alinhamento Final entre Arquitetura, Operação e Documentação


#### Tasks — Fase 1

- `CPP-F1-T1 — Inventariar resíduos mono-tenant`
- `CPP-F1-T2 — Localizar hardcodes de path e domínio`
- `CPP-F1-T3 — Mapear defaults legados de base e collection`
- `CPP-F1-T4 — Identificar scripts críticos de operação e deploy`
- `CPP-F1-T5 — Registrar arquivos sensíveis e pontos de risco`
- `CPP-F1-T6 — Separar resíduos funcionais de resíduos cosméticos`
- `CPP-F1-T7 — Consolidar inventário técnico da refatoração`

---

## Card Macro — Fase 2 — Sanitização Funcional do Runtime

### Objetivo da fase
Remover hardcodes, defaults históricos e dependências operacionais legadas que impactam execução real.

### Resultado esperado
Backend, painel e scripts principais operando sem dependência estrutural do projeto original.

### Critério de aceite
- ausência de paths, domínios e bases antigas em componentes críticos
- aplicação sobe sem acoplamento legível ao legado
- painel/admin não depende de base fixa antiga
- scripts operacionais não apontam para paths históricos
- falhas por ausência de configuração são explícitas e controladas

### Riscos
- quebrar startup
- remover referência sem substituir por configuração válida
- limpar apenas a superfície e manter dependência invisível
- criar defaults neutros, mas ainda perigosos

### Dependências
- fase 1 concluída
- padrão de configuração alvo definido

### Observações
Priorizar backend, painel e scripts de runtime. Documentação ampla não entra como foco desta fase.

#### Tasks — Fase 2

- `CPP-F2-T1 — Remover hardcodes de runtime no backend`
- `CPP-F2-T2 — Remover defaults legados do painel admin`
- `CPP-F2-T3 — Sanitizar scripts operacionais e systemd`
- `CPP-F2-T4 — Revisar compose e serviços auxiliares`
- `CPP-F2-T5 — Neutralizar domínios e contatos legados`
- `CPP-F2-T6 — Revisar variáveis e fontes de configuração`
- `CPP-F2-T7 — Validar startup sem dependência histórica`

---

## Card Macro — Fase 3 — Consolidação do Contrato Multi-Tenant

### Objetivo da fase
Tornar tenant_id um contrato explícito e consistente nos fluxos principais.

### Resultado esperado
Resolução, propagação e uso de tenant coerentes entre chat, webhook, RAG, auditoria e persistência.

### Critério de aceite
- fluxo de tenant definido arquiteturalmente
- endpoint de chat com estratégia clara de resolução de tenant
- webhook sem associação frágil de tenant
- retrieval e auditoria operando com tenant consistente
- ausência de tenant gera erro controlado ou fallback explícito

### Riscos
- tenant implícito ou default silencioso
- divergência entre webhook e chat
- isolamento incompleto entre camadas
- vazamento lógico por uso incorreto de contexto

### Dependências
- fase 2 concluída
- definição do mecanismo de entrada de tenant no chat

### Observações
Nenhum fluxo crítico deve depender de tenant herdado por sorte ou base default.

#### Tasks — Fase 3

- `CPP-F3-T1 — Definir contrato de entrada de tenant_id`
- `CPP-F3-T2 — Tornar tenant_id explícito no endpoint de chat`
- `CPP-F3-T3 — Corrigir resolução de tenant no webhook`
- `CPP-F3-T4 — Revisar tenant_context e propagação assíncrona`
- `CPP-F3-T5 — Validar retrieval por tenant no ChromaDB`
- `CPP-F3-T6 — Validar auditoria com contexto de tenant`
- `CPP-F3-T7 — Revisar falhas silenciosas de tenant default`
- `CPP-F3-T8 — Documentar contrato operacional de tenant`

---

## Card Macro — Fase 4 — Reset da Base RAG e Reingestão Limpa

### Objetivo da fase
Eliminar herança semântica antiga e preparar o projeto para nova ingestão neutra e controlada.

### Resultado esperado
Estrutura RAG limpa, sem base legada fixa, pronta para ingest por tenant.

### Critério de aceite
- collections antigas removidas ou desacopladas
- ingest sem base hardcoded
- admin/painel operando com nova lógica
- retrieval falha de forma controlada quando não houver base
- estrutura mínima de ingest estável para novos tenants

### Riscos
- apagar base sem preservar estrutura mínima
- quebrar fluxo de teste
- manter referências antigas em scripts de ingest
- mascarar erro de ingest com fallback silencioso

### Dependências
- fase 3 concluída ou estabilizada

### Observações
A falha sem base carregada deve ser controlada, explícita e rastreável.

#### Tasks — Fase 4

- `CPP-F4-T1 — Resetar bases RAG legadas`
- `CPP-F4-T2 — Remover base hardcoded do fluxo de ingest`
- `CPP-F4-T3 — Revisar scripts de coleção e contagem`
- `CPP-F4-T4 — Ajustar painel admin para ingest tenant-aware`
- `CPP-F4-T5 — Validar comportamento sem base carregada`
- `CPP-F4-T6 — Preparar estrutura mínima para nova ingestão`
- `CPP-F4-T7 — Definir contrato de ingest por tenant`

---

## Card Macro — Fase 5 — Containerização e Ambiente Local Reproduzível

### Objetivo da fase
Consolidar a execução local do projeto em ambiente reproduzível, com Docker e Compose consistentes para desenvolvimento, teste e demonstração.

### Resultado esperado
Projeto sobe localmente com backend e dependências principais de forma previsível, padronizada e validável.

### Critério de aceite
- Dockerfile funcional e coerente com o runtime
- docker-compose limpo e sem legado estrutural
- serviços principais sobem com configuração previsível
- healthchecks e startup básico validados
- ambiente local permite testar chat, ingest e tenant demonstrativo

### Riscos
- compose inflado com serviços irrelevantes
- startup local quebrar por dependência implícita
- diferenças entre ambiente local e fluxo real do projeto
- containerização esconder problema estrutural em vez de resolvê-lo

### Dependências
- fases 2, 3 e 4 estabilizadas

### Observações
Esta fase é a base para a demonstração do projeto e para o CI. Sem execução local reproduzível, o restante vira castelo de fumaça.

#### Tasks — Fase 5

- `CPP-F5-T1 — Revisar Dockerfile do backend`
- `CPP-F5-T2 — Revisar docker-compose principal`
- `CPP-F5-T3 — Padronizar variáveis de ambiente para containers`
- `CPP-F5-T4 — Adicionar healthchecks dos serviços principais`
- `CPP-F5-T5 — Validar subida local ponta a ponta`
- `CPP-F5-T6 — Documentar bootstrap local mínimo`

---

## Card Macro — Fase 6 — Validação Estrutural da Base Refatorada

### Objetivo da fase
Executar uma validação intermediária da base refatorada antes de construir o tenant demonstrativo.

### Resultado esperado
Projeto em estado tecnicamente confiável para receber dados novos, tenant demonstrativo e canal real de operação.

### Critério de aceite
- buscas por termos proibidos sem resultado relevante em runtime
- backend sobe
- endpoints principais respondem
- fluxo principal não depende de legado
- compose local validado
- tenant-aware validado no mínimo funcional

### Riscos
- confiar em validação parcial
- ignorar regressões
- avançar para demo sem base estrutural sólida

### Dependências
- fases 1 a 5 concluídas ou estabilizadas

### Observações
Esta fase não fecha o projeto; ela fecha a refatoração estrutural e abre o caminho para a demonstração real.

#### Tasks — Fase 6

- `CPP-F6-T1 — Executar varredura intermediária de resíduos históricos`
- `CPP-F6-T2 — Validar startup do backend após refatoração`
- `CPP-F6-T3 — Validar endpoints principais`
- `CPP-F6-T4 — Validar integração mínima de tenant no fluxo`
- `CPP-F6-T5 — Revisar diff da refatoração estrutural`
- `CPP-F6-T6 — Consolidar evidências da base estabilizada`

---

## Card Macro — Fase 7 — Construção do Tenant Demonstrativo Fictício

### Objetivo da fase
Criar um tenant institucional fictício, coerente e reutilizável, para servir como base oficial de demonstração da plataforma.

### Resultado esperado
Um tenant demonstrativo funcional, com identidade neutra, configuração própria, escopo definido e estrutura mínima pronta para operação.

### Critério de aceite
- nome do tenant definido e padronizado
- identidade textual institucional criada
- configuração do tenant criada sem hardcodes
- escopo do assistente documentado
- estrutura inicial do tenant preparada para ingest

### Riscos
- criar identidade inconsistente entre docs e configuração
- misturar dados reais com dados fictícios
- deixar o tenant dependente de defaults globais

### Dependências
- fase 6 concluída
- contrato multi-tenant estabilizado

### Observações
O tenant demonstrativo deve representar uma prefeitura fictícia plausível, com linguagem institucional clara e escopo estritamente informativo.

#### Tasks — Fase 7

- `CPP-F7-T1 — Definir nome e identidade da prefeitura fictícia`
- `CPP-F7-T2 — Definir escopo informativo do assistente`
- `CPP-F7-T3 — Criar configuração inicial do tenant demonstrativo`
- `CPP-F7-T4 — Preparar estrutura de base documental do tenant`
- `CPP-F7-T5 — Criar documento institucional de limites e disclaimer`
- `CPP-F7-T6 — Validar coerência entre tenant, config e arquitetura`

---

## Card Macro — Fase 8 — Construção da Base Documental Fictícia e Ingest Limpa

### Objetivo da fase
Criar uma base documental fictícia, pequena e bem estruturada, e realizar a ingest limpa para o tenant demonstrativo.

### Resultado esperado
Tenant com base RAG própria, composta por documentos institucionais fictícios, adequados para recuperação semântica e demonstração do sistema.

### Critério de aceite
- documentos fictícios criados e organizados
- base cobre os principais temas da prefeitura fictícia
- ingest executada sem acoplamento legado
- retrieval retorna contexto útil para perguntas controladas
- ausência de base é tratada de forma controlada antes da ingest

### Riscos
- documentos mal escritos prejudicarem o RAG
- ingest ainda depender de base ou path antigo
- base ser pequena demais para demonstrar valor
- base ser grande demais e atrasar a entrega

### Dependências
- fase 7 concluída
- fluxo de ingest tenant-aware funcional

### Observações
A base documental deve ser enxuta e intencional. O objetivo é demonstrar qualidade de arquitetura e retrieval, não volume artificial.

#### Tasks — Fase 8

- `CPP-F8-T1 — Definir conjunto mínimo de documentos fictícios`
- `CPP-F8-T2 — Criar documentos de atendimento e contatos oficiais`
- `CPP-F8-T3 — Criar documentos de serviços municipais prioritários`
- `CPP-F8-T4 — Criar documentos de FAQ e procedimentos informativos`
- `CPP-F8-T5 — Organizar estrutura de arquivos para ingest`
- `CPP-F8-T6 — Executar ingest limpa do tenant demonstrativo`
- `CPP-F8-T7 — Validar retrieval com perguntas controladas`
- `CPP-F8-T8 — Ajustar documentos com base nos primeiros resultados`

---

## Card Macro — Fase 9 — Operacionalização do Chat via Telegram

### Objetivo da fase
Disponibilizar um canal real de demonstração para o tenant fictício, permitindo validar o fluxo ponta a ponta do chat em um ambiente acessível e reproduzível.

### Resultado esperado
Chat operacional no Telegram, integrado ao backend da plataforma, com fluxo funcional de entrada, processamento e resposta.

### Critério de aceite
- bot Telegram criado e configurado
- integração backend ↔ Telegram implementada
- tenant demonstrativo acessível via Telegram
- mensagens simples respondidas corretamente
- logs e auditoria registram as interações com correlação mínima por `request_id`, `tenant_id`, `channel`, `chat_id`, `message_id` e `update_id`
- comportamento do Telegram consistente com o fluxo principal de `POST /api/chat`

### Riscos
- acoplamento excessivo do canal à lógica principal
- falhas de configuração do bot
- ausência de rastreabilidade das conversas
- comportamento divergente entre /api/chat e fluxo do Telegram

### Dependências
- fases 7 e 8 concluídas
- backend estável após refatoração
- ambiente local reproduzível validado

### Observações
O Telegram deve ser tratado como canal demonstrativo operacional do núcleo da plataforma, e não como produto final definitivo.

#### Tasks — Fase 9

- `CPP-F9-T1 — Definir estratégia de integração com Telegram`
- `CPP-F9-T2 — Criar e configurar bot de demonstração`
- `CPP-F9-T3 — Implementar entrada de mensagens do Telegram`
- `CPP-F9-T4 — Integrar Telegram ao fluxo principal de chat`
- `CPP-F9-T5 — Garantir associação do Telegram ao tenant demonstrativo`
- `CPP-F9-T6 — Registrar auditoria correlacionada das conversas via Telegram`
- `CPP-F9-T7 — Validar fluxo ponta a ponta com perguntas reais e consistência com /api/chat`
- `CPP-F9-T8 — Corrigir inconsistências do canal demonstrativo`

---

## Card Macro — Fase 10 — Composição Generativa, Guardrails e Evidências

### Objetivo da fase
Introduzir a camada generativa mínima do projeto, com composição controlada sobre o contexto recuperado, guardrails executáveis e evidências rastreáveis.

### Resultado esperado
Assistente operando com composição generativa controlada, prompts e políticas versionados, decisões auditáveis e cenários validados com rastreabilidade por request.

### Critério de aceite
- adaptador de provedor LLM implementado e isolado do restante da aplicação
- composição de resposta limitada ao contexto recuperado e ao escopo institucional
- prompts e políticas versionados
- `policy_pre` e `policy_post` executados com `reason_codes`
- cenários normais, fora de escopo, baixa confiança e risco validados
- evidências registradas com correlação mínima por `request_id`
- comportamento alinhado ao escopo institucional do tenant fictício

### Riscos
- acoplar o provedor LLM diretamente ao fluxo principal
- introduzir composição generativa sem limite claro de contexto e escopo
- validar cenários sem versionar prompt, policy e evidência
- falta de consistência entre resposta, guardrail e auditoria

### Dependências
- fase 9 concluída

### Observações
Esta fase marca a entrada da camada generativa mínima do case. Ate aqui, o projeto continua sendo retrieval-first; a partir daqui, passa a demonstrar GenAI controlada.

#### Tasks — Fase 10

- `CPP-F10-T1 — Definir contrato da composição generativa e do adaptador LLM`
- `CPP-F10-T2 — Versionar prompt base, prompt de fallback e política textual`
- `CPP-F10-T3 — Implementar composição de resposta sobre contexto recuperado`
- `CPP-F10-T4 — Implementar PolicyDecision padronizado`
- `CPP-F10-T5 — Implementar AuditEvent versionado e persistência rastreável`
- `CPP-F10-T6 — Definir matriz de cenários de validação e rubrica de qualidade`
- `CPP-F10-T7 — Validar cenários normais, fora de escopo, baixa confiança e risco`
- `CPP-F10-T8 — Consolidar evidências e tabela de resultados por request_id`

---

## Card Macro — Fase 11 — Observabilidade Aplicada e Fechamento Técnico do Case

### Objetivo da fase
Consolidar uma visão operacional mínima do sistema em funcionamento, com observabilidade útil, rastreabilidade do fluxo e material técnico pronto para demonstração profissional.

### Resultado esperado
Projeto demonstrável com evidências de operação, logs, métricas, fluxo rastreável e narrativa técnica pronta para portfólio, currículo e entrevista.

### Critério de aceite
- logs estruturados acessíveis e correlacionados ao audit trail
- métricas básicas expostas e verificáveis em `/metrics`
- trilha mínima de processamento observável `request -> policy_pre -> retrieval -> compose -> policy_post -> response`
- auditoria, logs e traces usando os mesmos IDs de correlação
- fluxo do tenant demonstrativo documentado
- resumo técnico do case consolidado
- material suficiente para demonstração profissional

### Riscos
- excesso de esforço em dashboards irrelevantes
- falta de conexão entre observabilidade e valor demonstrado
- documentação final não refletir o comportamento real

### Dependências
- fases 9 e 10 concluídas ou estabilizadas

### Observações
A observabilidade desta fase deve ser suficiente para demonstrar maturidade operacional, sem expandir o projeto para complexidade desnecessária.

#### Tasks — Fase 11

- `CPP-F11-T1 — Validar logs estruturados correlacionados do fluxo de atendimento`
- `CPP-F11-T2 — Validar métricas básicas de retrieval, fallback, bloqueio e latência de composição`
- `CPP-F11-T3 — Instrumentar OpenTelemetry na trilha request → policy_pre → retrieval → compose → policy_post → resposta`
- `CPP-F11-T4 — Revisar correlação entre auditoria, logs, métricas e traces do tenant demonstrativo`
- `CPP-F11-T5 — Consolidar resumo técnico do case`
- `CPP-F11-T6 — Organizar evidências para portfólio e entrevista`
- `CPP-F11-T7 — Revisar aderência do case aos requisitos da vaga`
- `CPP-F11-T8 — Encerrar ciclo funcional da demonstração`

---

## Card Macro — Fase 12 — Automação de Qualidade com GitHub Actions

### Objetivo da fase
Automatizar validações essenciais do projeto para reduzir regressões e demonstrar disciplina de engenharia.

### Resultado esperado
Pipeline de CI funcional executando checks técnicos relevantes sobre o projeto.

### Critério de aceite
- workflow de CI criado e versionado
- lint, testes e validações mínimas executados automaticamente
- build Docker validado no pipeline
- varredura anti-resíduos históricos automatizada
- schema de auditoria e campos obrigatórios validados automaticamente
- matriz de cenários controlados executada automaticamente
- regressões de comportamento e rastreabilidade bloqueiam o pipeline
- falhas relevantes bloqueiam o pipeline

### Riscos
- pipeline lenta demais para o estágio atual do projeto
- checks irrelevantes aumentarem custo sem valor
- CI mascarar testes frágeis ou incompletos

### Dependências
- fases 5, 10 e 11 estabilizadas
- ambiente local e build Docker confiáveis

### Observações
Esta fase deve focar em CI. CD só entra quando houver alvo de deploy estável.
No corte atual, o workflow pode operar sem secrets novos obrigatorios, usando `LLM_PROVIDER=mock` e smoke reduzido sobre o runtime local do runner.

#### Tasks — Fase 12

- `CPP-F12-T1 — Definir escopo mínimo da pipeline de CI`
- `CPP-F12-T2 — Criar workflow de lint e testes`
- `CPP-F12-T3 — Adicionar validação de build Docker`
- `CPP-F12-T4 — Automatizar varredura de termos proibidos`
- `CPP-F12-T5 — Automatizar validação do schema de auditoria e campos obrigatórios`
- `CPP-F12-T6 — Adicionar regressão de request_id, tenant_id, reason_codes e integridade do audit trail`
- `CPP-F12-T7 — Automatizar matriz de cenários controlados e rubrica de qualidade`
- `CPP-F12-T8 — Revisar secrets, variáveis e gatilhos de bloqueio do GitHub Actions`

---

## Card Macro — Fase 13 — Infraestrutura como Código e Deploy em AWS

### Objetivo da fase
Provisionar um ambiente mínimo e reprodutível na AWS para hospedar a demonstração do projeto.

### Resultado esperado
Projeto preparado para rodar em infraestrutura provisionada por Terraform, com deploy controlado e evidência de execução fora do ambiente local.

### Critério de aceite
- infraestrutura mínima definida em Terraform
- ambiente AWS provisionado com sucesso
- aplicação executando em EC2 ou equivalente escolhido
- deploy reproduzível e documentado
- acesso controlado e validação do serviço em nuvem
- contratos de `request_id`, `tenant_id` e observabilidade mínima preservados no deploy
- validação remota de `/health`, `/metrics` e smoke mínimo do tenant demonstrativo

### Riscos
- complexidade excessiva de infraestrutura para o estágio do case
- custo desnecessário
- atrasar fechamento do projeto com decisões cloud exageradas
- criar ambiente nuvem sem refletir o runtime local validado
- perder contratos do método entre ambiente local e ambiente em nuvem

### Dependências
- fases 5, 11 e 12 concluídas ou estabilizadas
- escolha do recorte de deploy aprovada
- build Docker pronto para publicação

### Observações
O alvo recomendado é infraestrutura mínima, simples e explicável. O objetivo é demonstrar maturidade de entrega, não montar um zoológico de serviços AWS.

#### Tasks — Fase 13

- `CPP-F13-T1 — Definir arquitetura mínima de deploy na AWS`
- `CPP-F13-T2 — Estruturar projeto Terraform do ambiente`
- `CPP-F13-T3 — Provisionar rede e segurança mínimas`
- `CPP-F13-T4 — Provisionar instância de execução da aplicação`
- `CPP-F13-T5 — Preparar estratégia de deploy com Docker e secrets do LLM/Telegram`
- `CPP-F13-T6 — Executar primeiro deploy em ambiente AWS`
- `CPP-F13-T7 — Validar /health, /metrics e smoke mínimo do tenant demonstrativo em nuvem`
- `CPP-F13-T8 — Documentar operação mínima, envs e secrets do ambiente provisionado`

---

## Card Macro — Fase 14 — Alinhamento Final entre Arquitetura, Operação e Documentação

### Objetivo da fase
Garantir que código, documentação, pipeline, runtime local, demonstração funcional e deploy contem a mesma história técnica.

### Resultado esperado
Projeto coerente, retomável, explicável e pronto para apresentação profissional como case.

### Critério de aceite
- contexto.md, arquitetura.md e planejamento atualizados
- README ajustado ao estado real do sistema
- documentação principal coerente com CI, Docker, tenant demo e AWS
- decisões técnicas relevantes registradas
- narrativa do projeto alinhada ao que efetivamente funciona
- checklist final `claim -> evidência -> artefato` consolidado

### Riscos
- documentação prometer mais do que o projeto entrega
- divergência entre demo local e deploy em nuvem
- espalhar a verdade em arquivos demais

### Dependências
- fases 11, 12 e 13 estabilizadas

### Observações
Esta é a fase de acabamento técnico e narrativo. Ela não substitui validação; ela organiza o que já foi comprovado.
A promoção de `develop` para `main` deve ocorrer via Pull Request, usando a revisão final desta fase como evidência de coerência entre código, runtime e documentação.

#### Tasks — Fase 14

- `CPP-F14-T1 — Consolidar contexto operacional final do projeto`
- `CPP-F14-T2 — Atualizar arquitetura final do sistema`
- `CPP-F14-T3 — Revisar planejamento por fases concluídas`
- `CPP-F14-T4 — Revisar README com base no sistema real`
- `CPP-F14-T5 — Atualizar documentação crítica de operação`
- `CPP-F14-T6 — Validar coerência entre docs, runtime, CI e AWS`
- `CPP-F14-T7 — Consolidar checklist final de GenAI com método`

---

## Modelo de Descrição — Card de Task

```markdown
## Objetivo
[descrever a ação concreta da task]

## Arquivos / áreas afetadas
- [arquivo 1]
- [arquivo 2]

## Passo operacional
1. [passo 1]
2. [passo 2]
3. [passo 3]

## Validação
- [comando / evidência 1]
- [comando / evidência 2]

## Critério de conclusão
- [critério 1]
- [critério 2]

## Riscos
- [risco 1]
- [risco 2]

## Fechamento
- [ ] alteração realizada
- [ ] validação executada
- [ ] evidência registrada
- [ ] card movido corretamente
```

---

## Modelo de Comentário — Encerramento de Sessão

```markdown
Sessão encerrada.

Foi executado: [resumo curto].
Validação realizada: [resumo].
Status atual: [estado].
Próximo passo: [ação objetiva].
Branch atual: [nome da branch].
```
