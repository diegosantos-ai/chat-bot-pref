# Skill: validate-tenant-flow

## Quando usar
- Em tarefas que mexem com `tenant_id`, webhook, chat direto, auditoria, RAG ou persistencia.

## Objetivo
- Verificar se o tenant entra, propaga e e consumido sem fallback silencioso.

## Checklist
1. Identificar onde o tenant entra no fluxo.
2. Verificar propagacao em `tenant_context`, `tenant_resolver`, endpoints e camadas afetadas.
3. Confirmar comportamento quando `tenant_id` esta ausente.
4. Registrar se o erro e controlado ou se ainda existe dependencia implicita.

## Evidencias minimas
- ponto de entrada do tenant
- ponto de consumo do tenant
- comportamento na ausencia de tenant
