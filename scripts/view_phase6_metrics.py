#!/usr/bin/env python3
"""
Visão técnica mínima da Fase 6 (Qualidade, Latência e Custo por Tenant).
Uso: Inicie o app principal e execute: python scripts/view_phase6_metrics.py
Lê as métricas do runtime principal (/metrics) e o registro local de auditoria
para consolidar um painel operacional no terminal.
"""

import urllib.request
import urllib.error
import re
from pathlib import Path
import json

def fetch_metrics(url="http://localhost:8000/metrics"):
    try:
        req = urllib.request.Request(url, headers={'Accept': 'text/plain'})
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.read().decode("utf-8")
    except urllib.error.URLError as e:
        return None

def parse_metrics(text):
    # Dicionário de list de labels para valores
    parsed = {}
    for line in text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # chatpref_pipeline_fallback_total{tenant_id="prefeitura-demo"} 1.0
        match = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{([^}]*)\})?\s+(.+)$', line)
        if match:
            name = match.group(1)
            labels_str = match.group(2)
            value = float(match.group(3))

            labels = {}
            if labels_str:
                for kv in labels_str.split(','):
                    kv = kv.strip()
                    if '=' in kv:
                        k, v = kv.split('=', 1)
                        labels[k] = v.strip('"')
            if name not in parsed:
                parsed[name] = []
            parsed[name].append((labels, value))
    return parsed

def build_dashboard():
    print("=" * 60)
    print(" PAINEL OPERACIONAL MÍNIMO - FASE 6")
    print("=" * 60)

    text = fetch_metrics()
    if not text:
        print("\n[!] Runtime não acessível em http://localhost:8000/metrics.")
        print("[!] Inicie o runtime usando: make run ou python -m uvicorn app.main:app")
        print("=" * 60)
        return

    metrics = parse_metrics(text)

    # 1. Qual tenant está caindo em fallback?
    print("\n1. FALLBACKS POR TENANT")
    fallbacks = metrics.get("chatpref_pipeline_fallback_total", [])
    has_fallback = False
    for labels, value in fallbacks:
        if value > 0:
            print(f"   - {labels.get('tenant_id', 'unknown')}: {value} ocorrência(s)")
            has_fallback = True
    if not has_fallback:
        print("   Nenhum fallback registrado no momento.")

    # 2. Há retrieval vazio?
    print("\n2. RETRIEVAL VAZIO POR TENANT")
    empty_retrievals = metrics.get("chatpref_pipeline_retrieval_empty_total", [])
    has_empty = False
    for labels, value in empty_retrievals:
        if value > 0:
            print(f"   - {labels.get('tenant_id', 'unknown')}: {value} ocorrência(s)")
            has_empty = True
    if not has_empty:
        print("   Nenhum retrieval vazio registrado no momento.")

    # 3. Qual estágio parece mais lento? (Média baseada em _sum / _count)
    print("\n3. LATÊNCIA POR ESTÁGIO (Média Histórica)")
    lat_sum = metrics.get("chatpref_pipeline_stage_latency_seconds_sum", [])
    lat_count = metrics.get("chatpref_pipeline_stage_latency_seconds_count", [])

    # Agregar sum e count por tenant e stage
    stage_stats = {} # (tenant, stage) -> {'sum': x, 'count': y}
    for labels, value in lat_sum:
        k = (labels.get("tenant_id", "none"), labels.get("stage_name", "unknown"))
        if k not in stage_stats: stage_stats[k] = {"sum": 0, "count": 0}
        stage_stats[k]["sum"] += value

    for labels, value in lat_count:
        k = (labels.get("tenant_id", "none"), labels.get("stage_name", "unknown"))
        if k not in stage_stats: stage_stats[k] = {"sum": 0, "count": 0}
        stage_stats[k]["count"] += value

    has_latency = False
    sorted_stages = []
    for (tenant, stage), st in stage_stats.items():
        if st["count"] > 0:
            avg = st["sum"] / st["count"]
            sorted_stages.append((tenant, stage, avg, st["count"]))

    sorted_stages.sort(key=lambda x: x[2], reverse=True) # Mais lento primeiro

    for tenant, stage, avg, count in sorted_stages:
        print(f"   - [{tenant}] {stage}: {avg:.4f}s (base {int(count)} execuções)")
        has_latency = True

    if not has_latency:
        print("   Sem dados de latência registrados.")

    # 4. Existe custo estimado visível?
    print("\n4. CUSTO ESTIMADO ACUMULADO")
    costs = metrics.get("chatpref_pipeline_estimated_cost_usd_total", [])
    total_cost = 0.0
    for labels, value in costs:
        cost = float(value)
        if cost > 0:
            tenant = labels.get("tenant_id", "unknown")
            provider = labels.get("llm_provider", "unknown")
            model = labels.get("llm_model", "unknown")
            print(f"   - [{tenant}] via {provider}/{model}: U$ {cost:.6f}")
            total_cost += cost

    if total_cost == 0.0:
        print("   Nenhum custo monetário acumulado (uso de mocks ou runtime limpo).")
    else:
        print(f"   * TOTAL GLOBAL: U$ {total_cost:.6f}")

    # Policy Blocks
    print("\n5. BLOQUEIOS DE POLICY")
    blocks = metrics.get("chatpref_pipeline_policy_block_total", [])
    has_blocks = False
    for labels, value in blocks:
        if value > 0:
            print(f"   - {labels.get('tenant_id', 'unknown')}: {value} bloqueio(s)")
            has_blocks = True
    if not has_blocks:
        print("   Nenhum bloqueio de policy registrado.")

    # 6. Há contexto experimental correlacionável? (Auditoria local)
    print("\n6. CORRELAÇÃO OPERACIONAL x EXPERIMENTAL (Últimos Audits)")
    data_dir = Path("data/runtime/audit")
    if not data_dir.exists():
        print("   Diretório de auditoria não encontrado.")
    else:
        found_correlation = False
        correlations = []
        for p in data_dir.rglob("*.jsonl"):
            try:
                with p.open("r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip(): continue
                        try:
                            record = json.loads(line)
                            run_id = record.get("run_id") or record.get("request_id")
                            parent_run = record.get("parent_run_id")
                            strategy = record.get("strategy_name")

                            # if any explicit strategy or parent is registered, we have correlation
                            if parent_run or strategy:
                                correlations.append({
                                    "tenant": record.get("tenant_id", "unknown"),
                                    "session": record.get("session_id", "unknown"),
                                    "run_id": run_id,
                                    "parent_run_id": parent_run,
                                    "strategy": strategy
                                })
                        except:
                            pass
            except:
                pass

        # Limitar para os últimos 5 encontrados
        for c in correlations[-5:]:
            print(f"   - [{c['tenant']}] Session: {c['session']} | Run: {c['run_id']} | Pai: {c['parent_run_id']} | Strategy: {c['strategy']}")
            found_correlation = True

        if not found_correlation:
            print("   Nenhuma execução recente com contexto experimental explícito (run_id/parent_run_id/strategy).")

    print("\n" + "=" * 60)
    print(" NOTA: Valores obtidos instantaneamente via Prometheus (/metrics)")
    print(" limpos em memory cache ou na auditoria persistente local.")
    print("=" * 60)

if __name__ == "__main__":
    build_dashboard()
