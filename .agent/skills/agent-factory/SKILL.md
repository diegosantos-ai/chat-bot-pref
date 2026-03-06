---
name: Agent Factory
description: Conjunto de regras para o Agent Creator conduzir seu papel, interagir com a CLI e redigir descrições sólidas de agente.
---

# Agent Factory Skill

## Core Principles

- **Princípio 1:** Arquitetura do Antigravity Kit. Todo novo "cérebro" depende de uma casca em `.agent/agents/{name}.md` e dos conhecimentos práticos armazenados em ramificações `.agent/skills/{skill}/SKILL.md`. Essa arquitetura garante o reaproveitamento de skills. O Creator DEVE respeitá-la.
- **Princípio 2:** CLI FIRST. Não tente criar YAML com `write_to_file` quando for inaugurar a árvore inicial. Utilize a confiabilidade do Python para o esqueleto inicial e depois injete seu conhecimento.

## Regras de Execução

Quando você (o Agente Creator) estiver na fase execução:

1. **Defina Variáveis:** Tenha clareza de `--name`, `--desc` e `--skills` mentalmente.
2. **Execute a Ordem:** Rode: `python C:\Users\santo\.agent\scripts\scaffold_agent.py --name [name] --desc "[desc]" --skills [s1,s2]` (Não adicione espaços ao redor de vírgulas nas skills!).
3. **Leia o Log ou Path:** Preste atenção no sucesso da ferramenta de terminal, pois ela ditará os caminhos que você deve usar na etapa seguinte.
4. **Acabamento Obrigatório:** A criação física via terminal apenas coloca um header no arquivo da skill. Em seguida, utilize suas ferramentas nativas do sistema da IDE para rescrever o SKILL.md com regras reais sobre:
   - "Essa skill serve para..."
   - "Anti-patterns:"
   - "Regras de Ouro:"

## Anti-Patterns Evitados (O que NÃO fazer)

- Nunca faça bypass do `scaffold_agent.py` tentando usar ferramentas de escrita direta para iniciar o esqueleto nas raízes do projeto.
- Nunca faça uma lista de `--skills a, b` (com espaço). Use `--skills a,b`.
- Nunca assuma que você "terminou" a criação de um agente só porque você rodou o script Python. As skills recém-criadas estarão cheias do texto default `{SKILL_DESCRIPTION}` vindo dos templates até que você, Creator, entre nos arquivos gerados e redija os princípios reais lá dentro.
