# Diario de Bordo do Case

## Objetivo

Este documento registra eventos importantes da construcao do Chat Pref em linguagem mais direta do que os artefatos JSON e mais narrativa do que os documentos de arquitetura.

Ele serve para:

- contar a historia tecnica do projeto
- registrar testes e evidencias importantes
- apoiar apresentacao em entrevista, portfolio e analise de terceiros
- ligar cada claim do case a uma prova reproduzivel

## Como ler

Cada registro abaixo tenta responder quatro perguntas:

1. o que mudou
2. por que isso importou
3. como foi validado
4. onde esta a evidencia

## Linha do tempo

### 2026-03-14 - Fase 13 validada com deploy remoto em AWS

**Marco**

O Chat Pref passou a rodar fora da maquina local em um ambiente minimo na AWS, provisionado com Terraform e validado por smoke remoto.

**Por que isso importa**

Esse foi o ponto em que o case deixou de ser apenas uma demonstracao local e passou a provar entrega real: infraestrutura minima, deploy reproduzivel, ambiente acessivel por IP publico e validacao de comportamento institucional fora da maquina de desenvolvimento.

**Validacao principal**

- `terraform fmt`, `init`, `validate`, `plan` e `apply`
- stack minima com VPC, subnet publica, Security Group, role SSM, EC2 unica e Elastic IP
- redeploy remoto via SSM reaproveitando `scripts/deploy_aws_instance.sh`
- smoke remoto aprovado em `GET /`, `GET /health`, `GET /metrics` e `POST /api/chat`
- sessao manual via `aws ssm start-session` validando `health`, metricas e `POST /api/chat` dentro da propria EC2

**Aprendizados de engenharia**

Tres problemas reais apareceram no bootstrap remoto e foram corrigidos na propria fase:

- Amazon Linux 2023 nao expunha `docker-compose-plugin` no `dnf`, exigindo instalacao do Compose v2 por binario
- adicionar `curl` na lista de pacotes conflitou com `curl-minimal`
- a EC2 clonou a branch antes da publicacao do pacote da Fase 13 e o bootstrap ainda usava um `--phase-report` nao suportado

Esses ajustes sao parte da evidencia do case, porque mostram diagnostico de causa raiz, correcoes pequenas e rastreaveis e validacao de entrega remota de verdade.

**Leitura operacional da validacao manual**

Na validacao final via SSM, o runtime confirmou:

- `GET /health` retornando `healthy` dentro da instancia
- metricas `chatpref_*` disponiveis no endpoint local
- resposta institucional correta para a pergunta sobre horario da sala de vacinacao

Os erros observados nessa sessao nao foram falhas do deploy:

- `git safe.directory` apareceu por protecao de ownership do repositorio na EC2
- `docker.sock permission denied` apareceu porque os comandos foram executados sem `sudo`

Isso reforca um ponto importante do case: a aplicacao estava funcional; o que apareceu ali foi ergonomia de operacao da sessao administrativa.

**Evidencias**

- [fase_13_aws_deploy.md](docs/fase_13_aws_deploy.md)
- [fase13-remote-smoke.json](artifacts/fase13-remote-smoke.json)
- [main.tf](infra/terraform/aws/minimal/main.tf)
- [deploy_aws_instance.sh](scripts/deploy_aws_instance.sh)

### 2026-03-14 - Hotfix do build Docker no GitHub Actions

**Marco**

O primeiro run remoto da CI expôs uma divergencia entre o ambiente local e o checkout do GitHub Actions: o `Dockerfile` copiava `.env.example`, mas esse arquivo estava ignorado no Git e, por isso, nao existia no runner.

**Por que isso importa**

Esse tipo de falha e pequeno em codigo, mas importante como prova de maturidade. Ele mostra que o projeto nao ficou apenas "verde na maquina local": a pipeline remota encontrou uma diferenca real de empacotamento, a causa raiz foi identificada e o contrato do build foi corrigido.

**Validacao principal**

- erro reproduzido no job `docker build` do GitHub Actions
- causa raiz confirmada em `.gitignore`
- `docker build -t chat-pref-ci -f Dockerfile .` aprovado apos versionar `/.env.example`
- workflow remoto da branch voltou a passar

**Evidencias**

- [Dockerfile](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/Dockerfile)
- [.gitignore](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/.gitignore)
- [.env.example](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/.env.example)
- [ci.yml](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/.github/workflows/ci.yml)
- [fase_12_github_actions.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_12_github_actions.md)

### 2026-03-14 - Fase 12 implementada e validada localmente na branch

**Marco**

O projeto ganhou workflow de CI versionado com quality gates, build Docker, smoke reduzido e upload de artefato.

**Por que isso importa**

A partir daqui, o case nao depende apenas de validacao manual local. O repositorio passa a carregar regressao automatizada de comportamento, rastreabilidade e integridade do `audit.v1`.

**Validacao principal**

- `scripts/lint_runtime.py`
- `scripts/check_runtime_residues.py`
- `python -m compileall app scripts tests`
- `pytest` com `32 passed`
- `docker compose config`
- `docker build`
- smoke `prod` em `runtime-mode=reuse` com `15/15`

**Evidencias**

- [fase_12_github_actions.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_12_github_actions.md)
- [ci.yml](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/.github/workflows/ci.yml)
- [test_phase12.py](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/tests/test_phase12.py)

### 2026-03-14 - Fase 11 concluida na branch de trabalho

**Marco**

O projeto passou a expor observabilidade minima util de ponta a ponta:

- logs estruturados por `request_id`
- metricas em `GET /metrics`
- traces OpenTelemetry persistidos por request
- correlacao consistente entre auditoria, logs e traces

**Por que isso importa**

A partir daqui, o projeto deixa de apenas responder e passa a provar como respondeu. Isso fortalece o case para avaliacao tecnica, debugging, explicabilidade operacional e defesa em entrevista.

**Validacao principal**

- `pytest` com `29 passed`
- smoke `prod` da Fase 11 com `15/15`
- smoke `dev` da Fase 11 com `15/15`
- relatorio gerencial da fase com `6/6`

**Evidencias**

- [fase_11_observabilidade_aplicada.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_11_observabilidade_aplicada.md)
- [fase11-smoke-prod.json](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/artifacts/fase11-smoke-prod.json)
- [fase11-smoke-dev.json](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/artifacts/fase11-smoke-dev.json)

**Exemplo de leitura de evidencias**

No request manual `fase11-manual-01`, o projeto mostrou:

- `policy_pre=allow`
- `retrieval_status=knowledge_base_not_loaded`
- composicao em `mode=fallback`
- `policy_post=fallback`
- `reason_codes=["NO_KNOWLEDGE_BASE"]`

Isso prova que a trilha do pipeline consegue explicar nao apenas o resultado final, mas tambem o motivo tecnico e institucional do fallback.

### 2026-03-14 - Fase 10 estabilizada e entregue

**Marco**

Entrada da camada generativa minima do case, com adaptador LLM isolado, prompts versionados, `policy_pre`, `policy_post` e auditoria `audit.v1`.

**Por que isso importa**

Este foi o momento em que o projeto deixou de ser apenas retrieval-first e passou a demonstrar GenAI controlada, ainda em corte minimo.

**Validacao principal**

- `pytest` com `26 passed`
- smoke `prod` da Fase 10 com `14/14`
- smoke `dev` da Fase 10 com `14/14`

**Evidencias**

- [fase_10_composicao_generativa.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_10_composicao_generativa.md)
- [fase10-smoke-prod.json](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/artifacts/fase10-smoke-prod.json)
- [fase10-smoke-dev.json](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/artifacts/fase10-smoke-dev.json)

### 2026-03-14 - Fase 9 fechou o canal Telegram

**Marco**

O tenant demonstrativo passou a operar no Telegram reutilizando o mesmo fluxo principal do chat.

**Por que isso importa**

O projeto ganhou um canal demonstrativo real, aproximando o case de uma conversa externa e validando tenant-awareness fora do endpoint direto.

**Validacao principal**

- `pytest` com `21 passed`
- smoke `prod` e `dev` da Fase 9 aprovados
- webhook local do Telegram validado em `dry_run`

**Evidencias**

- [fase_9_telegram_demo.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_9_telegram_demo.md)
- [fase9-smoke-prod.json](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/artifacts/fase9-smoke-prod.json)
- [fase9-smoke-dev.json](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/artifacts/fase9-smoke-dev.json)

### 2026-03-14 - Fases 7 e 8 consolidaram o tenant demonstrativo

**Marco**

O projeto ganhou um tenant ficticio coerente, base documental propria, retrieval checks e ingest limpa.

**Por que isso importa**

Sem tenant e base documental controlados, a demonstracao de RAG e guardrails perderia explicabilidade e repetibilidade.

**Evidencias**

- [fase_7_tenant_demonstrativo.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_7_tenant_demonstrativo.md)
- [fase_8_base_documental_ficticia.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_8_base_documental_ficticia.md)
- [fase8-smoke-prod.json](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/artifacts/fase8-smoke-prod.json)

### 2026-03-14 - Fases 1 a 6 estabilizaram a base

**Marco**

As primeiras fases removeram acoplamentos legados, consolidaram o contrato multi-tenant, resetaram a base RAG e tornaram o ambiente local reproduzivel.

**Por que isso importa**

O projeto so pode defender GenAI com metodo porque antes fechou o basico: tenant explicito, runtime limpo, containerizacao previsivel e falha controlada sem base.

**Evidencias**

- [fase_6_validacao_estrutural.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_6_validacao_estrutural.md)
- [smoke-prod.json](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/artifacts/smoke-prod.json)
- [smoke-dev.json](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/artifacts/smoke-dev.json)

## Uso recomendado em entrevista

Para explicar o case com objetividade:

1. comece pelo problema: reconstruir uma base minima, tenant-aware e explicavel
2. mostre a virada da Fase 10: composicao generativa controlada
3. mostre a virada da Fase 11: observabilidade ponta a ponta
4. use um `request_id` real para provar como o pipeline decidiu
5. termine mostrando que o principal gap remanescente ja esta concentrado em CI e entrega

## Observacao final

Este documento nao substitui:

- `docs/contexto.md`
- `docs/arquitetura.md`
- `docs/planejamento_fases.md`
- `docs/fase_*.md`

Ele existe para transformar a historia tecnica do projeto em narrativa legivel e defensavel.
