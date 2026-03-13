# Scripts de suporte — n8n-specialist

Local: `C:\Users\santo\.agent\scripts`

Principais utilitários:

- `n8n_tools.py` — CLI Python para listar templates, criar placeholders de credentials e (opcional) importar workflows via API do n8n.
- `deploy_templates.ps1` — wrapper PowerShell que executa `n8n_tools.py deploy-all`.

Pré-requisitos:

1. Python 3.x
2. Instalar `requests` se desejar chamadas API:

```powershell
python -m pip install requests
```

Como usar:

1. Criar placeholders de credentials:

```powershell
python .\.agent\scripts\n8n_tools.py create-creds --out .\.agent\credentials
```

2. Deploy (se tiver N8N_URL e N8N_API_KEY):

```powershell
$env:N8N_URL = "https://seu-n8n"
$env:N8N_API_KEY = "sua_api_key"
python .\.agent\scripts\n8n_tools.py deploy-all
```

Também é possível executar deploy para um endpoint específico passando `--url` e `--api-key`:

```powershell
python .\.agent\scripts\n8n_tools.py deploy-cloud --url https://seu-n8n --api-key <sua_api_key>
```

Se a API do n8n não estiver disponível, o script apenas lista os templates e cria placeholders locais.
