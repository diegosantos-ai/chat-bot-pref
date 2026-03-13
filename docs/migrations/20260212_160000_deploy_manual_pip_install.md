# Migration: Deploy Manual e Instalação de Dependências Automática

**Data**: 2026-02-12
**Autor**: {bot_name} Dev Team
**Tipo**: Alteração de Processo de Deploy

## Resumo

Altera o processo de deploy de automático (on push) para manual (workflow_dispatch) e adiciona instalação automática de dependências (pip install) antes de reiniciar o serviço.

## Mudanças Implementadas

### 1. GitHub Actions - Trigger Manual

**Arquivo**: `.github/workflows/deploy.yml`

**Alteração**:
- Removido trigger automático `on: push: branches: [master]`
- Adicionado trigger manual `on: workflow_dispatch`

**Como usar**:
1. Acesse o GitHub Actions no repositório
2. Selecione o workflow "Deploy to Production"
3. Clique em "Run workflow"
4. O deploy será executado manualmente

### 2. Webhook de Deploy - Instalação de Dependências

**Arquivo**: `app/api/deploy.py`

**Alteração**:
Adicionado passo de instalação de dependências entre `git pull` e `systemctl restart`:

```python
# 4. Instalar dependências do requirements.txt
pip_result = subprocess.run(
    ["bash", "-c", "source venv/bin/activate && pip install -r requirements.txt"],
    cwd=work_dir,
    capture_output=True,
    text=True,
    timeout=300,
)
```

**Fluxo atualizado**:
1. ✅ Git fetch
2. ✅ Git pull
3. ✅ **NEW: pip install -r requirements.txt** (no venv)
4. ✅ Systemctl restart

**Observações**:
- Timeout de 5 minutos (300s) para instalação de dependências
- Se pip install falhar, o deploy continua (apenas loga o erro)
- Últimos 500 caracteres do output são capturados para o log

## Benefícios

1. **Controle**: Deploy só executa quando explicitamente solicitado
2. **Segurança**: Evita deploys acidentais em commits intermediários
3. **Automação**: Dependências são atualizadas automaticamente no deploy
4. **Rastreabilidade**: Quem executou o deploy fica registrado no GitHub Actions

## Rollback

Para voltar ao deploy automático:

1. **GitHub Actions**: Substitua `on: workflow_dispatch` por:
   ```yaml
   on:
     push:
       branches:
         - master
   ```

2. **Webhook**: Remova o bloco de `pip install` do `app/api/deploy.py`

## Testes

Para testar o novo fluxo:

1. Execute o workflow manualmente no GitHub Actions
2. Verifique os logs do webhook em `/var/log/terezia-api/`
3. Confirme que o serviço reiniciou corretamente: `systemctl status terezia-api`

## Referências

- Documentação GitHub Actions: https://docs.github.com/en/actions/using-workflows/manually-running-a-workflow
- Endpoint: `POST /updateAPI` com header `X-Deploy-Token`
