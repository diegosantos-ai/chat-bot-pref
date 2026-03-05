---
name: Project Architect and Management
description: Habilidade de criar especificações, ler templates e gerenciar o estado da sessão via progresso.md.
---

# Project Architect Skill

## Mapeamento de Templates Essenciais
Sempre que você precisar fazer o scaffolding de um novo projeto, você **deve usar as estruturas dos templates** localizados em `d:\Projetos\Desenvolvendo\agent-farm\templates`. Observe a clareza, os critérios de aceite, e a componentização neles definidos. Use-os como referencial de arquitetura.

## Estrutura do `progresso.md` (Padrão Ouro)

Sempre valide se o projeto possui o arquivo `progresso.md` em sua raiz. Ele é o seu cérebro de longo prazo. O arquivo deve ter este formato e VOCÊ DEVE mantê-lo atualizado em cada final de sessão (handoff):

```markdown
# Estado do Projeto: [Nome do Projeto]

**Fase Atual:** [Planejamento / Infra / Backend / Frontend / QA]
**Último Marco Atingido:** [Descreva a última grande conquista, ex: "Módulo Autenticação concluído"]
**Próxima Tarefa P0 (Imediata):** [Descreva o próximo passo óbvio que o dev-agent deve fazer na próxima sessão]

## Entregáveis do Projeto
- [ ] requirements.md (Requisitos de negócio)
- [ ] design.md (Arquitetura, Banco, Componentes)
- [ ] task.md (O Backlog / Planilha de Tarefas)

## Histórico de Handoffs (Sessões)
- **[DD/MM/YYYY]:** Breve resumo do que foi feito hoje e eventuais pontas soltas para a próxima sessão.
```

## Como Conduzir a Passagem de Bastão (Handoff)
Você é o guardião final de cada sessão. Quando o desenvolvimento do dia chega ao fim:
1. Certifique-se de que os checkboxes no `task.md` refletem a realidade (peça ao agente dev para atualizar, ou atualize na próxima vez que for chamado).
2. Rode `python C:\Users\santo\.agent\scripts\session_brief.py handoff` e atualize o `progresso.md` conforme as instruções que ele cuspir.
3. Chame `python C:\Users\santo\.agent\scripts\validation_execution_gate.py` para conferir se as specs existem, impedindo buracos na arquitetura.
