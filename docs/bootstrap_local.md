# Bootstrap Local

Este documento descreve o ambiente local de desenvolvimento usando Docker.

## Pré-requisitos

- Docker Desktop instalado e configurado
- Porta 8000 disponível (ou configurar `APP_PORT`)

## Subir ambiente

```bash
# Usando porta padrão (8000)
docker compose -f docker-compose.local.yml up -d

# Usando porta alternativa
APP_PORT=8001 docker compose -f docker-compose.local.yml up -d
```

## Parar ambiente

```bash
docker compose -f docker-compose.local.yml down
```

## Inspecionar

```bash
# Ver logs
docker logs chat-pref-api-dev

# Ver status
docker ps --filter "name=chat-pref-api-dev"

# Acessar shell (se necessário)
docker exec -it chat-pref-api-dev sh
```

## Health check

```bash
# Porta padrão
curl http://localhost:8000/health

# Porta alternativa
curl http://localhost:8001/health
```

## Notas

- O compose local usa `Dockerfile.dev` que inclui `ai_artifacts` para desenvolvimento.
- O compose de produção (`docker-compose.yml`) usa `Dockerfile` padrão.
- Dados são persistidos no volume `chat_pref_data`.
