# Requirements Specifications: Nexo Basis White-Label SaaS

## 1. Visão Geral (Overview)
Reestruturação da aplicação atual de Chatbot Cidadão para um motor de *SaaS White-Label Multi-Tenant*, construído sob princípios inegociáveis de segregação governamental de dados, compliance (LGPD) e automação de configuração simples, voltado como ferramenta passível de "dispensa de licitação".

## 2. Requisitos de Negócios (Business Requirements)
- **BR-01 [SaaS Core]:** O sistema deve aguentar a hospedagem de dados, conversas locais e documentos de IA de múltiplas "Contas" (Prefeituras) no mesmo servidor nativo (Hostinger VPS) de modo isolado.
- **BR-02 [Configuração Dinâmica]:** A infraestrutura deve suportar a parametrização de cada cliente, providenciando na saída de suas APIs interações lendo o seu `{bot_name}` e `{client_name}` apropriado. 
- **BR-03 [Onboarding Rápido]:** Processos de subida de novos clientes (Tenant Creation) não devem requerer re-deploy da infraestrutura de backend em produção, mas apenas um script ou payload executado no banco, viabilizando vendas expressas.
- **BR-04 [Conformidade Regulatória]:** Qualquer ação tomada envolvendo exclusão de cliente (desativação de prefeitura) deve conseguir garantir exclusão definitiva (Right to be Forgotten) e imediata de sua Knowledge Base e banco vetorial, uma obrigação da LGPD.

## 3. Requisitos Funcionais (Functional Requirements)
- **FR-01 [Webhook Router]:** A API pública de recepção de eventos da Meta deve identificar, processar a carga (JSON/Payload) de entrada, analisar de quem veio (e.g. Page ID, Application ID), e associar rapidamente a requisição no sistema ao registro correspondente na base da prefeitura.
- **FR-02 [Isolamento de Credenciais]:** Tokens do Facebook/Instagram não devem estar estáticos (hard-coded/environment variables). O sistema de envio de mensagem deve buscar os tokens de integração associados à prefeitura (Tenant) executando o processo.
- **FR-03 [Isolamento de Resposta]:** A construção do System Prompt para a chamada do LLM deve obrigatoriamente referenciar disclaimers, tom de voz ou links administrativos do cliente atual da thread (Governo A via Ouvidoria A vs Governo B via Site B).
- **FR-04 [Base Isolada de Conhecimento]:** Os resultados de RAG devem originar EXATAMENTE do subset de indexações do banco pertinente ao Tenant em questão, sem index cruzado. O index de um Diário Oficial da prefeitura de "Santa Cecília" nunca poderá aparecer de RAG query advindo da conta da prefeitura de "Esperança". 
- **FR-05 [Ecossistema Integrado]:** O SaaS (nexo-gov-api) não fará provisão própria de Bancos de Dados, utilizando as instâncias `nexo-postgres` (Relacional RLS), `nexo-chromadb` (Vetorização) e sendo servido exclusivamente na porta host **8101** sob proxy do Traefik da stack unificada `infra/`.

## 4. Requisitos Não Funcionais (Non-Functional Requirements)
- **NFR-01 [Segurança de Dados Transacional (RLS)]:** Por padrão de segurança, transações em tabelas sensíveis de Banco de Dados relacionais devem abortar se executadas sem `tenant_id` ativo atrelado ao pool de requisição. A política de proteção Row Level Security do PostgreSQL fará a vedação na camada inferior de infra, independentemente da verificação pelo app backend.
- **NFR-02 [Docker Networking Strictness]:** O contêiner da aplicação obrigatoriamente fará join na rede de ponte `infra_nexo-network` via `external: true` e passará a apontar as strings de conexão não mais para localhost, mas para os hostnames dos recursos compartilhados (Ex: `postgresql://user:pass@nexo-postgres:5432/...`).
- **NFR-03 [Latência Cidadão]:** Rotinas intensivas do core da inteligência de dados (web crawling automático, chunking) DEVEM rodar separadamente do processo que atende e retorna respostas para os usuários no chat. 

## 5. Critérios de Aceite Globais (Definição de Pronto)
- **Smoke Guard Isolado:** Testes unitários E2E nos endpoints rodando simultaneamente os IDs de duas páginas falsas devem demonstrar preenchimentos de relatórios e de chats preenchidos unicamente nas contas e credenciais dos seus respectivos identificadores, sem exceções.
- **Validação de Porta e Domínio:** Docker Compose da aplicação não deve instanciar nenhum serviço externo (além do si mesmo), expondo limitadamente `8101:8000`, provido de Traefik Labels (se dinâmicos localmente) ou registrados no Dynamic.yml configurado em proxy.
