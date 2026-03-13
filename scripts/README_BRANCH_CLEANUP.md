# Limpeza de Branches do Repositório

Este diretório contém scripts para limpar branches do repositório, mantendo apenas `main` e `develop`.

## Objetivo

Mergear todas as branches secundárias na `develop` e depois deletá-las, mantendo apenas:
- `main` - branch padrão/produção
- `develop` - branch de desenvolvimento

## Branches Identificadas para Merge/Remoção

Baseado no estado atual do repositório (12/02/2026):

1. `copilot/merge-and-delete-secondary-branches` (branch atual de trabalho)
2. `copilot/sub-pr-44-again`
3. `copilot/sub-pr-44`
4. `diegosantos-ai-patch-1`
5. `diegosantos-ai-patch-2`
6. `master` (duplicate of main)
7. `metadeveloperconfig`
8. `organizacao`
9. `perf-rag`

## Uso

### Opção 1: GitHub Actions (recomendado - automático)

A forma mais fácil é usar o workflow do GitHub Actions que já está configurado:

1. Vá para o repositório no GitHub
2. Clique em "Actions" no menu superior
3. Selecione "Cleanup Branches" na lista de workflows à esquerda
4. Clique em "Run workflow" (botão à direita)
5. Digite `CONFIRM` no campo de confirmação
6. Clique em "Run workflow" para executar

O workflow irá:
- Fazer fetch de todas as branches
- Mergear todas as branches (exceto main) na develop
- Deletar todas as branches remotas (exceto main e develop)
- Mostrar um resumo do resultado

### Opção 2: Script Bash (para execução local em Linux/Mac)

```bash
# Dar permissão de execução
chmod +x scripts/cleanup_branches.sh

# Executar
./scripts/cleanup_branches.sh
```

### Opção 3: Script Python (multiplataforma)

```bash
# Executar diretamente
python scripts/cleanup_branches.py

# Ou com permissão de execução (Linux/Mac)
chmod +x scripts/cleanup_branches.py
./scripts/cleanup_branches.py
```

### Opção 4: Comandos Manuais

Se preferir executar manualmente:

```bash
# 1. Fetch todas as branches
git fetch --all

# 2. Checkout para develop
git checkout develop

# 3. Atualizar develop
git pull origin develop

# 4. Mergear cada branch (exemplo)
git merge origin/copilot/sub-pr-44-again --no-edit -m "Merge branch 'copilot/sub-pr-44-again' into develop"
git merge origin/copilot/sub-pr-44 --no-edit -m "Merge branch 'copilot/sub-pr-44' into develop"
git merge origin/diegosantos-ai-patch-1 --no-edit -m "Merge branch 'diegosantos-ai-patch-1' into develop"
git merge origin/diegosantos-ai-patch-2 --no-edit -m "Merge branch 'diegosantos-ai-patch-2' into develop"
git merge origin/master --no-edit -m "Merge branch 'master' into develop"
git merge origin/metadeveloperconfig --no-edit -m "Merge branch 'metadeveloperconfig' into develop"
git merge origin/organizacao --no-edit -m "Merge branch 'organizacao' into develop"
git merge origin/perf-rag --no-edit -m "Merge branch 'perf-rag' into develop"
git merge origin/copilot/merge-and-delete-secondary-branches --no-edit -m "Merge branch 'copilot/merge-and-delete-secondary-branches' into develop"

# 5. Push develop
git push origin develop

# 6. Deletar branches remotas
git push origin --delete copilot/merge-and-delete-secondary-branches
git push origin --delete copilot/sub-pr-44-again
git push origin --delete copilot/sub-pr-44
git push origin --delete diegosantos-ai-patch-1
git push origin --delete diegosantos-ai-patch-2
git push origin --delete master
git push origin --delete metadeveloperconfig
git push origin --delete organizacao
git push origin --delete perf-rag

# 7. Limpar branches locais
git branch -D copilot/merge-and-delete-secondary-branches
git branch -D copilot/sub-pr-44-again
git branch -D copilot/sub-pr-44
git branch -D diegosantos-ai-patch-1
git branch -D diegosantos-ai-patch-2
git branch -D master
git branch -D metadeveloperconfig
git branch -D organizacao
git branch -D perf-rag

# 8. Verificar resultado
git branch -a
```

## Tratamento de Conflitos

Se houver conflitos durante o merge, os scripts tentarão resolver automaticamente usando a estratégia `theirs` (mantendo as mudanças da branch sendo mergeada).

Para resolver conflitos manualmente:

```bash
# Se encontrar conflito
git merge origin/NOME_DA_BRANCH

# Resolver conflitos manualmente editando os arquivos
# Depois:
git add .
git commit -m "Resolve merge conflicts with NOME_DA_BRANCH"
```

## Notas Importantes

- **Backup**: Recomenda-se fazer backup antes de executar (ex: criar um fork ou baixar o repositório)
- **Permissões**: Você precisa ter permissões de push e delete no repositório remoto
- **Branches Protegidas**: Se `main` ou `develop` estiverem protegidas, ajuste as configurações no GitHub antes
- **Reversão**: Após deletar branches remotas, elas podem ser recuperadas do histórico do git dentro de ~30 dias

## Resultado Esperado

Após a execução, o repositório terá apenas duas branches:
- `main` (branch padrão)
- `develop` (branch de desenvolvimento com todo o histórico mergeado)

## Verificação

Para verificar o estado final:

```bash
# Listar branches locais
git branch

# Listar branches remotas
git branch -r

# Listar todas as branches
git branch -a
```

Deve mostrar apenas:
```
* develop
  main
  remotes/origin/develop
  remotes/origin/main
```
