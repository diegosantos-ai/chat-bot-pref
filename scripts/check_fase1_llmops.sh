#!/usr/bin/env bash
set -u

EXPECTED_BRANCH="setup/fundacao-llmops"
ROOT_DIR="${1:-$(pwd)}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
REPORT_DIR="${ROOT_DIR}/reports/fase1_llmops"
REPORT_FILE="${REPORT_DIR}/report_${TIMESTAMP}.md"
JSON_FILE="${REPORT_DIR}/report_${TIMESTAMP}.json"

mkdir -p "${REPORT_DIR}"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

TMP_TASKS="$(mktemp)"
TMP_LOG="$(mktemp)"

cleanup() {
  rm -f "$TMP_TASKS" "$TMP_LOG" /tmp/fase1_import_parse.txt 2>/dev/null || true
}
trap cleanup EXIT

print() { printf "%b\n" "$*" | tee -a "$TMP_LOG"; }
pass() { PASS_COUNT=$((PASS_COUNT+1)); print "[PASS] $*"; }
warn() { WARN_COUNT=$((WARN_COUNT+1)); print "[WARN] $*"; }
fail() { FAIL_COUNT=$((FAIL_COUNT+1)); print "[FAIL] $*"; }
info() { print "[INFO] $*"; }
section() { print "\n== $* =="; }

has_file() { [[ -f "$1" ]]; }
has_dir() { [[ -d "$1" ]]; }

contains_path() {
  local path="$1"
  local pattern="$2"
  grep -RIn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv --exclude-dir=__pycache__ -- "$pattern" "$path" >/dev/null 2>&1
}

count_contains() {
  local path="$1"
  local pattern="$2"
  grep -RIn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv --exclude-dir=__pycache__ -- "$pattern" "$path" 2>/dev/null | wc -l | tr -d ' '
}

contains_any() {
  local pattern="$1"
  shift
  local p
  for p in "$@"; do
    if [[ -e "$p" ]] && contains_path "$p" "$pattern"; then
      return 0
    fi
  done
  return 1
}

add_task_result() {
  local task="$1"
  local status="$2"
  local evidence="$3"
  printf '%s|%s|%s\n' "$task" "$status" "$evidence" >> "$TMP_TASKS"
}

current_branch="(desconhecida)"
python_cmd=""
pip_cmd=""

section "Contexto do repositório"
if [[ ! -d "$ROOT_DIR" ]]; then
  fail "Diretório não encontrado: $ROOT_DIR"
  exit 1
fi

cd "$ROOT_DIR" || exit 1
info "Repositório analisado: $ROOT_DIR"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  current_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "(desconhecida)")"
  info "Branch atual: ${current_branch}"
  if [[ "$current_branch" == "$EXPECTED_BRANCH" ]]; then
    pass "Branch esperada da fase encontrada (${EXPECTED_BRANCH})"
  else
    warn "Branch atual difere da esperada. Esperada='${EXPECTED_BRANCH}' | Atual='${current_branch}'"
  fi
else
  warn "Diretório não está em um repositório Git válido."
fi

if command -v python3 >/dev/null 2>&1; then
  python_cmd="python3"
elif command -v python >/dev/null 2>&1; then
  python_cmd="python"
else
  fail "Python não encontrado no PATH."
  exit 1
fi

if "$python_cmd" -m pip --version >/dev/null 2>&1; then
  pip_cmd="$python_cmd -m pip"
  info "Python detectado: $($python_cmd --version 2>&1)"
  info "Pip detectado: $($python_cmd -m pip --version 2>&1)"
else
  fail "pip não disponível no interpretador atual."
  exit 1
fi

section "Arquivos e documentação-base"
README_OK=0
DOCS_OK=0
REQ_OK=0
REQDEV_OK=0
APP_AUDIT_OK=0
APP_RAG_OK=0

if has_file "README.md"; then
  pass "README.md encontrado"
  README_OK=1
else
  fail "README.md ausente"
fi

required_docs=(
  "docs-LLMOps/README.md"
  "docs-LLMOps/CONTEXTO-LLMOps.md"
  "docs-LLMOps/ARQUITETURA-LLMOps.md"
)

missing_docs=0
for doc in "${required_docs[@]}"; do
  if has_file "$doc"; then
    pass "Doc encontrado: $doc"
  else
    fail "Doc ausente: $doc"
    missing_docs=$((missing_docs+1))
  fi
done

planning_doc_found=0
for candidate in \
  "docs-LLMOps/PLANEJAMENTO-LLMOPS.md" \
  "docs-LLMOps/PLANEJAMENTO_LLMOPS.md" \
  "docs-LLMOps/PLANEJAMENTO-LLMOps.md" \
  "docs-LLMOps/PLANEJAMENTO_LLMOps.md"
do
  if has_file "$candidate"; then
    pass "Doc encontrado: $candidate"
    planning_doc_found=1
    break
  fi
done

if [[ $planning_doc_found -eq 0 ]]; then
  fail "Doc de planejamento da fase não encontrado em nenhuma variante de nome esperada"
fi

[[ $missing_docs -eq 0 && $planning_doc_found -eq 1 ]] && DOCS_OK=1

if has_file "requirements.txt"; then
  lines=$(grep -Ev '^\s*#|^\s*$' requirements.txt | wc -l | tr -d ' ')
  if [[ "$lines" -gt 0 ]]; then
    pass "requirements.txt encontrado e não vazio (${lines} dependências declaradas)"
    REQ_OK=1
  else
    fail "requirements.txt existe, mas está vazio"
  fi
else
  fail "requirements.txt ausente"
fi

if has_file "requirements-dev.txt"; then
  lines=$(grep -Ev '^\s*#|^\s*$' requirements-dev.txt | wc -l | tr -d ' ')
  if [[ "$lines" -gt 0 ]]; then
    pass "requirements-dev.txt encontrado e não vazio (${lines} dependências declaradas)"
    REQDEV_OK=1
  else
    fail "requirements-dev.txt existe, mas está vazio"
  fi
else
  fail "requirements-dev.txt ausente"
fi

if has_dir "app/audit"; then
  pass "Diretório app/audit encontrado"
  APP_AUDIT_OK=1
else
  warn "Diretório app/audit não encontrado"
fi

if has_dir "app/rag"; then
  pass "Diretório app/rag encontrado"
  APP_RAG_OK=1
else
  warn "Diretório app/rag não encontrado"
fi

section "Inspeção documental da Fase 1"
MLFLOW_DOC=0
TENANT_DOC=0
AUDIT_X_EXPERIMENT_DOC=0
RUN_CONTRACT_DOC=0
VERSIONING_DOC=0
INSTRUMENT_DOC=0
TARGET_ARCH_DOC=0

search_scope=("README.md" "docs-LLMOps" "docs-fundacao-operacional")

if contains_any "MLflow" "${search_scope[@]}"; then
  pass "Menções a MLflow encontradas na documentação"
  MLFLOW_DOC=1
else
  warn "Não encontrei menções a MLflow na documentação"
fi

if contains_any "tenant_id" "${search_scope[@]}"; then
  pass "Menções a tenant_id encontradas na documentação"
  TENANT_DOC=1
else
  warn "Não encontrei menções a tenant_id na documentação"
fi

if contains_any "auditoria operacional" "${search_scope[@]}" && contains_any "tracking experimental" "${search_scope[@]}"; then
  pass "Separação entre auditoria operacional e tracking experimental aparece na documentação"
  AUDIT_X_EXPERIMENT_DOC=1
else
  warn "Separação auditoria x tracking experimental não apareceu de forma clara na busca textual"
fi

if contains_path "docs-LLMOps" "runs" && contains_path "docs-LLMOps" "params" && contains_path "docs-LLMOps" "metrics" && contains_path "docs-LLMOps" "artifacts"; then
  pass "Contrato mínimo de runs/params/metrics/artifacts aparece na documentação"
  RUN_CONTRACT_DOC=1
else
  warn "Não achei todas as menções de runs/params/metrics/artifacts na documentação"
fi

if contains_path "docs-LLMOps" "prompt" && contains_path "docs-LLMOps" "retriever" && contains_path "docs-LLMOps" "embedding"; then
  pass "Há sinais documentais de versionamento de prompt/retriever/embeddings"
  VERSIONING_DOC=1
else
  warn "Não achei todas as menções de versionamento de prompt/retriever/embeddings"
fi

if contains_path "docs-LLMOps" "app/audit" && contains_path "docs-LLMOps" "app/rag"; then
  pass "Documentação cita pontos de instrumentação em app/audit e app/rag"
  INSTRUMENT_DOC=1
else
  warn "Não achei menção explícita a app/audit e app/rag na documentação da fase"
fi

if contains_path "docs-LLMOps" "tenant-aware"; then
  pass "Arquitetura alvo tenant-aware aparece documentada"
  TARGET_ARCH_DOC=1
else
  warn "Não achei menção explícita a tenant-aware na arquitetura da fase"
fi

section "Inspeção do código e contratos ativos"
TENANT_CODE=0
REQUEST_CODE=0
MLFLOW_CODE=0
PROMPT_CODE=0
RETRIEVER_CODE=0
EMBEDDING_CODE=0

if has_dir "app"; then
  tcount=$(count_contains "app" "tenant_id")
  if [[ "$tcount" -gt 0 ]]; then
    pass "tenant_id encontrado no código (${tcount} ocorrências)"
    TENANT_CODE=1
  else
    warn "tenant_id não encontrado no código sob app/"
  fi

  rcount=$(count_contains "app" "request_id")
  if [[ "$rcount" -gt 0 ]]; then
    pass "request_id encontrado no código (${rcount} ocorrências)"
    REQUEST_CODE=1
  else
    warn "request_id não encontrado no código sob app/"
  fi

  mcount=$(count_contains "app" "mlflow")
  if [[ "$mcount" -gt 0 ]]; then
    pass "Referências a mlflow já aparecem no código (${mcount} ocorrências)"
    MLFLOW_CODE=1
  else
    warn "Ainda não encontrei referências a mlflow no código"
  fi

  pcount=$(count_contains "app" "prompt")
  if [[ "$pcount" -gt 0 ]]; then
    pass "Sinais de prompt no código (${pcount} ocorrências)"
    PROMPT_CODE=1
  else
    warn "Sinais de prompt não encontrados em app/"
  fi

  retrcount=$(count_contains "app" "retriev")
  if [[ "$retrcount" -gt 0 ]]; then
    pass "Sinais de retriever/retrieval no código (${retrcount} ocorrências)"
    RETRIEVER_CODE=1
  else
    warn "Sinais de retrieval não encontrados em app/"
  fi

  embcount=$(count_contains "app" "embedding")
  if [[ "$embcount" -gt 0 ]]; then
    pass "Sinais de embeddings no código (${embcount} ocorrências)"
    EMBEDDING_CODE=1
  else
    warn "Sinais de embeddings não encontrados em app/"
  fi
else
  fail "Diretório app/ ausente"
fi

section "Validação do ambiente Python atual"
IMPORT_REPORT="$($python_cmd - <<'PY'
import importlib
import json

modules = {
    'fastapi': 'base',
    'uvicorn': 'base',
    'pydantic': 'base',
    'sqlalchemy': 'base',
    'chromadb': 'base',
    'opentelemetry': 'base',
    'mlflow': 'dev',
    'pytest': 'dev',
    'httpx': 'dev',
    'ragas': 'dev',
    'pandas': 'dev',
}

out = {}
for name, group in modules.items():
    try:
        importlib.import_module(name)
        out[name] = {'ok': True, 'group': group}
    except Exception as e:
        out[name] = {'ok': False, 'group': group, 'error': str(e)}

print(json.dumps(out, ensure_ascii=False))
PY
)"

BASE_IMPORT_OK=0
DEV_IMPORT_OK=0

python3 - <<'PY' "$IMPORT_REPORT" > /tmp/fase1_import_parse.txt
import json, sys
report = json.loads(sys.argv[1])
base = [k for k,v in report.items() if v['group']=='base']
dev = [k for k,v in report.items() if v['group']=='dev']
print(sum(1 for k in base if report[k]['ok']))
print(len(base))
print(sum(1 for k in dev if report[k]['ok']))
print(len(dev))
for k,v in report.items():
    if not v['ok']:
        print(f"MISS|{k}|{v['group']}|{v.get('error','')}")
PY

mapfile -t import_stats < /tmp/fase1_import_parse.txt

base_ok="${import_stats[0]:-0}"
base_total="${import_stats[1]:-0}"
dev_ok="${import_stats[2]:-0}"
dev_total="${import_stats[3]:-0}"

if [[ "$base_ok" -ge 4 ]]; then
  pass "Imports do ambiente base razoavelmente íntegros (${base_ok}/${base_total})"
  BASE_IMPORT_OK=1
else
  fail "Imports do ambiente base insuficientes (${base_ok}/${base_total})"
fi

if [[ "$dev_ok" -ge 3 ]]; then
  pass "Imports do ambiente de desenvolvimento parcialmente/totalmente disponíveis (${dev_ok}/${dev_total})"
  DEV_IMPORT_OK=1
else
  warn "Imports do ambiente dev ainda fracos (${dev_ok}/${dev_total})"
fi

while IFS='|' read -r marker mod grp err; do
  [[ "$marker" == "MISS" ]] || continue
  warn "Import ausente/falhou: módulo='${mod}' grupo='${grp}' erro='${err}'"
done < /tmp/fase1_import_parse.txt

section "Contratos mínimos da Fase 1"
TENANT_SEGREGATION_OK=0
RAG_VERSIONING_OK=0
INSTRUMENTATION_MAP_OK=0

PHASE1_CONTRACT_REPORT="$($python_cmd - <<'PY'
import json

from app.audit import PHASE1_AUDIT_INSTRUMENTATION_POINTS, PHASE1_TENANT_SEGREGATION
from app.rag import PHASE1_RAG_ARTIFACT_VERSIONS, PHASE1_RAG_INSTRUMENTATION_POINTS

payload = {
    "tenant_segregation_ok": (
        PHASE1_TENANT_SEGREGATION.tenant_field == "tenant_id"
        and PHASE1_TENANT_SEGREGATION.request_field == "request_id"
        and len(PHASE1_TENANT_SEGREGATION.required_run_fields) >= 2
    ),
    "rag_versioning_ok": (
        bool(PHASE1_RAG_ARTIFACT_VERSIONS.retriever_version)
        and bool(PHASE1_RAG_ARTIFACT_VERSIONS.embedding_version)
    ),
    "instrumentation_map_ok": (
        len(PHASE1_AUDIT_INSTRUMENTATION_POINTS) >= 1
        and len(PHASE1_RAG_INSTRUMENTATION_POINTS) >= 1
    ),
    "audit_points": len(PHASE1_AUDIT_INSTRUMENTATION_POINTS),
    "rag_points": len(PHASE1_RAG_INSTRUMENTATION_POINTS),
    "retriever_version": PHASE1_RAG_ARTIFACT_VERSIONS.retriever_version,
    "embedding_version": PHASE1_RAG_ARTIFACT_VERSIONS.embedding_version,
}
print(json.dumps(payload, ensure_ascii=False))
PY
)"

CONTRACT_STATS="$($python_cmd - <<'PY' "$PHASE1_CONTRACT_REPORT"
import json, sys

payload = json.loads(sys.argv[1])
print(int(payload["tenant_segregation_ok"]))
print(int(payload["rag_versioning_ok"]))
print(int(payload["instrumentation_map_ok"]))
print(payload["audit_points"])
print(payload["rag_points"])
print(payload["retriever_version"])
print(payload["embedding_version"])
PY
)"

mapfile -t contract_stats < <(printf "%s\n" "$CONTRACT_STATS")

tenant_seg_ok="${contract_stats[0]:-0}"
rag_version_ok="${contract_stats[1]:-0}"
instrumentation_ok="${contract_stats[2]:-0}"
audit_points="${contract_stats[3]:-0}"
rag_points="${contract_stats[4]:-0}"
retriever_version="${contract_stats[5]:-}"
embedding_version="${contract_stats[6]:-}"

if [[ "$tenant_seg_ok" -eq 1 ]]; then
  pass "Segregação experimental explícita por tenant_id/request_id disponível em app/audit"
  TENANT_SEGREGATION_OK=1
else
  warn "Contrato explícito de segregação experimental por tenant_id/request_id não encontrado"
fi

if [[ "$rag_version_ok" -eq 1 ]]; then
  pass "Versionamento inicial de retrieval/embeddings disponível (${retriever_version} | ${embedding_version})"
  RAG_VERSIONING_OK=1
else
  warn "Versionamento inicial de retrieval/embeddings não ficou explícito"
fi

if [[ "$instrumentation_ok" -eq 1 ]]; then
  pass "Mapeamento mínimo de instrumentação disponível (audit=${audit_points} | rag=${rag_points})"
  INSTRUMENTATION_MAP_OK=1
else
  warn "Mapeamento mínimo de instrumentação ainda incompleto"
fi

section "Checagens de requirements"
REQDEV_HAS_MLFLOW=0
SMOKE_OK=0

if has_file "requirements-dev.txt"; then
  if grep -Eiq '^mlflow([<>=~!]|$)' requirements-dev.txt; then
    pass "mlflow declarado em requirements-dev.txt"
    REQDEV_HAS_MLFLOW=1
  else
    warn "mlflow não encontrado em requirements-dev.txt"
  fi
fi

section "Evidência do smoke oficial"
if has_file "artifacts/llmops/smoke_fase1/smoke_report.json"; then
  SMOKE_STATS="$($python_cmd - <<'PY'
import json
from pathlib import Path

path = Path("artifacts/llmops/smoke_fase1/smoke_report.json")
data = json.loads(path.read_text(encoding="utf-8"))
summary = data.get("summary", {})
mlflow_ok = any(
    row.get("name") == "mlflow" and row.get("status") == "PASS"
    for row in data.get("results", [])
)
print(int(summary.get("pass", 0)))
print(int(summary.get("fail", 0)))
print(int(mlflow_ok))
PY
)"

  mapfile -t smoke_stats < <(printf "%s\n" "$SMOKE_STATS")
  smoke_pass="${smoke_stats[0]:-0}"
  smoke_fail="${smoke_stats[1]:-0}"
  smoke_mlflow="${smoke_stats[2]:-0}"

  if [[ "$smoke_fail" -eq 0 && "$smoke_mlflow" -eq 1 ]]; then
    pass "Smoke oficial da Fase 1 disponível e sem falhas (${smoke_pass} checks aprovadas)"
    SMOKE_OK=1
  else
    warn "Smoke oficial encontrado, mas com falhas ou sem evidência de MLflow (pass=${smoke_pass} fail=${smoke_fail} mlflow=${smoke_mlflow})"
  fi
else
  warn "Smoke oficial da Fase 1 ainda não gerou artifacts/llmops/smoke_fase1/smoke_report.json"
fi

section "Avaliação heurística das tasks da Fase 1"

[[ $MLFLOW_DOC -eq 1 ]] && add_task_result "CPPX-F1-T1" "OK" "Estratégia MLflow aparece na documentação." || add_task_result "CPPX-F1-T1" "PENDENTE" "Não encontrei estratégia MLflow clara nos docs."

if [[ $TENANT_DOC -eq 1 && $TENANT_SEGREGATION_OK -eq 1 && $SMOKE_OK -eq 1 ]]; then
  add_task_result "CPPX-F1-T2" "OK" "Segregação experimental por tenant_id/request_id está explícita em contrato e validada no smoke."
elif [[ $TENANT_DOC -eq 1 && ( $MLFLOW_DOC -eq 1 || $MLFLOW_CODE -eq 1 ) ]]; then
  add_task_result "CPPX-F1-T2" "PARCIAL" "Há tenant_id e sinais de tracking; isolamento experimental ainda exige revisão humana."
else
  add_task_result "CPPX-F1-T2" "PENDENTE" "Faltam sinais suficientes de segregação experimental por tenant_id."
fi

[[ $AUDIT_X_EXPERIMENT_DOC -eq 1 ]] && add_task_result "CPPX-F1-T3" "OK" "Separação auditoria operacional x tracking experimental apareceu nos docs." || add_task_result "CPPX-F1-T3" "PENDENTE" "Separação auditoria x experimento não ficou clara."

[[ $RUN_CONTRACT_DOC -eq 1 ]] && add_task_result "CPPX-F1-T4" "OK" "Contrato de run/params/metrics/artifacts aparece nos docs." || add_task_result "CPPX-F1-T4" "PENDENTE" "Contrato mínimo de tracking não apareceu claramente."

if [[ $VERSIONING_DOC -eq 1 && $RAG_VERSIONING_OK -eq 1 ]]; then
  add_task_result "CPPX-F1-T5" "OK" "Prompt, retriever e embeddings possuem versionamento mínimo explícito e importável."
elif [[ $VERSIONING_DOC -eq 1 || ( $PROMPT_CODE -eq 1 && $RETRIEVER_CODE -eq 1 ) ]]; then
  add_task_result "CPPX-F1-T5" "PARCIAL" "Há sinais de versionamento/artefatos, mas o contrato formal ainda pede revisão."
else
  add_task_result "CPPX-F1-T5" "PENDENTE" "Não encontrei evidências suficientes de versionamento inicial."
fi

if [[ $INSTRUMENT_DOC -eq 1 && $INSTRUMENTATION_MAP_OK -eq 1 && $SMOKE_OK -eq 1 ]]; then
  add_task_result "CPPX-F1-T6" "OK" "Pontos mínimos de instrumentação em app/audit e app/rag estão formalizados e refletem o smoke."
elif [[ $INSTRUMENT_DOC -eq 1 || ( $APP_AUDIT_OK -eq 1 && $APP_RAG_OK -eq 1 ) ]]; then
  add_task_result "CPPX-F1-T6" "PARCIAL" "Há evidência estrutural para instrumentação; falta fechar mapeamento formal."
else
  add_task_result "CPPX-F1-T6" "PENDENTE" "Não encontrei evidência suficiente dos pontos de instrumentação."
fi

[[ $TARGET_ARCH_DOC -eq 1 ]] && add_task_result "CPPX-F1-T7" "OK" "Arquitetura alvo tenant-aware aparece documentada." || add_task_result "CPPX-F1-T7" "PENDENTE" "Arquitetura alvo tenant-aware não apareceu claramente."
[[ $REQ_OK -eq 1 ]] && add_task_result "CPPX-F1-T8" "OK" "requirements.txt existe e não está vazio." || add_task_result "CPPX-F1-T8" "PENDENTE" "requirements.txt ausente ou inválido."
[[ $REQDEV_OK -eq 1 ]] && add_task_result "CPPX-F1-T9" "OK" "requirements-dev.txt existe e não está vazio." || add_task_result "CPPX-F1-T9" "PENDENTE" "requirements-dev.txt ausente ou inválido."

if [[ $BASE_IMPORT_OK -eq 1 && $SMOKE_OK -eq 1 ]]; then
  add_task_result "CPPX-F1-T10" "OK" "Ambiente base validado no interpretador atual e confirmado pelo smoke oficial."
elif [[ $BASE_IMPORT_OK -eq 1 ]]; then
  add_task_result "CPPX-F1-T10" "PARCIAL" "Ambiente base parece instalado no interpretador atual."
else
  add_task_result "CPPX-F1-T10" "PENDENTE" "Ambiente base não parece instalado corretamente."
fi

if [[ $DEV_IMPORT_OK -eq 1 && $REQDEV_HAS_MLFLOW -eq 1 && $SMOKE_OK -eq 1 ]]; then
  add_task_result "CPPX-F1-T11" "OK" "Ambiente dev validado com MLflow e smoke oficial executado no venv."
elif [[ $DEV_IMPORT_OK -eq 1 && $REQDEV_HAS_MLFLOW -eq 1 ]]; then
  add_task_result "CPPX-F1-T11" "PARCIAL" "Ambiente dev parece ao menos parcialmente instalado."
else
  add_task_result "CPPX-F1-T11" "PENDENTE" "Ambiente dev não parece instalado de forma consistente."
fi

if [[ $SMOKE_OK -eq 1 ]]; then
  add_task_result "CPPX-F1-T12" "OK" "Smoke oficial da Fase 1 executado com sucesso no venv e compatibilidade mínima confirmada."
elif [[ $BASE_IMPORT_OK -eq 1 || $DEV_IMPORT_OK -eq 1 ]]; then
  add_task_result "CPPX-F1-T12" "PARCIAL" "Há sinais de compatibilidade/imports; ainda precisa smoke test do venv oficial."
else
  add_task_result "CPPX-F1-T12" "PENDENTE" "Compatibilidade mínima ainda não passou na checagem heurística."
fi

section "Gerando relatório"

{
  echo "# Relatório de Verificação — Fase 1 LLMOps"
  echo
  echo "- Data: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "- Repositório: ${ROOT_DIR}"
  echo "- Branch atual: ${current_branch}"
  echo
  echo "## Saída do script"
  echo
  sed 's/^/- /' "$TMP_LOG"
  echo
  echo "## Resumo"
  echo
  echo "- PASS: ${PASS_COUNT}"
  echo "- WARN: ${WARN_COUNT}"
  echo "- FAIL: ${FAIL_COUNT}"
  echo
  echo "## Status por task"
  echo
  echo "| Task | Status | Evidência |"
  echo "|---|---|---|"
  while IFS='|' read -r task status evidence; do
    echo "| ${task} | ${status} | ${evidence} |"
  done < "$TMP_TASKS"
} > "$REPORT_FILE"

python3 - <<'PY' "$TMP_TASKS" "$JSON_FILE" "$ROOT_DIR" "$current_branch" "$PASS_COUNT" "$WARN_COUNT" "$FAIL_COUNT"
import json, sys, pathlib
src, dst, root, branch, p, w, f = sys.argv[1:8]
rows = []
for line in pathlib.Path(src).read_text(encoding='utf-8').splitlines():
    task, status, evidence = line.split('|', 2)
    rows.append({"task": task, "status": status, "evidence": evidence})
payload = {
    "repo_root": root,
    "branch": branch,
    "summary": {"pass": int(p), "warn": int(w), "fail": int(f)},
    "tasks": rows,
}
pathlib.Path(dst).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
PY

pass "Relatório Markdown gerado em: ${REPORT_FILE}"
pass "Relatório JSON gerado em: ${JSON_FILE}"

section "Resumo final"
print "PASS=${PASS_COUNT} | WARN=${WARN_COUNT} | FAIL=${FAIL_COUNT}"
print "Abra o relatório em: ${REPORT_FILE}"
print "JSON em: ${JSON_FILE}"
