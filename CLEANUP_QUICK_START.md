# Guia Rápido de Execução - Limpeza de Branches

## 🎯 Objetivo
Limpar o repositório mantendo apenas as branches `main` e `develop`, mergeando todo o código das outras branches na `develop` antes de deletá-las.

## ⚡ Execução Rápida (Recomendado)

### Via GitHub Actions (Mais Fácil)

1. Acesse: https://github.com/diegosantos-ai/pilot-atendimento/actions/workflows/cleanup_branches.yml
2. Clique no botão **"Run workflow"** (à direita)
3. No campo que aparecer, digite: `CONFIRM`
4. Clique em **"Run workflow"** novamente
5. Aguarde a execução (acompanhe o log)

**✅ Pronto!** O workflow vai automaticamente:
- Fazer merge de todas as 9 branches secundárias na `develop`
- Deletar todas as branches secundárias
- Deixar apenas `main` e `develop`

## 📋 Branches que serão mergeadas e deletadas

1. `copilot/merge-and-delete-secondary-branches`
2. `copilot/sub-pr-44-again`
3. `copilot/sub-pr-44`
4. `diegosantos-ai-patch-1`
5. `diegosantos-ai-patch-2`
6. `master` (duplicata da main)
7. `metadeveloperconfig`
8. `organizacao`
9. `perf-rag`

## 🔄 Alternativas de Execução

### Opção 2: Script Local (se tiver acesso git)

```bash
cd pilot-atendimento
chmod +x scripts/cleanup_branches.py
python scripts/cleanup_branches.py
```

### Opção 3: Comandos Git Manuais

```bash
# Detalhes completos em: scripts/README_BRANCH_CLEANUP.md
git fetch --all
git checkout develop
# ... (ver documentação completa)
```

## ⚠️ Notas Importantes

- **Não há risco de perda de código**: Todo código será mergeado na `develop` antes da deleção
- **Reversível**: Branches deletadas podem ser recuperadas do histórico Git por ~30 dias
- **Tempo estimado**: 2-3 minutos
- **Sem interrupção**: Não afeta o funcionamento atual do sistema

## ✅ Verificação Final

Após a execução, execute:

```bash
git branch -r
```

Deve mostrar apenas:
```
origin/develop
origin/main
```

## 🆘 Suporte

Em caso de problemas:
1. Verifique os logs do GitHub Actions
2. Consulte a documentação completa em `scripts/README_BRANCH_CLEANUP.md`
3. Em caso de conflitos, o merge usará automaticamente a estratégia "theirs" (mantém código das branches sendo mergeadas)
