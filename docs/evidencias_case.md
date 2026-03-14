# Evidencias do Case

## Objetivo

Este documento traduz o projeto em uma matriz simples de `claim -> evidencia -> artefato`, com foco em leitura rapida por terceiros.

## Matriz de evidencias

| Claim | Evidencia objetiva | Artefato principal |
| --- | --- | --- |
| O backend sobe de forma reproduzivel | smoke `prod` e `dev` aprovados; Docker validado | [bootstrap_local.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/bootstrap_local.md) |
| O fluxo e tenant-aware | `tenant_id` obrigatorio; segregacao por tenant em chat, auditoria e RAG | [arquitetura.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/arquitetura.md) |
| O tenant demonstrativo e controlado | tenant ficticio versionado e base documental propria | [fase_7_tenant_demonstrativo.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_7_tenant_demonstrativo.md) |
| O RAG e controlado por tenant | ingest, query, reset e retrieval checks validados | [fase_8_base_documental_ficticia.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_8_base_documental_ficticia.md) |
| O Telegram reutiliza o mesmo fluxo principal | webhook demonstrativo e smoke do canal aprovados | [fase_9_telegram_demo.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_9_telegram_demo.md) |
| O projeto demonstra GenAI controlada | adaptador LLM isolado, prompts versionados, `policy_pre` e `policy_post` | [fase_10_composicao_generativa.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_10_composicao_generativa.md) |
| O pipeline e rastreavel | `request_id` compartilhado por auditoria, logs e traces | [fase_11_observabilidade_aplicada.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_11_observabilidade_aplicada.md) |
| O projeto bloqueia regressao relevante em pipeline | workflow de CI versionado com quality gates, build Docker, smoke reduzido e artefato JSON | [fase_12_github_actions.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_12_github_actions.md) |
| O projeto ja tem evidencias executaveis | `pytest`, smoke por fase e artefatos JSON versionados | [diario_bordo.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/diario_bordo.md) |

## Exemplo curto de prova tecnica

Claim:

- o pipeline explica por que respondeu com fallback

Evidencia:

- no request `fase11-manual-01`, `policy_pre=allow`, `retrieval_status=knowledge_base_not_loaded`, `compose.mode=fallback`, `policy_post=fallback`, `reason_codes=["NO_KNOWLEDGE_BASE"]`

Artefatos:

- log JSONL por `request_id`
- trace JSONL por `request_id`
- resposta HTTP com `X-Request-ID`

## Como apresentar para terceiros

Leitura curta recomendada:

1. [README.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/README.md)
2. [contexto.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/contexto.md)
3. [arquitetura.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/arquitetura.md)
4. [diario_bordo.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/diario_bordo.md)
5. [fase_11_observabilidade_aplicada.md](/media/diegosantos/TOSHIBA%20EXT/Projetos/Desenvolvendo/chat-bot-pref/docs/fase_11_observabilidade_aplicada.md)

Leitura de prova:

1. um artefato de smoke da fase
2. um request real com `request_id`
3. log JSONL
4. trace JSONL

## Limite deste documento

Este documento nao vende maturidade inexistente. Ele resume evidencias da base atual e deve ser revisado sempre que um novo claim passar a existir ou deixar de existir.
