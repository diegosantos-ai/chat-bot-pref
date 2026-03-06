<#
Script PowerShell para criar labels no repositório via GitHub CLI (`gh`).
Uso (PowerShell):
  $env:GITHUB_REPO = 'owner/repo'
  gh auth login
  .\scripts\create_labels.ps1
#>
if (-not $env:GITHUB_REPO) {
  Write-Error "Defina a variável de ambiente GITHUB_REPO (owner/repo) antes de executar"
  exit 1
}

Write-Host "Criando labels em $($env:GITHUB_REPO)..."

function Create-Label($name, $color, $desc) {
  gh label create "$name" --color $color --description "$desc" --repo $env:GITHUB_REPO 2>$null
}

Create-Label "bug" d73a4a "Bug funcional que precisa correção"
Create-Label "enhancement" a2eeef "Nova funcionalidade / melhoria"
Create-Label "task" 0e8a16 "Tarefa operacional geral"
Create-Label "infra" 5319e7 "Infraestrutura / deploy / cloud"
Create-Label "db" 8e6ad8 "Banco de dados / migrations / backup"
Create-Label "observability" 1d76db "Métricas, dashboards e alertas"
Create-Label "security" fbca04 "Segurança, LGPD, PII e políticas"
Create-Label "docs" 0075ca "Documentação e runbooks"
Create-Label "test" d4c5f9 "Testes, smoke tests, E2E"
Create-Label "performance" 0052cc "Latência e otimizações"
Create-Label "blocked" b60205 "Impeditivo / dependência externa"
Create-Label "needs-review" ffd3b6 "Pronto para revisão / QA"
Create-Label "priority:high" b60205 "Alta prioridade / urgente"
Create-Label "help wanted" 008672 "Precisa de ajuda externa"
Create-Label "smoke-test" 0e8a16 "Teste rápido em produção"
Create-Label "policy" a2eeef "Mudanças em PolicyGuard e protocolos"
Create-Label "chore" c2e0c6 "Manutenção sem entrega funcional"

Write-Host "Concluído. Revise as labels em: https://github.com/$($env:GITHUB_REPO)/labels"
