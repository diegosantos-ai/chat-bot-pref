# Diagrama de Fluxo End-to-End do Sistema

Este diagrama ilustra a arquitetura completa da aplicação, destacando o isolamento multitenant, os *guardrails* de segurança e o pipeline de LLMOps (teste e tracking contínuo).

```mermaid
graph TD
    %% ==========================================
    %% 🎨 CLASSES DE ESTILO CORES E FORMATOS
    %% ==========================================
    classDef channel fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b
    classDef api fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#e65100
    classDef core fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1b5e20
    classDef storage fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px,color:#4a148c
    classDef ops fill:#ffebee,stroke:#d32f2f,stroke-width:2px,color:#b71c1c
    classDef note fill:#fff9c4,stroke:#fbc02d,stroke-width:1px,stroke-dasharray: 5 5,color:#333

    %% ==========================================
    %% 📦 AGRUPAMENTOS E COMPONENTES
    %% ==========================================

    subgraph Client_Layer ["👤 1. Canais de Entrada"]
        API_User["💻 Client API Rest<br/>(Integração Direta)"]:::channel
        Telegram["📱 Telegram Bot<br/>(Webhook)"]:::channel
    end

    subgraph API_Gateway ["🌐 2. Camada API & Roteamento"]
        MainRouter["🚦 Router FastAPI<br/>(/api/chat)"]:::api
        Tenant["🏢 Tenant Resolver<br/>(Isolamento Estrito)"]:::api
    end

    subgraph Engine ["⚙️ 3. Core Engine & Segurança"]
        PolicyPre["🛡️ Guardrail Pre-Flight<br/>(Anti-Jailbreak / Sanitização)"]:::core
        RAG["🔍 RAG Service<br/>(Motor de Busca em Documentos)"]:::core
        LLM_Adapter["🧠 LLM Adapter<br/>(Mock / Agnostic Provider)"]:::core
        PolicyPost["🛡️ Guardrail Post-Flight<br/>(Toxicidade / Tom)"]:::core
    end

    subgraph Storage_Layer ["💾 4. Armazenamento de Dados"]
        Chroma[("🗄️ ChromaDB<br/>(Banco de Vetores)")]:::storage
        Docs[("📂 Artefatos Base<br/>(Documentos PDF/MD/TXT)")]:::storage
        Audit[("📝 Repositório de Auditoria<br/>(Logs Isolados)")]:::storage
    end

    subgraph LLMOps ["🔬 5. Governança & LLMOps offline"]
        Otel["📡 Telemetria OpenTelemetry<br/>(X-Request-ID)"]:::ops
        MLFlow["📊 MLFlow Tracking<br/>(Métricas de Qualidade)"]:::ops
        CI_CD["⚙️ GitHub Actions CI<br/>(Gate de Aprovação LLM)"]:::ops
    end

    %% ==========================================
    %% 💡 NOTAS EXPLICATIVAS (Caixas de observação)
    %% ==========================================
    NoteTenant["💡 O Gateway impede o request se<br/>o tenant_id for inexistente"]:::note
    NoteRAG["💡 Busca feita estritamente no<br/>espaço vetorial do Tenant logado"]:::note
    NoteQuality["💡 O deploy falha caso o Ragas avalie<br/>cases_evaluated = 0 ou score ruim"]:::note

    %% ==========================================
    %% 🔄 FLUXO DE EXECUÇÃO
    %% ==========================================

    API_User -->|"POST HTTP"| MainRouter
    Telegram -->|"Payload JSON"| MainRouter

    MainRouter --> Tenant
    Tenant -.- NoteTenant

    Tenant -->|"Passa Contexto Seguro"| PolicyPre

    PolicyPre -->|"Aprovado: Regras OK"| RAG
    PolicyPre -.->|"Bloqueado: Retorno Direto"| Audit

    RAG -.- NoteRAG
    RAG <-->|"Busca de Similaridade"| Chroma
    Chroma -.->|"Vetorização Ingest"| Docs

    RAG -->|"Contexto + Prompt"| LLM_Adapter

    LLM_Adapter -->|"Geração Bruta"| PolicyPost
    PolicyPost -->|"Aprovado"| Audit
    PolicyPost -.->|"Desvio/Bloqueado"| Audit

    Audit -->|"Resposta Final"| MainRouter

    %% ==========================================
    %% 📡 FLUXO DE OBSERVABILIDADE E OPS
    %% ==========================================
    MainRouter -.->|"Traces Síncronos"| Otel
    Audit -.->|"Exportação Batch Offline"| MLFlow
    MLFlow -.->|"Validação Dry-Run"| CI_CD
    CI_CD -.- NoteQuality
```
