# Tenant Demonstrativo - Prefeitura Municipal de Vila Serena

## Identidade

- `tenant_id`: `prefeitura-vila-serena`
- `client_name`: `Prefeitura Municipal de Vila Serena`
- `bot_name`: `Atende Vila Serena`
- municipio ficticio criado exclusivamente para demonstracao tecnica da plataforma

## Escopo do assistente

O `Atende Vila Serena` atua como assistente institucional estritamente informativo.

Ele pode orientar sobre:

- horarios de atendimento
- canais oficiais
- documentos basicos exigidos em servicos recorrentes
- orientacoes institucionais gerais

Ele nao pode:

- emitir documentos
- prometer decisao administrativa
- consultar dados pessoais
- substituir protocolo oficial
- prestar orientacao juridica individual

## Canais e configuracao

- chat web habilitado
- `webhook_page_id`: `page-demo-vila-serena`
- base documental versionada neste bundle e materializada no runtime por script explicito

## Estrutura documental

Este bundle inclui uma base documental enxuta e organizada em quatro grupos:

- institucional
- atendimento
- servicos municipais prioritarios
- FAQ e procedimentos informativos

Temas cobertos na base atual:

- identidade institucional e limites do assistente
- central de atendimento e canais oficiais
- protocolo geral e documentos basicos
- alvara de funcionamento
- IPTU e certidoes imobiliarias
- UBS e vacinacao
- matricula e transferencia escolar
- coleta seletiva e recolhimento de entulho
- FAQ de servicos digitais

As perguntas controladas de retrieval ficam em `knowledge_base/retrieval_checks.json` e servem como evidencia objetiva do comportamento esperado do RAG nas validacoes da fase.
