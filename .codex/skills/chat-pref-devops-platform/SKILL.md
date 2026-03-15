---
name: chat-pref-devops-platform
description: Usar no repositorio Chat Pref quando a tarefa tocar Dockerfile, `docker-compose*.yml`, scripts operacionais, GitHub Actions, Terraform, AWS, deploy minimo, smoke remoto ou setup de ambiente. Acionar tambem em ajustes de segredos, bootstrap reproduzivel ou limites entre runtime principal e camadas offline.
---

# Chat Pref Devops Platform

Manter ambiente local e remoto reproduziveis, com infraestrutura proporcional ao estagio real do projeto e sem prometer endurecimento que ainda nao foi validado.

## Ler antes de editar

- `AGENTS.md`
- `README.md`
- `docs-fundacao-operacional/contexto.md`
- `docs-fundacao-operacional/arquitetura.md`
- `docs-fundacao-operacional/planejamento_fases.md`
- `docs-fundacao-operacional/fase_13_aws_deploy.md` quando a task tocar AWS ou deploy remoto
- `docs-LLMOps/README.md`, `docs-LLMOps/ARQUITETURA-LLMOps.md` e `docs-LLMOps/PLANEJAMENTO-LLMOps.md` quando a task tocar setup de ambiente, tracking ou camadas offline
- `docs-LLMOps/runbooks/setup-ambiente.md` e `docs-LLMOps/runbooks/operacao-airflow.md` quando aplicavel
- `.github/agents/devops-platform.agent.md`
- `.ai/skills/deploy-aws-ec2.md`
- `.ai/skills/validate-runtime.md`
- `.ai/workflows/deploy-aws.md`
- `.ai/workflows/refatoracao-fase.md`

## Workflow

1. Identificar o alvo: ambiente local, CI, deploy remoto demonstrativo ou camada offline futura.
2. Confirmar a fase e o criterio de aceite antes de acrescentar ferramenta ou servico.
3. Separar provisionamento, configuracao e deploy da aplicacao.
4. Manter segredos fora do repositorio e documentar apenas exemplos seguros.
5. Validar com comandos reproduziveis, proporcionais ao impacto.
6. Declarar risco de ambiente quando a validacao depender de credenciais, cloud externa ou runtime remoto.

## Guardrails

- Evitar Compose inflado e infraestrutura excessiva para o case demonstrativo.
- Nao versionar credenciais reais nem manter segredos em areas ativas.
- Nao tratar Airflow, benchmark operacional ou secrets gerenciados como capacidade ativa sem validacao correspondente.
- Fazer CI validar o que ja e confiavel, sem teatro.

## Validacao sugerida

- `docker compose -f docker-compose.yml config`
- `docker build -t chat-pref-ci -f Dockerfile .`
- `python3 -m pytest tests -q` quando a mudanca tocar runtime executado na pipeline
- `terraform fmt`, `terraform validate` e `terraform plan` quando a task tocar `infra/terraform/`
- Smoke local ou remoto somente quando o escopo realmente tocar deploy ou runtime publicado
