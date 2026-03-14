# setup-ambiente

## Objetivo

Este documento descreve a preparação dos ambientes necessários para a fase de **LLMOps, avaliação formal, governança e observabilidade avançada** do Chat Pref.

Seu objetivo é padronizar a instalação das dependências e evitar deriva de ambiente entre desenvolvimento local, execução de benchmark, avaliação experimental e orquestração offline.

## Princípios

A preparação de ambiente desta fase segue os princípios abaixo:

- separar dependências do runtime principal das dependências de desenvolvimento e experimentação;
- isolar a camada de orquestração offline do ambiente principal do backend;
- garantir reprodutibilidade mínima do setup;
- evitar instalação ad hoc de bibliotecas fora das fases previstas no planejamento;
- manter coerência entre planejamento, arquitetura e execução.

## Ambientes previstos

A fase trabalha com três contextos principais de instalação:

### 1. Ambiente base do backend
Responsável por sustentar o runtime principal da aplicação.

Este ambiente cobre:
- API FastAPI;
- integração com RAG;
- auditoria operacional;
- observabilidade básica;
- execução do pipeline transacional.

Arquivo de referência:
- `requirements.txt`

### 2. Ambiente de desenvolvimento e experimentação
Responsável por sustentar:
- testes;
- tracking experimental;
- benchmark;
- avaliação formal de RAG;
- análise comparativa de versões;
- suporte a tarefas de validação da fase LLMOps.

Arquivo de referência:
- `requirements-dev.txt`

### 3. Ambiente de orquestração offline
Responsável por sustentar:
- Airflow;
- jobs de ingestão;
- reindexação;
- benchmark recorrente;
- avaliação offline;
- rotinas ligadas à deriva semântica.

Arquivo de referência:
- `requirements-airflow.txt`

## Arquivos de dependência

### `requirements.txt`
Contém as dependências do runtime principal.

Uso esperado:
- instalação inicial do backend;
- execução local da aplicação;
- base para desenvolvimento operacional.

### `requirements-dev.txt`
Contém as dependências adicionais de desenvolvimento, avaliação e experimentação.

Uso esperado:
- fases de LLMOps;
- execução de benchmark;
- testes assíncronos;
- tracking experimental;
- avaliação formal do pipeline.

### `requirements-airflow.txt`
Contém as dependências específicas do ambiente de orquestração offline.

Uso esperado:
- preparação da Fase 8;
- execução de jobs desacoplados do runtime principal.

## Regra de instalação por fase

A instalação das dependências deve obedecer ao planejamento formal da fase.

### Instalações permitidas
- **Fase 1:** instalar `requirements.txt` e `requirements-dev.txt`
- **Fase 8:** instalar `requirements-airflow.txt`

### Instalações fora dessas fases
Qualquer nova dependência identificada fora dessas fases deve ser tratada como:
- ajuste formal do planejamento, ou
- exceção técnica documentada em card próprio.

## Sequência recomendada de instalação

### Passo 1 — Preparar o ambiente base
Instalar o runtime principal da aplicação.

```bash
pip install -r requirements.txt
````

### Passo 2 — Preparar o ambiente de desenvolvimento

Instalar a camada de testes, avaliação e experimentação.

```bash
pip install -r requirements-dev.txt
```

### Passo 3 — Preparar o ambiente de orquestração offline

Executar apenas quando a Fase 8 for iniciada, preferencialmente em ambiente separado.

```bash
pip install -r requirements-airflow.txt
```

## Estratégia recomendada de isolamento

### Backend principal

Deve operar em ambiente dedicado ao runtime do projeto.

### Desenvolvimento / experimentação

Pode reutilizar o ambiente base, desde que a instalação do `requirements-dev.txt` seja controlada e registrada.

### Airflow

Deve operar em ambiente separado do backend principal.

Motivos:

* evitar poluição do runtime transacional;
* reduzir risco de conflito de dependência;
* manter separação clara entre request path e jobs offline;
* facilitar manutenção e troubleshooting.

## Validação mínima após instalação

Após a instalação do ambiente, devem ser validados ao menos os seguintes pontos:

### Ambiente base

* imports principais do backend funcionando;
* aplicação sobe sem erro de dependência;
* integração mínima com configuração e RAG disponível.

### Ambiente dev

* imports de MLflow funcionando;
* imports das bibliotecas de avaliação funcionando;
* suíte mínima de testes executável;
* bibliotecas analíticas disponíveis.

### Ambiente Airflow

* import principal do Airflow funcionando;
* ambiente isolado configurado;
* dependências auxiliares mínimas disponíveis.

## Evidência esperada

Toda instalação relevante desta fase deve gerar evidência mínima de execução, preferencialmente registrada em:

* card da fase correspondente;
* log de sessão;
* comentário de encerramento;
* documentação de apoio, quando aplicável.

## Riscos conhecidos

* instalar dependências no momento errado do plano;
* misturar ambiente de Airflow com ambiente do backend principal;
* adicionar bibliotecas sem revisão arquitetural;
* dificultar reprodutibilidade por falta de registro do setup;
* mascarar falhas de planejamento com instalação improvisada.

## Relação com a documentação da fase

Este runbook deve ser lido em conjunto com:

* `README.md`
* `CONTEXTO-LLMOps.md`
* `ARQUITETURA-LLMOps.md`
* `PLANEJAMENTO_LLMOps.md`

## Status

Runbook inicial de preparação de ambiente definido.

Próximo passo:

* consolidar os arquivos `requirements.txt`, `requirements-dev.txt` e `requirements-airflow.txt`;
* executar a instalação prevista na Fase 1.

```
```
