# PORTS - Infra Compartilhada

> Fonte de verdade das portas expostas no host pela stack `infra/`.
> Escopo: operacao atual + referencia para onboarding de novos projetos.
> Ultima atualizacao: 2026-03-05 (snapshot de `docker ps`).

---

## 1. Regras de Alocacao

- Toda porta publicada no host deve ser registrada aqui antes de deploy.
- Priorizar acesso externo via Traefik (`80`/`443`) sempre que possivel.
- Novos projetos devem usar faixas livres definidas na secao 5.
- Em caso de conflito de documento, este arquivo prevalece para portas.

---

## 2. Infra Base (Compartilhada)

| Porta host:container | Container | Servico | Observacao |
|---|---|---|---|
| `80:80` | `nexo-traefik` | Traefik HTTP | Entrada publica |
| `443:443` | `nexo-traefik` | Traefik HTTPS | Entrada publica TLS |
| `8099:8080` | `nexo-traefik` | Traefik Dashboard | Acesso interno/admin |
| `5432:5432` | `nexo-postgres` | PostgreSQL principal | DB transacional |
| `5433:5432` | `nexo-postgres-vector` | PostgreSQL pgvector | Vetores/embeddings |
| `6379:6379` | `nexo-redis` | Redis | Cache/filas |
| `8000:8000` | `nexo-chromadb` | ChromaDB | Vetor store |
| `5000:5000` | `nexo-mlflow` | MLflow | Tracking ML |

---

## 3. APIs e Servicos de Projeto (Atuais)

| Porta host:container | Container | Projeto/Servico | Dominio principal |
|---|---|---|---|
| `8080:8080` | `nexo-suporte-api` | Nexo Suporte | `suporte.nexobasis.tech` |
| `8085:8080` | `agencia-antigravity-api` | Agencia Antigravity | `agencia.nexobasis.tech` |
| `8090:8000` | `nexo-360-api` | Nexo 360 API | `api.nexobasis.tech` |
| `8091:8000` | `nexo-growth-api` | Nexo Growth | `growth.nexobasis.tech` |
| `8092:8000` | `nexo-talent-api` | Nexo Talent | `talent.nexobasis.tech` |
| `8093:8000` | `nexo-admin-api` | Nexo Admin | `admin.nexobasis.tech` |
| `8094:8000` | `nexo-insights-api` | Nexo Insights | `insights.nexobasis.tech` |
| `8095:8000` | `nexo-finance-api` | Nexo Finance | `finance.nexobasis.tech` |
| `8100:8000` | `nexo-orchestrator` | Nexo Orchestrator | interno |
| `18080:8080` | `nexo-conect-api` | Nexo Conect | interno/edge |

---

## 4. Tooling e Integracoes

| Porta host:container | Container | Uso |
|---|---|---|
| `4040:4040` | `nexo-ngrok` | Inspecao de tunel |
| `5678:5678` | `nexo-n8n` | Automacao principal |
| `5679:5678` | `lead-scraper-n8n` | Automacao isolada (`lead-scrapper`) |

---

## 5. Faixas Recomendadas para Novos Projetos

| Faixa de porta no host | Regra |
|---|---|
| `8101-8199` | Novas APIs HTTP da plataforma |
| `8200-8299` | Frontends, paineis e consoles de projeto |
| `18081-18199` | Integracoes que exigem container em `8080` |
| `9000-9099` | Ferramentas tecnicas internas/observabilidade |

Notas:
- `80`, `443`, `5000`, `5432`, `5433`, `5678`, `5679`, `6379`, `8000`, `8080`, `8085`, `8090-8100`, `18080` ja estao ocupadas.
- Antes de reservar nova porta, validar com `docker ps` e `ss -lnt`.

---

## 6. Checklist de Reserva de Porta

1. Escolher porta livre na faixa correta.
2. Registrar aqui a nova porta (antes do merge/deploy).
3. Publicar a porta no `docker-compose.yml` do projeto.
4. Atualizar `GUIA_INFRA.md` se houver novo padrao.
5. Validar conflito com `docker ps --format 'table {{.Names}}\t{{.Ports}}'`.

---

## 7. Comandos de Verificacao Rapida

```bash
# Portas publicadas pelos containers ativos
docker ps --format 'table {{.Names}}\t{{.Ports}}'

# Validar portas em escuta no host
ss -lnt

# Validar compose da infra
docker compose config
```

