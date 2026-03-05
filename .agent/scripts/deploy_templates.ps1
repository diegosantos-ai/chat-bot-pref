<#
Wrapper PowerShell para deploy de templates n8n usando o script Python.

Uso (com n8n API configurada):

$env:N8N_URL = "https://seu-n8n.example.com"
$env:N8N_API_KEY = "seu_api_key"
python .\.agent\scripts\n8n_tools.py deploy-all

Para criar placeholders de credentials:
python .\.agent\scripts\n8n_tools.py create-creds --out .\.agent\credentials
#>

param()

Write-Host "Executando deploy de templates..."
python "$PSScriptRoot\n8n_tools.py" deploy-all
