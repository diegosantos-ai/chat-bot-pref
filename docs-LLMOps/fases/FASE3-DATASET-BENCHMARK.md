# Fase 3 — Dataset de Benchmark Reproduzivel

## Objetivo deste documento

Registrar o estado atual do dataset de benchmark da Fase 3 apos os Blocos 1 a 6.

Este documento descreve apenas o que foi efetivamente implementado ate aqui:

- estrutura local do dataset no repositorio;
- contrato minimo de casos de avaliacao;
- organizacao por tenant e por cenario;
- priorizacao metodologica inicial dos cenarios do tenant demonstrativo;
- diferenciacao entre cenario aderente ao tenant, cenario generico municipal e placeholder controlado;
- validacoes locais simples da estrutura e da classificacao metodologica.

Ele nao declara benchmark automatico, scoring formal ou execucao recorrente como capacidades ja ativas.

## Enquadramento da fase

- ciclo: LLMOps, avaliacao e governanca
- fase ativa: Fase 3 — Dataset de Avaliacao e Benchmark Reproduzivel
- branch de execucao: `feat/dataset-avaliacao`
- task principal desta entrega: `CPPX-F3-T6`
- tasks ja cobertas na base atual: `CPPX-F3-T1`, `CPPX-F3-T2`, `CPPX-F3-T3`, `CPPX-F3-T4` e `CPPX-F3-T5`
- apoio parcial nesta entrega: `CPPX-F3-T7`

## Estrutura adotada

O dataset inicial foi separado do runtime transacional e do tracking experimental em uma pasta propria:

```text
benchmark_datasets/
├── README.md
└── tenants/
    └── prefeitura-vila-serena/
        └── benchmark_v1/
            ├── dataset_manifest.json
            └── scenarios/
                ├── atendimento_normal.jsonl
                ├── pergunta_ambigua.jsonl
                ├── fora_de_escopo.jsonl
                ├── baixa_confianca.jsonl
                └── risco_policy.jsonl
```

Regra estrutural desta etapa:

- `benchmark_datasets/` guarda apenas artefatos offline de benchmark;
- `tenant_id` aparece no caminho e no contrato de cada caso;
- `dataset_version` aparece no caminho do dataset e no manifest;
- cada arquivo JSONL agrupa apenas um tipo de cenario.

## Contrato minimo do manifest

Cada dataset local desta fase possui um `dataset_manifest.json` com os campos:

- `dataset_version`
- `tenant_id`
- `description`
- `selection_hypotheses`
- `scenario_files`
- `notes`

Cada item de `scenario_files` declara:

- `scenario_type`
- `relative_path`
- `cases_count`
- `priority_tier`
- `coverage_type`
- `selection_rationale`

Esse manifest permite que as proximas tasks da Fase 3 executem o benchmark de forma repetivel sem depender de banco ou servico externo.

## Contrato minimo de cada caso

Cada linha JSONL representa um caso de avaliacao com o seguinte contrato minimo:

- `case_id`
- `tenant_id`
- `scenario_type`
- `priority_tier`
- `coverage_type`
- `input_query`
- `expected_behavior`
- `expected_answer_reference`
- `expected_context_reference`
- `notes`

### Estrutura de `expected_answer_reference`

- `reference_type`
- `summary`
- `must_include`
- `must_not_include`

Interpretacao operacional:

- `summary` descreve o comportamento minimo esperado, nao um gabarito textual literal;
- `must_include` registra os sinais obrigatorios que precisam aparecer de forma recognoscivel na resposta;
- `must_not_include` registra os sinais proibidos que invalidam a comparabilidade minima do caso;
- qualquer formulacao fora desses campos permanece livre, desde que respeite o comportamento esperado.

### Estrutura de `expected_context_reference`

- `reference_type`
- `document_hints`
- `required_terms`
- `notes`

Interpretacao operacional:

- `document_hints` indica onde o grounding esperado deve estar ancorado, mesmo quando ele for leve ou indireto;
- `required_terms` registra os termos minimos de grounding esperados para cenarios com contexto suficiente;
- `notes` explica a nuance do caso, inclusive quando o benchmark aceita grounding limitado ou comparativo;
- em cenarios de desambiguacao, `required_terms` pode ficar vazio, desde que haja mais de um `document_hint` concorrente.

## Padrao minimo adotado neste bloco

Para fechar o Bloco 6, a referencia minima foi padronizada de forma scenario-aware:

- `atendimento_normal`: `reference_type` de resposta `resposta_informativa_minima` e contexto `grounding_documental_forte`;
- `pergunta_ambigua`: `reference_type` de resposta `resposta_de_desambiguacao_minima` e contexto `grounding_de_desambiguacao`;
- `fora_de_escopo`: `reference_type` de resposta `recusa_fora_de_escopo_minima` e contexto `grounding_em_limite_institucional`;
- `baixa_confianca`: `reference_type` de resposta `resposta_de_baixa_confianca_controlada` e contexto `grounding_limitado_com_lacuna_controlada`;
- `risco_policy`: `reference_type` de resposta `bloqueio_por_policy_minimo` e contexto `grounding_em_policy_e_limite`.

Essa padronizacao nao cria resposta unica. Ela apenas torna comparavel:

- qual comportamento o benchmark exige;
- quais sinais obrigatorios precisam aparecer;
- quais sinais proibidos invalidam a saida;
- que tipo de grounding minimo deve existir em cada familia de cenario.

## Cenarios cobertos na base atual

O dataset atual cobre os cinco cenarios exigidos no planejamento:

- `atendimento_normal`
- `pergunta_ambigua`
- `fora_de_escopo`
- `baixa_confianca`
- `risco_policy`

Nesta etapa, a cobertura continua pequena de proposito. O objetivo segue sendo estruturar o metodo com casos diagnosticos fortes, nao preencher o benchmark com volume artificial.

## Priorizacao inicial adotada

Os cenarios foram priorizados com tres faixas simples:

- `p1`: cenarios centrais para o tenant demonstrativo, frequentes ou sensiveis a regressao funcional;
- `p2`: cenarios importantes para ambiguidade, limites de escopo ou comparacao complementar;
- `p3`: placeholders honestos para lacunas ainda nao cobertas pelo tenant demonstrativo.

Tambem foi adotada uma diferenciacao explicita de aderencia:

- `tenant_demonstrativo`: caso sustentado diretamente por bundle, retrieval checks ou limite institucional ja documentado do tenant demonstrativo;
- `generico_municipal`: caso plausivel no dominio municipal, util para benchmark, mas nao validado por um servico especifico do tenant;
- `placeholder`: caso mantido para explicitar lacuna real e guiar refinamento posterior.

### Matriz inicial de priorizacao

| Cenário | Prioridade | Aderência | Racional curto |
|---|---|---|---|
| `atendimento_normal` | `p1` | `tenant_demonstrativo` | cobre perguntas centrais e frequentes do bundle atual, sensiveis a regressao de retrieval |
| `risco_policy` | `p1` | `tenant_demonstrativo` | protege um comportamento critico de guardrail e privacidade |
| `pergunta_ambigua` | `p2` | `tenant_demonstrativo` | testa desambiguacao dentro do dominio ja coberto pelo tenant |
| `fora_de_escopo` | `p2` | `generico_municipal` | mede limite de escopo com exemplo plausivel no contexto municipal |
| `baixa_confianca` | `p3` | `placeholder` | explicita uma lacuna atual do tenant sem inventar cobertura documental |

### Casos P1 atualmente materializados

Os casos P1 escolhidos para o tenant demonstrativo foram:

- horario da Central de Atendimento;
- documentos basicos para protocolo geral presencial;
- segunda via do IPTU;
- solicitacao de alvara para comercio de baixo risco;
- horario da sala de vacinacao da UBS;
- solicitacao de coleta de entulho;
- bloqueio de pedido de CPF de servidor;
- bloqueio de pedido para liberar alvara sem analise administrativa;
- bloqueio de orientacao para protocolar sem comprovante de endereco;
- bloqueio de pedido de telefone pessoal de fiscal da prefeitura.

Eles foram priorizados porque combinam:

- alta aderencia ao escopo institucional conhecido do tenant;
- frequencia plausivel no atendimento municipal;
- dependencia clara de contexto recuperado ou de guardrail;
- utilidade alta para detectar regressao funcional.

### Cobertura atual de `atendimento_normal`

Depois desta ampliacao, `atendimento_normal` passou a cobrir, de forma mais representativa:

- informacao institucional de horario e canal principal;
- documentos necessarios para atendimento presencial;
- emissao ou segunda via de servico recorrente;
- etapa inicial de procedimento administrativo;
- horario e local de servico municipal especifico;
- solicitacao de servico com regra operacional objetiva.

Casos propositalmente evitados neste bloco:

- `Cadastro Unico`, `nota fiscal avulsa` e `iluminacao publica`, porque ampliariam o volume com padroes ja parcialmente cobertos por documentos, procedimento ou solicitacao de servico;
- variacoes muito proximas das perguntas ja escolhidas, para nao transformar diversidade aparente em redundancia de benchmark.

## Tenant demonstrativo usado

O primeiro dataset foi criado para:

- `tenant_id`: `prefeitura-vila-serena`

Justificativa:

- o tenant demonstrativo ja possui bundle institucional documentado;
- existem retrieval checks controladas no repositorio;
- o conjunto permite exemplos plausiveis sem usar dado sensivel ou caso real.

Mesmo assim, o dataset ainda preserva um caso explicitamente `placeholder` em `baixa_confianca` e um caso `generico_municipal` em `fora_de_escopo`, justamente para nao transformar suposicao em verdade institucional.

## Diferenca metodologica entre `risco_policy`, `fora_de_escopo`, `baixa_confianca` e `pergunta_ambigua`

Nesta fase, esses cenarios nao devem ser tratados como equivalentes:

- `risco_policy`: a pergunta pede dado pessoal, bypass, excecao indevida ou orientacao para burlar fluxo oficial, entao a resposta correta e bloquear e redirecionar;
- `fora_de_escopo`: a pergunta pede algo que o assistente nao faz por papel institucional, mesmo sem componente de risco ou burla;
- `baixa_confianca`: a pergunta continua dentro ou muito proxima do dominio municipal, mas o contexto documental atual do tenant nao sustenta uma resposta segura;
- `pergunta_ambigua`: a pergunta ainda pode ser atendida, mas exige desambiguacao antes de responder.

Em outras palavras:

- `risco_policy` testa limite de seguranca e integridade do fluxo;
- `fora_de_escopo` testa limite de papel;
- `baixa_confianca` testa limite de evidencia;
- `pergunta_ambigua` testa necessidade de esclarecimento, nao de bloqueio.

### Como interpretar a referencia por tipo de cenario

- `atendimento_normal`: espera grounding forte em documento de servico e resposta informativa com fatos minimos verificaveis.
- `pergunta_ambigua`: espera pedido de esclarecimento antes da orientacao; o benchmark compara a desambiguacao, nao uma resposta final de servico.
- `fora_de_escopo`: espera recusa por papel institucional, com grounding suficiente em limite operacional e redirecionamento.
- `baixa_confianca`: espera reconhecimento explicito de lacuna ou insuficiencia documental, sem inventar dado operacional.
- `risco_policy`: espera bloqueio claro, tom seguro e redirecionamento institucional, mesmo quando houver documento de servico relacionado.

### Casos atuais de `fora_de_escopo`

Os casos de `fora_de_escopo` passaram a cobrir:

- emissao de documento que nao pertence ao papel do assistente;
- agendamento transacional de consulta;
- consulta de processo pessoal por CPF.

Esses casos ajudam a detectar regressao quando o sistema tenta responder como se pudesse executar acao, consultar dado individual ou operar fora do papel institucional declarado.

### Casos atuais de `baixa_confianca`

Os casos de `baixa_confianca` passaram a cobrir:

- taxa exata de licenciamento ambiental especial sem base documental;
- valor atualizado de taxa de alvara, quando o tenant so documenta procedimento;
- disponibilidade diaria de vacina, quando a base documenta servico e horario, mas nao estoque do dia.

Esses casos ajudam a detectar regressao quando o sistema deixa de sinalizar incerteza e passa a inventar valor, prazo ou disponibilidade operacional sem suporte do RAG.

### Casos atuais de `risco_policy`

Os casos de `risco_policy` passaram a cobrir:

- pedido de CPF de servidor;
- tentativa de liberar alvara sem aguardar analise administrativa;
- tentativa de protocolar sem comprovante de endereco;
- pedido de telefone pessoal de fiscal para resolver demanda por fora do fluxo oficial.

Esses casos ajudam a detectar regressao quando o sistema:

- expõe dado pessoal ou contato privado;
- orienta atalho administrativo indevido;
- ensina a burlar exigencia documental;
- troca redirecionamento institucional por promessa, conivencia ou instrucao indevida.

## Relacao com o runtime e com o tracking

Esta entrega:

- nao altera comportamento funcional do chat;
- nao muda o runtime RAG transacional;
- nao mistura benchmark com auditoria operacional;
- nao executa avaliacao automatica sofisticada;
- nao integra ainda o dataset a um runner formal da Fase 3.

O contrato foi colocado em `app/llmops/benchmark_dataset.py` apenas para carga e validacao local do dataset offline.

## O que fica preparado para os proximos blocos

Com esta estrutura, os proximos blocos podem:

- ampliar casos por tenant e por cenario;
- reutilizar o padrao refinado de `expected_answer_reference` e `expected_context_reference` no runner inicial;
- substituir placeholders por casos aderentes ao tenant quando a base documental for aprofundada;
- conectar `dataset_version` ao tracking experimental local;
- criar o runner repetivel do benchmark;
- consolidar baseline inicial da Fase 3.

## O que ainda nao foi implementado

Neste bloco ainda nao existe:

- benchmark runner recorrente;
- scoring automatico de qualidade;
- comparacao formal entre runs de benchmark;
- integracao do dataset com MLflow;
- cobertura ampla de casos por tenant.

## Leitura metodologica do estado atual

No estado atual:

- `tenant_demonstrativo` significa aderencia suficiente ao bundle e aos retrieval checks ja versionados;
- `generico_municipal` significa utilidade metodologica sem declaracao de servico especifico do tenant;
- `placeholder` significa falta de cobertura assumida explicitamente, nao defeito escondido.

Isso permite usar o benchmark repetidamente desde agora, sem perder a distinção entre evidencia real do tenant e extrapolacao ainda nao consolidada.

## Validacoes locais recomendadas

```bash
source .venv/bin/activate
pytest tests/test_phase3_benchmark_dataset.py -q
pytest tests -q
```

## Referencias internas

- `docs-LLMOps/PLANEJAMENTO-LLMOps.md`
- `docs-LLMOps/runbooks/avaliacao-rag.md`
- `docs-LLMOps/adrs/ADR-004-versionamento-de-prompts-policies-e-configuracoes.md`
- `docs-LLMOps/adrs/ADR-005-benchmark-por-tenant-como-contrato-de-avaliacao.md`
