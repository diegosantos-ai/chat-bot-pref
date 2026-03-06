**Manual de Uso — Workflow: Add Issues to Project**

Este documento descreve, na prática, como usar o workflow `add_issues_to_project.yml` para vincular issues em lote ao GitHub Project V2 do projeto.

**Resumo rápido**
- O workflow lê um CSV (`artifacts/issues_mapping.csv` por padrão) e executa o script `scripts/action_add_issues.py` para adicionar issues ao Project V2.
- É acionado manualmente (workflow_dispatch) e requer o secret `PROJECT_TOKEN` com scope `project` (e `repo` se necessário).

**Benefícios no dia a dia**
- Automação: evita adicionar issues manualmente ao board.
- Consistência: o CSV é a fonte única (Start/Due/labels/milestone).
- Rastreabilidade: logs de execução ficam no Actions.
- Escalabilidade: processa muitos itens de uma vez.
- Redução de erros: mapeamento via arquivo evita cliques incorretos.

**Quando usar — momentos práticos do dia / do projeto**
- Planejamento matinal (Daily / Kickoff): atualizar o CSV com prioridades e datas antes da reunião.
- Antes do Sprint Planning: sincronizar backlog novo com o Project para que o time veja itens oficiais.
- Durante preparação de release ou entrega: rodar para garantir que todas as issues de release tenham Start/Due e status no board.
- Depois de sessões de grooming/triagem: quando muitos tickets são criados/atualizados em lote.
- Handoff para QA / Ops: certificar que as issues estão ligadas ao board com informações de deploy/monitoring.
- Dias de limpeza/organização (chore day): usar para aplicar ajustes massivos (datas, labels) de forma controlada.

**Passo a passo (uso prático)**

1. Atualizar o CSV fonte
   - Abra `artifacts/issues_mapping.csv` e confirme que contém as colunas mínimas: `number,url,title,start,due,labels,milestone`.
   - Edite apenas as linhas que precisam ser alteradas. Para testes, mantenha 2–3 linhas.

2. Commit & push
   - Commit das mudanças no CSV e no código (se aplicável). Exemplo:

```powershell
git add artifacts/issues_mapping.csv
git commit -m "sync: atualizar artifacts/issues_mapping.csv para vinculação ao Project"
git push origin main
```

3. Verificar `PROJECT_TOKEN`
   - Assegure que o repositório tem `Settings > Secrets > Actions > PROJECT_TOKEN` configurado.
   - O token deve ter escopo `project` (e `repo` se o script acessar issues privadas).

4. Disparar o workflow
   - Pela CLI:

```bash
gh workflow run add_issues_to_project.yml -f project_id="PVT_kwHODI7RY84BM1k1" -f csv_path="artifacts/issues_mapping.csv"
```

   - Ou pela UI: Actions → selecionar `Add Issues to Project` → Run workflow → preencher `project_id` e `csv_path` → Run.

5. Monitorar execução
   - Listar runs:

```bash
gh run list --workflow="add_issues_to_project.yml"
```

   - Ver logs:

```bash
gh run view <run-id> --log
```

6. Verificar o Project
   - No GitHub Projects, confirme se os items aparecem vinculados (ícone de issue/link) e se campos `Status`, `Start`, `Due` foram ajustados.

7. Limpeza final
   - Se o Project ficou com draft items duplicados, remova-os manualmente.

**Boas práticas operacionais**
- Teste com pequenos lotes antes de rodar em todo o CSV.
- Manter o CSV em um único local do repositório para evitar divergência.
- Registrar quem disparou o workflow (logs do Actions já fornecem isso).
- Rodar o workflow como parte da rotina de release/entrega.
- Garantir que `scripts/action_add_issues.py` trate erros e faça logs claros (linha/issue que falhou).

**Checklist rápida antes de rodar**
- [ ] CSV atualizado e commitado
- [ ] `PROJECT_TOKEN` presente e válido
- [ ] Projeto (Project V2) e `project_id` corretos
- [ ] Changes pushadas para branch padrão

**Soluções para falhas comuns**
- Erro de permissão/escopo do token: recreie o PAT com `project` scope e atualize o secret.
- CSV não encontrado: confira `csv_path` no dispatch ou o caminho no repositório.
- Mutação GraphQL indisponível: revisar logs; se for limitação da API, o script pode precisar de fallback para criação manual via REST ou instrução para adicionar itens manualmente.

**Exemplo mínimo de uso (fluxo rápido)**
1. Editar 3 linhas de `artifacts/issues_mapping.csv` com `start`/`due`.
2. git commit & push.
3. `gh workflow run add_issues_to_project.yml -f project_id="PVT_kwHODI7RY84BM1k1"`
4. `gh run view --log <run-id>` para confirmar sucesso.

---
Arquivo criado automaticamente pelo assistente com instruções operacionais.
