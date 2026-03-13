---
name: devops-platform
description: Use quando a tarefa tocar Docker, Compose, GitHub Actions, deploy, Terraform, AWS ou scripts operacionais.
---

# DevOps Platform

## Foco
- Manter ambiente local reproduzivel e pipeline tecnica proporcional ao estagio do projeto.
- Trabalhar em `docker-compose*.yml`, `Dockerfile*`, `.github/workflows/`, `scripts/` e futura estrutura Terraform.

## Regras
- Evite infraestrutura excessiva para o case demonstrativo.
- CI deve validar o que ja e confiavel, sem teatro.
- Qualquer segredo deve sair de areas ativas e virar exemplo seguro ou orientacao operacional.

## Entrega esperada
- Mudanca operacional explicavel.
- Comando de validacao reproduzivel.
- Risco de ambiente explicitado quando existir.
