# System Design: Nexo Basis White-Label SaaS

## 1. Arquitetura Alvo
O sistema fará a transição de um script isolado/monolítico focado num município para uma **Arquitetura Multi-Tenant isolada logicamente**. 
O core backend será guiado por APIs (FastAPI), apoiado em PostgreSQL (dados relacionais/logs e configurações de prefeituras) e ChromaDB (RAG Vector Store).

## 2. Padrões Arquiteturais Definidos
- **Multi-Tenancy Relacional (Row-Level Security):** O banco de dados usará RLS no PostgreSQL. Uma variável de contexto (`app.current_tenant`) no PostgreSQL será definida via middleware antes de qualquer transação de banco de dados, protegendo e isolando implicitamente todos os comandos `SELECT`, `UPDATE`, e `DELETE` mediante checagem global da tabela contra o `tenant_id` ativo. Isso resolve de vez vazamentos causados por descuido em queries SQL.
- **RAG Logical Isolation:** O ChromaDB usará o conceito de "Collections" distintas para isolamento vetorial. Nome da coleção padrão: `{tenant_id}_knowledge_base`. Isso atende à LGPD garantindo Direito a Deleção (Exclusão total do banco vetorial de um parceiro na recisao contratual) de forma simples através do *Drop Collection*.
- **API Context Middleware:** Um Middleware Global interceptará requisições webhooks recebidas pela Meta API. Ao acessar o ID da Página originária ou token do Request, fará uma busca ultra-rápida (em memória local LRU ou na configuração global) associando o webhook à um Cliente (`tenant_id`). Usaremos `contextvars` do Python para sustentar a sessão assíncrona.
- **Infraestrutura Compartilhada (Shared Infra):** O SaaS será hospedado como um contêiner conectado à rede externa `infra_nexo-network`, aproveitando os recursos unificados gerenciados pelo repositório base `infra/`. Isso significa que o SaaS **não subirá seus próprios bancos PostgreSQL/ChromaDB em seu docker-compose**, mas sim se conectará às instâncias unificadas (`nexo-postgres`, `nexo-chromadb`, `nexo-redis`). O roteamento de borda e terminação TLS ficará exclusivamente a cargo do **Traefik**. O projeto alocará a porta livre **8101** no host (`8101:8000`) e seu roteamento (ex: `gov.nexobasis.tech`) será configurado no `dynamic.yml` do Traefik local/VPS.

## 3. Diagrama Lógico de Fluxo (Tratando Evento de Webhook)

```mermaid
sequenceDiagram
    participant Meta UI (Cidadão)
    participant Traefik (Proxy Ingress)
    participant FastAPI (nexo-gov-api:8101)
    participant Context Middleware
    participant Chroma DB (Shared:8000)
    participant PostgreSQL (Shared:5432)
    participant LLM API (OpenAI/Anthropic)

    Meta UI (Cidadão)->>Traefik (Proxy Ingress): Webhook Request
    Traefik (Proxy Ingress)->>FastAPI (nexo-gov-api:8101): Roteia (Network infra_nexo-network)
    FastAPI (nexo-gov-api:8101)->>Context Middleware: Intercepta Payload
    Note over Context Middleware: Resolve PageID X para Tenant = 442
    Context Middleware->>PostgreSQL (Shared:5432): SET LOCAL app.tenant = 442;
    Context Middleware->>Chroma DB (Shared:8000): Collection = 442_knowledge_base
    Chroma DB (Shared:8000)-->>Context Middleware: Retorna dados vetoriais de leis
    Context Middleware->>LLM API (OpenAI/Anthropic): Geração de resposta RAG
    LLM API (OpenAI/Anthropic)-->>Context Middleware: Resposta formatada
    Context Middleware->>PostgreSQL (Shared:5432): Grava logs auditados no Tenant 442
    Context Middleware->>Traefik (Proxy Ingress): OK
```

## 4. Suposições e Restrições Assumidas (Trade-offs)
- **Collections Dinâmicas vs Unified Collection com Metadata Filter:** Ter, digamos, 10 collections no Chroma exige marginalmente mais RAM do que criar apenas 1 coleção gigantesca filtrando com metadata tags. O trade-off resultou em favorecimento às Collections distintas focado em prefeituras.
- **Desacoplamento de Infra:** Em vez de mantermos o Docker Compose com todos os serviços embutidos no repositório do chatbot, externalizaremos o banco de dados e o vector store para a Infra Central (`infra/`). O trade-off é que desenvolvedores precisam ter o a rede `infra_nexo-network` rodando para desenvolverem localmente, mas em contrapartida elimina duplicação de dados e conflitos de portas na VPS.
