# Planejamento por Fases

## Fase 1 — Diagnóstico e Inventário do Legado

### Objetivo
Mapear resíduos mono-tenant, hardcodes, defaults antigos, acoplamentos invisíveis e inconsistências entre código, documentação e operação.

### Resultado Esperado
Inventário confiável do que precisa ser removido, substituído ou reestruturado antes da evolução arquitetural.

### Critérios de Aceite
- Termos legados identificados
- Áreas críticas mapeadas
- Arquivos de maior risco listados
- Próximos cortes definidos com prioridade

### Riscos
- Análise superficial
- Deixar resíduo oculto em scripts auxiliares
- Ignorar acoplamentos operacionais

### Dependências
- Acesso ao repositório completo
- Leitura inicial da estrutura e dos arquivos críticos

### Observações
Não executar limpeza ampla nesta fase sem antes concluir o inventário.

### Tasks
- **CPP-F1-T1** — Inventariar resíduos mono-tenant
- **CPP-F1-T2** — Localizar hardcodes de path e domínio
- **CPP-F1-T3** — Mapear defaults legados de base e collection
- **CPP-F1-T4** — Identificar scripts críticos de operação e deploy
- **CPP-F1-T5** — Registrar arquivos sensíveis e pontos de risco
- **CPP-F1-T6** — Consolidar inventário técnico da refatoração

---

## Fase 2 — Sanitização Funcional do Runtime

### Objetivo
Remover hardcodes, defaults históricos e dependências operacionais legadas que impactam execução real.

### Resultado Esperado
Backend, painel e scripts principais operando sem dependência estrutural do projeto original.

### Critérios de Aceite
- Ausência de paths, domínios e bases antigas em componentes críticos
- Aplicação sobe sem acoplamento legível ao legado
- Painel/admin não depende de base fixa antiga
- Scripts operacionais não apontam para paths históricos

### Riscos
- Quebrar startup
- Remover referência sem substituir por configuração válida
- Limpar apenas a superfície e manter dependência invisível

### Dependências
- Fase 1 concluída
- Padrão de configuração alvo definido

### Observações
Priorizar backend, painel e scripts de runtime. Documentação ampla não entra como foco desta fase.

### Tasks
- **CPP-F2-T1** — Remover hardcodes de runtime no backend
- **CPP-F2-T2** — Remover defaults legados do painel admin
- **CPP-F2-T3** — Sanitizar scripts operacionais e systemd
- **CPP-F2-T4** — Revisar compose e serviços auxiliares
- **CPP-F2-T5** — Neutralizar domínios e contatos legados
- **CPP-F2-T6** — Validar startup sem dependência histórica

---

## Fase 3 — Consolidação do Contrato Multi-Tenant

### Objetivo
Tornar `tenant_id` um contrato explícito e consistente nos fluxos principais.

### Resultado Esperado
Resolução, propagação e uso de tenant coerentes entre chat, webhook, RAG, auditoria e persistência.

### Critérios de Aceite
- Fluxo de tenant definido documentalmente
- Endpoint de chat com estratégia clara de resolução de tenant
- Webhook sem associação frágil de tenant
- Retrieval e auditoria operando com tenant consistente

### Riscos
- Tenant implícito ou default silencioso
- Divergência entre webhook e chat
- Isolamento incompleto entre camadas

### Dependências
- Fase 2 concluída
- Definição do mecanismo de entrada de tenant no chat

### Observações
Nenhum fluxo crítico deve depender de tenant herdado “por sorte” ou base default.

### Tasks
- **CPP-F3-T1** — Definir contrato de entrada de tenant_id
- **CPP-F3-T2** — Tornar tenant_id explícito no endpoint de chat
- **CPP-F3-T3** — Corrigir resolução de tenant no webhook
- **CPP-F3-T4** — Revisar tenant_context e propagação assíncrona
- **CPP-F3-T5** — Validar retrieval por tenant no ChromaDB
- **CPP-F3-T6** — Validar auditoria com contexto de tenant
- **CPP-F3-T7** — Revisar falhas silenciosas de tenant default

---

## Fase 4 — Reset da Base RAG e Reingestão Limpa

### Objetivo
Eliminar herança semântica antiga e preparar o projeto para nova ingestão neutra e controlada.

### Resultado Esperado
Estrutura RAG limpa, sem base legada fixa, pronta para ingest por tenant.

### Critérios de Aceite
- Collections antigas removidas ou desacopladas
- Ingest sem base hardcoded
- Admin/painel operando com nova lógica
- Retrieval falha de forma controlada quando não houver base

### Riscos
- Apagar base sem preservar estrutura mínima
- Quebrar fluxo de teste
- Manter referências antigas em scripts de ingest

### Dependências
- Fase 2 concluída
- Contrato multi-tenant minimamente estabelecido

### Observações
A falha sem base carregada deve ser controlada, explícita e rastreável.

### Tasks
- **CPP-F4-T1** — Resetar bases RAG legadas
- **CPP-F4-T2** — Remover base hardcoded do fluxo de ingest
- **CPP-F4-T3** — Revisar scripts de coleção e contagem
- **CPP-F4-T4** — Ajustar painel admin para ingest tenant-aware
- **CPP-F4-T5** — Validar comportamento sem base carregada
- **CPP-F4-T6** — Preparar estrutura mínima para nova ingestão

---

## Fase 5 — Alinhamento entre Arquitetura, Operação e Documentação

### Objetivo
Garantir que código, documentação, scripts, compose e operação contem a mesma história técnica.

### Resultado Esperado
Projeto coerente, retomável e explicável, sem divergência entre documentação e comportamento real.

### Critérios de Aceite
- `contexto.md`, `arquitetura.md` e planejamento atualizados
- README ajustado ao estado real
- Documentos principais revisados
- Fluxo operacional documentado de forma honesta

### Riscos
- Documentação prometer o que o código não faz
- Esquecer scripts auxiliares
- Espalhar verdade em arquivos demais

### Dependências
- Fases 2, 3 e 4 suficientemente estabilizadas

### Observações
Nenhum documento deve descrever comportamento não validado.

### Tasks
- **CPP-F5-T1** — Consolidar contexto operacional do projeto
- **CPP-F5-T2** — Atualizar arquitetura do sistema
- **CPP-F5-T3** — Estruturar planejamento por fases
- **CPP-F5-T4** — Revisar README com base no runtime real
- **CPP-F5-T5** — Atualizar documentação crítica de operação
- **CPP-F5-T6** — Validar coerência entre docs, runtime e operação

---

## Fase 6 — Validação Estrutural e Fechamento do Ciclo

### Objetivo
Executar validações finais da refatoração e fechar o ciclo com evidência.

### Resultado Esperado
Projeto em estado tecnicamente demonstrável, com runtime validado, legado saneado e arquitetura defendível.

### Critérios de Aceite
- Buscas por termos proibidos sem resultado relevante
- Aplicação sobe
- Endpoints principais respondem
- Fluxo principal não depende de legado
- Quadro atualizado com status real

### Riscos
- Confiar em validação parcial
- Ignorar regressões
- Encerrar o ciclo sem evidência suficiente

### Dependências
- Fases anteriores concluídas ou estabilizadas

### Observações
Nenhum encerramento deve ocorrer sem validação mínima dos fluxos críticos.

### Tasks
- **CPP-F6-T1** — Executar varredura final de resíduos históricos
- **CPP-F6-T2** — Validar startup do backend após refatoração
- **CPP-F6-T3** — Validar endpoints principais
- **CPP-F6-T4** — Validar integração mínima de tenant no fluxo
- **CPP-F6-T5** — Revisar diff final e riscos residuais
- **CPP-F6-T6** — Consolidar evidências e encerrar ciclo
