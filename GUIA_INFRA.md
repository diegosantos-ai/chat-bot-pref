# GUIA_INFRA - Infra Isolada e Compartilhada

> Guia operacional para o repositorio `infra/` como base unica de infraestrutura para varios projetos.
> Fonte de verdade para portas: `PORTS.md`.
> Ultima revisao: 2026-03-05.

---

## 1. Objetivo do `infra/`

O repositorio `infra/` foi isolado para centralizar recursos compartilhados:

- rede Docker comum;
- proxy reverso e TLS (Traefik);
- bancos, cache e servicos de dados;
- padrao de deploy, monitoramento e backup.

### Limite de responsabilidade

`infra/`:
- opera servicos compartilhados;
- define padrao de portas e roteamento;
- expoe recursos comuns para outros projetos.

Repositorios de aplicacao (`nexo-360`, `lead-scrapper`, outros):
- constroem imagem e logica de negocio;
- conectam na rede compartilhada;
- usam portas e dominios reservados no `infra/`.

---

## 2. Caminhos e Ambientes

| Ambiente | Caminho recomendado |
|---|---|
| Windows | `D:\Projetos\Desenvolvendo\Nexo\infra` |
| WSL | `/mnt/d/Projetos/Desenvolvendo/Nexo/infra` |
| VPS (deploy) | `~/infra` |

Boas praticas:
- validar contexto antes de rodar comandos (`pwd`, `hostname`);
- nao misturar comandos locais e de VPS na mesma sessao;
- alteracoes de producao sempre via `docker-compose.yml` e scripts do repo.

---

## 3. Estrutura do Repositorio

```text
infra/
|-- docker-compose.yml
|-- .env
|-- .env.example
|-- PORTS.md
|-- GUIA_INFRA.md
|-- TEMPLATE_NOVO_PROJETO.md
|-- scripts/
|   |-- deploy.sh
|   |-- monitor.sh
|   `-- backup.sh
|-- traefik/
|   |-- traefik.yml
|   `-- dynamic.yml
|-- docker/
|-- config/
`-- docs/
```

---

## 4. Stack Compartilhada Atual

Servicos base gerenciados por este repo:
- `nexo-traefik`
- `nexo-postgres`
- `nexo-postgres-vector`
- `nexo-redis`
- `nexo-chromadb`
- `nexo-mlflow`

Projetos conectados hoje (exemplos ativos):
- Nexo 360 e microsservicos (`8090-8095`)
- Nexo Orchestrator (`8100`)
- Nexo Conect (`18080`)
- N8N principal (`5678`) e N8N isolado do lead-scrapper (`5679`)

Detalhes completos de portas: ver `PORTS.md`.

---

## 5. Como Conectar um Novo Projeto

### Passo 1 - Reservar porta e dominio

1. Escolher porta livre conforme faixas em `PORTS.md`.
2. Definir subdominio (se publico) e registrar DNS.
3. Atualizar `PORTS.md` antes do deploy.

### Passo 2 - Conectar na rede compartilhada

Use rede externa existente (`infra_nexo-network`) no compose do novo projeto:

```yaml
services:
  meu-projeto-api:
    image: meu-projeto-api:latest
    container_name: meu-projeto-api
    ports:
      - "8101:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@nexo-postgres:5432/meu_projeto
      - REDIS_URL=redis://nexo-redis:6379
      - CHROMA_URL=http://nexo-chromadb:8000
    networks:
      - infra-network

networks:
  infra-network:
    external: true
    name: infra_nexo-network
```

### Passo 3 - Roteamento no Traefik

Neste projeto, o Traefik usa provider de arquivo (`traefik/dynamic.yml`).
Para expor novo dominio, adicionar router e service no arquivo:

```yaml
http:
  routers:
    meu-projeto:
      rule: "Host(`meu-projeto.nexobasis.tech`)"
      service: meu-projeto-service

  services:
    meu-projeto-service:
      loadBalancer:
        servers:
          - url: "http://meu-projeto-api:8000"
```

Aplicar alteracao:

```bash
docker compose restart traefik
```

### Passo 4 - Healthcheck e observabilidade

- expor endpoint de health no novo servico;
- validar com `scripts/monitor.sh`;
- acompanhar logs com `docker compose logs -f <service>`.

---

## 6. Operacao Padrao

```bash
# Deploy completo da stack infra
bash scripts/deploy.sh

# Healthcheck consolidado
bash scripts/monitor.sh

# Backup de volumes
bash scripts/backup.sh

# Estado atual de containers e portas
docker compose ps
docker ps --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}'
```

---

## 7. Checklist para Novo Projeto

- [ ] Porta reservada e registrada em `PORTS.md`
- [ ] Container conectado na rede `infra_nexo-network`
- [ ] Variaveis de conexao apontando para servicos compartilhados
- [ ] Rota adicionada em `traefik/dynamic.yml` (quando publico)
- [ ] DNS validado
- [ ] Healthcheck funcionando
- [ ] Logs e monitoramento validados
- [ ] Documentacao do projeto atualizada

---

## 8. Politica de Mudanca

1. Nao editar container manualmente em producao.
2. Toda mudanca estrutural passa por git + revisao.
3. Nao publicar segredo em markdown ou compose.
4. Mudou porta, rota ou volume: atualizar documentacao no mesmo commit.
5. Em duvida sobre impacto de rede/porta, parar e revisar antes do deploy.

---

## 9. Historico de Revisoes

| Data | Mudanca |
|---|---|
| 2026-03-05 | Guia reestruturado para `infra/` isolado e onboarding de novos projetos |
| 2026-02-23 | Atualizacoes operacionais iniciais |
| 2026-02-22 | Versao inicial |

