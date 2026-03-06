# Migration: Deploy Webhook

**Data**: 2025-02-05
**Autor**: AI Assistant
**Tipo**: Nova funcionalidade

## Descrição

Adiciona webhook para deploy automático via CI/CD (GitHub Actions).
Ao fazer push para `main`, o GitHub Actions chama o endpoint que executa git pull e reinicia o serviço.

## Mudanças

### Código
- `app/api/deploy.py`: Novo endpoint `POST /updateAPI`
- `app/settings.py`: Nova variável `DEPLOY_WEBHOOK_TOKEN`
- `app/main.py`: Registro do router de deploy
- `.github/workflows/deploy.yml`: Workflow de deploy automático

### Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `DEPLOY_WEBHOOK_TOKEN` | Sim | Token para autorizar chamadas ao webhook |

## Ações no Servidor

1. Adicionar no `.env` do servidor:
   ```bash
   DEPLOY_WEBHOOK_TOKEN=moneyCalled
   ```

2. Reiniciar o serviço para carregar a nova variável:
   ```bash
   sudo systemctl restart terezia-api
   ```

## Ações no GitHub

1. Adicionar secret no repositório:
   - **Nome**: `DEPLOY_WEBHOOK_TOKEN`
   - **Valor**: `moneyCalled`
   - **Local**: Settings > Secrets and variables > Actions > New repository secret

## Fluxo de Deploy

```
┌─────────────┐     push      ┌─────────────────┐
│   GitHub    │ ────────────> │  GitHub Actions │
│    (main)   │               │   deploy.yml    │
└─────────────┘               └────────┬────────┘
                                       │
                                       │ POST /tereziapi/updateAPI
                                       │ X-Deploy-Token: moneyCalled
                                       ▼
                              ┌─────────────────┐
                              │   nexobasis.br  │
                              │   terezia-api   │
                              └────────┬────────┘
                                       │
                                       │ 1. git fetch --all
                                       │ 2. git pull --ff-only
                                       │ 3. systemctl restart
                                       ▼
                              ┌─────────────────┐
                              │   Nova versão   │
                              │   em produção   │
                              └─────────────────┘
```

## Teste Manual

```bash
curl -X POST https://nexobasis.com.br/tereziapi/updateAPI \
  -H "X-Deploy-Token: moneyCalled"
```

## Rollback

Se necessário reverter:
1. SSH no servidor
2. `cd /root/pilot-atendimento && git checkout <commit_anterior>`
3. `sudo systemctl restart terezia-api`

## Segurança

- Token validado via header `X-Deploy-Token`
- Logs de todas as tentativas de deploy (autorizadas e rejeitadas)
- Retorna erro 401 para token inválido, 503 se token não configurado
- Retorna erro 500 com detalhes se o deploy falhar
