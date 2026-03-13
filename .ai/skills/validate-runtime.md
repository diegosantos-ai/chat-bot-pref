# Skill: validate-runtime

## Quando usar
- Depois de mudancas em backend, configuracao, scripts operacionais ou Docker.

## Objetivo
- Confirmar que a base continua inicializando e que a mudanca nao quebrou o fluxo principal.

## Checklist
1. Verificar arquivos alterados e impacto em runtime.
2. Executar apenas os checks coerentes com a task:
   - `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - `pytest`
   - `docker compose config`
3. Registrar falhas com comando, ponto de quebra e escopo afetado.

## Evidencias minimas
- comando executado
- resultado observado
- risco residual
