# Matriz de Capacidades Arquiteturais e Padrões de Indústria

## Objetivo
Este documento consolida o alinhamento técnico entre o que foi construído durante as fases deste projeto e os requisitos fundamentais em desafios de Engenharia de IA, MLOps e Backend GenAI.

Ele não promete maturidade inexistente. Limita-se a mapear evidências já ativas na **Fundação Operacional** e suportadas por validações em repositório.

## Matriz de Capacidades vs Padrões de Mercado

| Requisito de Indústria | Implementação Real no Projeto | Evidência Objetiva | Status de Implementação | Lacuna Residual |
| --- | --- | --- | --- | --- |
| **Backend em Python moderno e APIs REST** | FastAPI modular, rotas isoladas (`/api/chat`, `/api/rag/*`, `/metrics`). Runtime assíncrono. | `app/main.py`, smoke tests locais e remotos passando. | Atendido | Nenhuma estrutural (não possui ORM complexo pois banco relacional não é do escopo crítico atual). |
| **Desenvolvimento e Deploy de soluçōes com LLM** | Adaptador de LLM isolado, GenAI com método (prompts versionados), pipeline semântico via provider mock. | Artefatos de resposta com modelo transacional em `fase10-smoke-dev.json` e `fase11`. | Atendido com ressalva | Uso atual restrito ao `mock` para demonstração offline/barata de CI, sem provider comercial engatado no runtime remoto em default. |
| **Governança, Guardrails e Segurança (IA Responsável)** | Pipeline com `policy_pre` e `policy_post`. Decisão imperativa (allow, deny, fallback) documentada no request. | Log gerado com tags `policy_pre=allow`, fallback acionado automaticamente por RAG vazio. | Atendido | Faltam barreiras externas agressivas como LLM-as-a-Judge no runtime (já testado nas fases de MLOps, mas não no path síncrono por latência). |
| **RAG (Retrieval-Augmented Generation) e Vector DBs** | Ingestão e recuperação semântica no ChromaDB operando nativamente em tenant-aware. | Endpoints `/api/rag/*` validados; test-cases verificam chunks por tenant. | Atendido | Coleção não escalável nativamente (Chroma local). Para clusterização, requer outro componente (Qdrant, Milvus). |
| **Observabilidade, Logging, Tracing** | Propagação de contexto no fluxo (`X-Request-ID`); logging JSONL; Exportação de Traces (OpenTelemetry e Prometheus). | Traces salvos localmente (`logs/trace_*.jsonl`); `/metrics` retornando latência. | Atendido | Telemetria roda local e em arquivos, não está plugada em um Grafana/Datadog permanente. |
| **Arquitetura Multi-Tenant** | `tenant_id` exigido por contrato; persistência, RAG, e auditorias isoladas por inquilino. | Exceção gerada no middleware quando request sai sem `tenant_id`. Auditorias separadas na file tree. | Atendido | Nenhuma (contrato validado em todas as etapas). |
| **Práticas DevOps/SRE e CI/CD** | `Dockerfile`, `docker-compose.yml`, GitHub Actions com quality gates estruturais, provisionamento AWS via Terraform. | `ci.yml` cobrindo lint/smoke; `.tf` scripts e smoke testes remotos logando OK. | Atendido | Deploy atual em EC2 simplificada (single-node) em modo demonstrativo, não em cluster GKE/EKS autogerenciado. |

## Resumo das Entregas (Provas de Trabalho)
Esta iniciativa se consolida como uma prova real de execução arquitetural:
- Separação clara de runtime síncrono e experimentação assíncrona (LLMOps).
- Abordagem rigorosa de tracking de decisão por `request_id`.
- Pragmatismo técnico (não há dependências mágicas mascarando o fluxo RAG).
