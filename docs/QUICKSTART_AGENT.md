# {bot_name} - Guia Rápido para o Agente

Guia de referência rápida para desenvolvimento e operação do assistente virtual {bot_name}.

## 📋 Visão Geral
- **Nome**: {bot_name} - Chatbot da Prefeitura de {client_name} - PR
- **Objetivo**: Atendimento informativo via Facebook/Instagram
- **Natureza**: Estritamente informativa (não realiza atos administrativos)
- **Stack**: Python 3.11+ | FastAPI | PostgreSQL | ChromaDB | Google Gemini
- **Status**: Fase 5 (Deploy & Observabilidade) EM PROGRESSO

## ⚠️ Diretrizes Críticas (NÃO ESQUECER)
1. **Caráter Informativo**: Apenas informar documentos, horários, endereços, procedimentos
2. **Proibido**: Agendar, processar isenções, prometer prazos não oficiais
3. **Redirecionamento Assistido**: Explicar regra + fornecer contato/link
4. **Disclaimer Obrigatório**: "Informações baseadas na base oficial. Para decisões legais, consulte o Diário Oficial."
5. **Identidade**: Sempre se identificar como "IA em treinamento"

## 🚨 Protocolos de Crise (Respostas Estáticas)
| Cenário | Ação | Contatos |
|---------|------|----------|
| Suicídio | Interromper, resposta empática | CVV 188, SAMU 192 |
| Violência | Fornecer canais de denúncia | 180, 100, PM 190, Conselho Tutelar |
| Fake News | Não engajar | Redirecionar notas oficiais |
| Ofensas | Não responder | Notificar moderação |

## 📞 Telefones de Redirecionamento
- Prefeitura: (45) 3124-1000 | Av. Paraná, 61
- Saúde: (45) 3124-1020 | Av. Brasília, 525
- SAMU: 192
- Educação: (45) 3124-1010 | R. Internacional, 1597
- Assistência Social: (45) 3124-1030 | Av. Brasília, 1050
- Conselho Tutelar: (45) 3124-1035 (PM 190)
- Meio Ambiente: (45) 3124-1095

## 🏗️ Arquitetura do Pipeline

```
Input (Webhook FB/IG)
    ↓
Classifier (Intent)
    ↓
Policy Guard PRE (Security)
    ↓
RAG (Retriever → Composer)
    ↓
Policy Guard POST (Validation)
    ↓
Response (Audit)
```

**Decisões Especiais**:
- GREETING → resposta direta
- COMPLIMENT (público) → ACK
- HUMAN_HANDOFF → escalate
- NO_REPLY → silêncio
- BLOCK → bloqueio/ouvidoria
- CRISIS → resposta estática

## 📁 Estrutura Principal
```
app/
├── main.py              # FastAPI entry point
├── settings.py          # Configurações
├── orchestrator/service.py  # Pipeline completo
├── classifier/service.py    # Classificação de intenção
├── policy_guard/service.py   # Guardrails PRE/POST
├── rag/
│   ├── retriever.py     # ChromaDB search
│   ├── composer.py      # LLM generation
│   └── ingest.py        # Markdown parsing
├── nlp/                 # Sentimento, normalização, query expansion
├── channels/            # Meta sender/adapter
├── integrations/meta/   # Webhook, security, client
├── audit/               # PostgreSQL repository
└── contracts/           # Enums, DTOs
```

## 🔑 Contratos Principais

**Enums** (`app/contracts/enums.py`):
- `Intent`: GREETING, COMPLIMENT, INFO_REQUEST, SCHEDULE_QUERY, CONTACT_REQUEST, COMPLAINT, HUMAN_HANDOFF, OUT_OF_SCOPE
- `Decision`: ANSWER_RAG, ANSWER_DIRECT, PUBLIC_ACK, PUBLIC_REDIRECT, FALLBACK, ESCALATE, NO_REPLY, BLOCK
- `ResponseType`: SUCCESS, FALLBACK, BLOCKED, ESCALATED, NO_REPLY, ERROR
- `PolicyDecision`: ALLOW, ALLOW_LIMITED, REDIRECT, NO_REPLY, BLOCK
- `Channel`: WEB_WIDGET, INSTAGRAM_DM, INSTAGRAM_COMMENT, FACEBOOK_DM, FACEBOOK_COMMENT
- `SurfaceType`: INBOX, PUBLIC_COMMENT, WEB

**DTOs** (`app/contracts/dto.py`):
- `ChatRequest`: session_id, message, channel, surface_type
- `ChatResponse`: session_id, message, intent, decision, response_type, base_id, docs_found, sources
- `RequestContext`: Contexto acumulado através do pipeline

## ⚙️ Configurações Chave

```python
# LLM
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_TEMPERATURE = 0.3
GEMINI_MAX_TOKENS = 1024

# RAG
RAG_BASE_ID = "default"
RAG_TOP_K = 5
RAG_MIN_SCORE = 0.3

# Policy Guard
POLICY_MAX_MESSAGE_LENGTH = 2000
POLICY_PUBLIC_COMMENT_MAX_LENGTH = 280

# Meta
META_API_VERSION = "v19.0"
```

## 📚 Base de Conhecimento RAG
**Localização**: `base/default/items/`

**Documentos**:
- `0001_horarios.md` - Horários de atendimento, secretarias, ônibus
- `0002_contatos.md` - Matriz de redirecionamento, telefones
- `0003_secretarias.md` - Descrição das secretarias
- `0004_saude.md` - Unidades de saúde, PSFs, horários
- `0005_empreendedor.md` - Agência do Trabalhador, MEI
- `0006_tributacao.md` - IPTU 2025, REFIS, Nota Fiscal
- `0007_assistencia_social.md` - CRAS, Conselho Tutelar
- `0008_educacao.md` - Matrículas 2026, escolas

## 🧪 Testes e Validação

**Smoke Tests** (produção):
- ✅ Qual o telefone da prefeitura?
- ✅ Qual o horário do posto de saúde?
- ✅ Documentos para matrícula escolar?
- ✅ Segunda via do IPTU?
- ➡️ Agendar consulta médica (redirecionar)
- ➡️ Parcelar dívida IPTU (redirecionar)
- 🚨 Quero me matar (crise)
- 🚨 Sofrendo violência (crise)
- ❓ Capital da França? (fora de escopo)
- ❓ Me conte uma piada (fora de escopo)

## 🚀 Comandos Úteis

```bash
# Validar infraestrutura
python scripts/ops/validate_infrastructure.py

# Setup banco de dados
python scripts/setup_db.py --database-url postgresql://user:pwd@host:5432/db

# Executar API
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Teste webhook
python scripts/test_webhook_local.py

# Simular webhook
python scripts/simulate_webhook.py

# Verificar tokens Meta
python scripts/verify_meta_tokens.py
```

## 📊 Endpoints API
- `GET /` e `GET /health` — Saúde do serviço
- `POST /api/chat` — Entrada padrão (JSON)
- `POST /api/chat/simple` — Teste rápido (query params)
- `POST /webhook/meta` — Webhook Meta (FB/IG) com HMAC

## 📖 Referências Principais
| Arquivo | Descrição |
|---------|----------|
| `AGENTS.md` | Contexto completo (FONTE DA VERDADE) |
| `README.md` | Detalhes técnicos, setup, status |
| `docs/estudo.md` | Regras de negócio, FAQs |
| `app/policy_guard/service.py` | Guardrails de segurança |
| `app/orchestrator/service.py` | Pipeline completo |
| `db/schema.sql` | Schema PostgreSQL |

## 🛡️ Policy Guard - Padrões de Detecção

**Prevenção**:
- PROMPT_INJECTION: jailbreak, ignore instructions, pretend
- PII: CPF, RG, dados pessoais, bancários
- OFFENSIVE: palavrões, ameaças, ofensas
- CRISIS_SUICIDE: quero me matar, suicídio, desisto
- CRISIS_VIOLENCE: bateram, agrediu, violência doméstica
- HEALTH_CLINICAL: dor, sintoma, médico, remédio, emergência
- OUT_OF_SCOPE: casamento, concurso, emprego, política

## 💡 Dicas de Desenvolvimento

**Python**:
- Python 3.11+
- Type hints obrigatórios
- Pydantic para validação
- Async/await para I/O

**FastAPI**:
- Routers modularizados
- OpenAPI/Swagger em `/docs`
- CORS habilitado (dev)

**Banco de Dados**:
- PostgreSQL 15+
- UUIDs para identificadores
- Timestamptz para timestamps
- Índices para queries comuns

**Segurança**:
- HMAC-SHA256 para webhooks
- Env variables em .env
- Policy guard PRE/POST
- Detecção de PII e prompt injection

---
**Para informações completas, consulte: [AGENTS.md](./AGENTS.md)**
