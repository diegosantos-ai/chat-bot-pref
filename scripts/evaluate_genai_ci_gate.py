import sys
import json
from pathlib import Path

def evaluate_gate(reports_dir: Path) -> int:
    """Regras estritas de pass/fail para PRs na Fase 7"""
    run_files = list(reports_dir.glob("*_run.json"))
    if not run_files:
        print("FAIL: Nenhum arquivo _run.json encontrado no tracking-dir. O RAG quebrou fatalmente e não ejetou sumarização.")
        return 1

    report_file = run_files[0]
    try:
        report = json.loads(report_file.read_text())
    except Exception as e:
        print(f"FAIL: Parse do relatório RAG falhou, JSON corrompido. {e}")
        return 1

    cases_total = report.get("tracking", {}).get("metrics", {}).get("cases_total", report.get("cases_total", 0))
    cases_evaluated = report.get("tracking", {}).get("metrics", {}).get("cases_evaluated", report.get("cases_evaluated", 0))

    if cases_total == 0 or cases_evaluated == 0:
        print("FAIL: O runner nao executou sequer o baseline estrito vazio (cases_evaluated=0).")
        return 1

    if cases_evaluated < cases_total:
         print(f"FAIL: Foram dropados casos por exception interna durante CI. Evaluated: {cases_evaluated} / Expected: {cases_total}")
         return 1

    print("✅ PASS: Pipeline textual e engrenagem JSON do Runtime mantiveram viabilidade contra Mock!")
    print("ℹ AVISO: Validação em nota descritiva/qualidade como `faithfulness_mean` desativada momentâneamente via `--mock` provider no CI de PR.")

    return 0

if __name__ == "__main__":
    workdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tmp/mlflow_ci_run/run_reports")
    sys.exit(evaluate_gate(workdir))
