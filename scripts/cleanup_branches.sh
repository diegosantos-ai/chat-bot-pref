#!/bin/bash

# Script para limpar branches do repositório
# Mantém apenas main e develop, mergeando todas as outras na develop

set -e

echo "🔧 Iniciando limpeza de branches..."

# Configuração
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

# Verificar se estamos em um repositório git
if [ ! -d .git ]; then
    echo "❌ Erro: Este não é um repositório git!"
    exit 1
fi

# Fetch all branches
echo "📥 Fazendo fetch de todas as branches remotas..."
git fetch --all

# Lista de branches a serem mantidas
KEEP_BRANCHES=("main" "develop")

# Checkout para develop
echo "🔄 Fazendo checkout para develop..."
git checkout develop

# Pull latest develop
echo "📥 Atualizando develop..."
git pull origin develop || true

# Obter lista de todas as branches remotas (exceto main e develop)
echo "📋 Identificando branches para merge..."
BRANCHES_TO_MERGE=$(git branch -r | grep -v '\->' | grep -v 'origin/main' | grep -v 'origin/develop' | sed 's/origin\///' | tr -d ' ')

if [ -z "$BRANCHES_TO_MERGE" ]; then
    echo "✅ Nenhuma branch adicional encontrada para merge"
else
    echo "🔍 Branches encontradas para merge:"
    echo "$BRANCHES_TO_MERGE"
    echo ""
    
    # Merge each branch into develop
    for branch in $BRANCHES_TO_MERGE; do
        echo "🔀 Mergeando branch: $branch"
        
        # Tentar merge
        if git merge "origin/$branch" --no-edit -m "Merge branch '$branch' into develop"; then
            echo "✅ Branch $branch mergeada com sucesso"
        else
            echo "⚠️  Conflito ao mergear $branch - resolvendo automaticamente usando theirs"
            git merge --abort || true
            git merge "origin/$branch" -X theirs --no-edit -m "Merge branch '$branch' into develop"
        fi
        echo ""
    done
fi

# Push develop
echo "📤 Fazendo push de develop..."
git push origin develop

# Delete remote branches (exceto main e develop)
echo "🗑️  Deletando branches remotas..."
for branch in $BRANCHES_TO_MERGE; do
    echo "🗑️  Deletando branch remota: $branch"
    git push origin --delete "$branch" || echo "⚠️  Falha ao deletar $branch (pode já estar deletada)"
done

# Cleanup local branches
echo "🧹 Limpando branches locais..."
git branch | grep -v "main" | grep -v "develop" | grep -v "\*" | xargs -r git branch -D || true

echo ""
echo "✅ Limpeza concluída!"
echo "📊 Branches restantes:"
git branch -a | grep -E "(main|develop)"
