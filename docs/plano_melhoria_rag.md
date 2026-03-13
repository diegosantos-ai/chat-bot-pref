# Plano de Melhoria - RAG e Tomada de Decisao

Objetivo: reduzir fallbacks/erros repetidos e melhorar a decisao de resposta.

Como usar: execute uma tarefa por vez, registre resultados e so depois avance.

---

## Tarefa 1 — Coleta de Falhas (Banco)
**Objetivo:** mapear os pontos que mais falham.

Checklist:
- [OK ] Rodar consultas de top fallback, low_confidence e NO_REPLY.
- [x] Exportar top 20 perguntas com fallback (se disponivel).
- [X] Registrar data/hora da coleta.

Consultas sugeridas:
```sql
select intencao, motivo_fallback, count(*)
from conversas
where tipo_resposta='FALLBACK'
group by 1,2
order by count(*) desc;

select canal, tipo_superficie, intencao, count(*)
from conversas
where tipo_resposta='NO_REPLY' and tipo_superficie='inbox'
group by 1,2,3;

select motivo_fallback, count(*)
from conversas
where motivo_fallback='low_confidence'
group by 1;
```

Entrega esperada:
- Lista dos top problemas (por intent e motivo).

---

## Tarefa 2 — Diagnostico por Categoria
**Objetivo:** classificar cada erro em causa raiz.

Checklist:
- [ X] Classificar falhas como: Intent errado / RAG sem docs / Policy bloqueou / Resposta ruim.
- [ X] Criar planilha (ou doc) com: pergunta → causa → acao.

Entrega esperada:
- Lista priorizada de ajustes por impacto.

---

## Tarefa 3 — Correcoes Rapidas (Prompts/Regras)
**Objetivo:** corrigir respostas erradas ou mal direcionadas.

Checklist:
- [x] Ajustar `prompts/v1/fallback.txt` e `prompts/v1/fallback_private.txt`.
- [x] Ajustar `prompts/v1/public_redirect.txt` (sem telefone em publico).
- [x] Ajustar regras de fallback no `app/orchestrator/service.py` por intent.

Entrega esperada:
- Novos textos padronizados, sem emojis, com disclaimer e contato correto.

---

## Tarefa 4 — Base RAG (Conteudo)
**Objetivo:** melhorar cobertura e precisao do RAG.

Checklist:
- [x] Revisar documentos faltantes (saude/PSF, tributos, horarios) - Criados docs de Emergência e Zeladoria.
- [x] Padronizar titulos e tags nos arquivos `base/BA-RAG-PILOTO-2026.01.v1/items` - Manifesto atualizado.
- [x] Reingestar base: `python -m app.rag.ingest base/BA-RAG-PILOTO-2026.01.v1`.

Entrega esperada:
- Mais respostas de sucesso e menos fallback por `no_docs_found` (Validado: reduziu de 33% para 26% no teste de regressão).

---

## Tarefa 5 — Refino do Classificador
**Objetivo:** reduzir intent incorreto.

Checklist:
- [x] Adicionar termos locais (ex: UBS, PSF, posto, 2a via, parcelamento) - Inseridos no prompt few-shot.
- [x] Ajustar padrões de intents comuns - Adicionada categoria `COMPLAINT` e exemplos de treinamento em `classifier.txt`.

Entrega esperada:
- Menos OUT_OF_SCOPE indevido e melhor detecção de reclamações (COMPLAINT).

---

## Tarefa 6 — Ajustes RAG (Score/Top-K)
**Objetivo:** reduzir respostas ruins por baixa relevancia.

Checklist:
- [x] Revisar `RAG_MIN_SCORE` e `RAG_TOP_K` - Ajustado para `TOP_K=7` e `MIN_SCORE=0.35` em `settings.py`.
- [x] Testar queries criticas com novos thresholds - Script `debug_rag_score.py` validou recuperação melhorada.

Entrega esperada:
- Menos low_confidence e melhor qualidade de resposta.

---

## Tarefa 7 — Testes de Regressao
**Objetivo:** garantir que melhorias nao quebram o que ja funciona.

Checklist:
- [x] Criar lista de perguntas reais que falharam - Dataset `artifacts/testes/Dataset de Teste Atendimento Cidadão.txt` padronizado.
- [x] Rodar teste manual ou automatizado antes de cada deploy - Executado `scripts/run_validation_test.py`.

Entrega esperada:
- Suite de testes minima validada.
- **Resultado Final (v0.5.0)**:
    - Fallback rate reduzido de 33% para 26%.
    - Cobertura de Zeladoria e Emergência melhorada significativamente.
    - Classificação de COMPLAINT corrigida.

---

## Registro de Resultados
Anote aqui o resumo depois de cada tarefa:
- Tarefa 1:
intencao       |motivo_fallback|count|
---------------+---------------+-----+
HUMAN_HANDOFF  |no_docs_found  |   36|
COMPLAINT      |no_docs_found  |   34|
SCHEDULE_QUERY |no_docs_found  |   28|
INFO_REQUEST   |no_docs_found  |   28|
CONTACT_REQUEST|no_docs_found  |   26|
SCHEDULE_QUERY |low_confidence |    6|
INFO_REQUEST   |low_confidence |    3|

motivo_fallback|count|
---------------+-----+
low_confidence |    9|

canal|tipo_superficie|intencao|total|
-----+---------------+--------+-----+
SEM RETORNO

id_usuario|mensagem_usuario                |mensagem_resposta                                                                  |motivo_fallback|
----------+--------------------------------+-----------------------------------------------------------------------------------+---------------+
         1|Como conseguir vaga no CMEI?    |Entre em contato com a Secretaria de Educação para orientações.                    |no_docs_found  |
         6|Qual o horario de atendimento?  |O atendimento é em horário comercial. Confira a secretaria desejada para detalhes. |no_docs_found  |
         1|Quero agendar consulta          |Para agendamento, entre em contato com a Secretaria de Saúde: (45) 3124-1020.      |no_docs_found  |
         4|Como conseguir vaga no CMEI?    |Entre em contato com a Secretaria de Educação para orientações.                    |no_docs_found  |
        17|Como falar com o CRAS?          |Contato do CRAS/Assistência Social: (45) 3124-1030.                                |no_docs_found  |
        21|Onde fica a Secretaria de Saúde?|A Secretaria de Saúde fica na Av. Brasília, 525.                                   |no_docs_found  |
        19|Como conseguir vaga no CMEI?    |Entre em contato com a Secretaria de Educação para orientações.                    |no_docs_found  |
        26|Onde fica a Secretaria de Saúde?|A Secretaria de Saúde fica na Av. Brasília, 525.                                   |no_docs_found  |
        32|Tem transporte escolar?         |A Secretaria de Educação orienta sobre transporte escolar. Contato: (45) 3124-1010.|no_docs_found  |
         6|Quero agendar consulta          |Para agendamento, entre em contato com a Secretaria de Saúde: (45) 3124-1020.      |no_docs_found  |
        44|Como falar com o CRAS?          |Contato do CRAS/Assistência Social: (45) 3124-1030.                                |no_docs_found  |
        20|Onde fica a Secretaria de Saúde?|A Secretaria de Saúde fica na Av. Brasília, 525.                                   |no_docs_found  |
        33|Como conseguir vaga no CMEI?    |Entre em contato com a Secretaria de Educação para orientações.                    |no_docs_found  |
        48|Quero parcelar minha divida     |Para parcelamento de dívida, procure o atendimento da Prefeitura.                  |no_docs_found  |
        43|Quero parcelar minha divida     |Para parcelamento de dívida, procure o atendimento da Prefeitura.                  |no_docs_found  |
        52|Tem transporte escolar?         |A Secretaria de Educação orienta sobre transporte escolar. Contato: (45) 3124-1010.|no_docs_found  |
        53|Qual o telefone da prefeitura?  |O telefone da Prefeitura é (45) 3124-1000. Endereço: Av. Paraná, 61.               |no_docs_found  |
        55|Como tirar segunda via do IPTU? |Você pode solicitar a segunda via do IPTU no atendimento da Prefeitura.            |no_docs_found  |
        13|Quero agendar consulta          |Para agendamento, entre em contato com a Secretaria de Saúde: (45) 3124-1020.      |no_docs_found  |
        57|Como conseguir vaga no CMEI?    |Entre em contato com a Secretaria de Educação para orientações.                    |no_docs_found  |

COLETA REALIZADA 22/01/2025 AS 11:44

- Tarefa 2:

artifacts\analises\analise_falhas_rag.csv
- Tarefa 3:
- Tarefa 4:
- Tarefa 5:
- Tarefa 6:
- Tarefa 7:
