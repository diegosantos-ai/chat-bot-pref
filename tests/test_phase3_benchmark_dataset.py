from pathlib import Path
from collections import Counter

import pytest

from app.llmops.benchmark_dataset import (
    BENCHMARK_DATASETS_DIR,
    PHASE3_INITIAL_BASELINE_MANIFEST,
    BenchmarkCase,
    BenchmarkCoverageType,
    BenchmarkDatasetSummary,
    BenchmarkPriorityTier,
    BenchmarkScenarioType,
    SCENARIO_ANSWER_REFERENCE_TYPES,
    SCENARIO_CONTEXT_REFERENCE_TYPES,
    build_benchmark_dataset_summary,
    discover_benchmark_manifests,
    format_benchmark_dataset_summary,
    load_benchmark_dataset,
    load_phase3_initial_baseline,
)


def test_phase3_benchmark_manifests_are_discoverable() -> None:
    manifests = discover_benchmark_manifests()

    assert manifests
    assert all(path.is_file() for path in manifests)
    assert BENCHMARK_DATASETS_DIR.is_dir()


def test_phase3_initial_baseline_manifest_is_explicit_and_loadable() -> None:
    dataset = load_phase3_initial_baseline()

    assert PHASE3_INITIAL_BASELINE_MANIFEST.is_file()
    assert dataset.manifest.manifest_path == PHASE3_INITIAL_BASELINE_MANIFEST
    assert dataset.manifest.tenant_id == "prefeitura-vila-serena"
    assert dataset.manifest.dataset_version == "benchmark_v1"


def test_phase3_benchmark_dataset_has_required_structure_and_tenant_isolation() -> None:
    manifest_path = (
        BENCHMARK_DATASETS_DIR
        / "tenants"
        / "prefeitura-vila-serena"
        / "benchmark_v1"
        / "dataset_manifest.json"
    )

    dataset = load_benchmark_dataset(manifest_path)
    scenario_types = {case.scenario_type for case in dataset.cases}
    case_ids = {case.case_id for case in dataset.cases}
    priorities = Counter(case.priority_tier for case in dataset.cases)
    coverage_types = Counter(case.coverage_type for case in dataset.cases)

    assert dataset.manifest.dataset_version == "benchmark_v1"
    assert dataset.manifest.tenant_id == "prefeitura-vila-serena"
    assert dataset.manifest.selection_hypotheses
    assert len(dataset.cases) == 17
    assert len(case_ids) == len(dataset.cases)
    assert scenario_types == {
        BenchmarkScenarioType.ATENDIMENTO_NORMAL,
        BenchmarkScenarioType.PERGUNTA_AMBIGUA,
        BenchmarkScenarioType.FORA_DE_ESCOPO,
        BenchmarkScenarioType.BAIXA_CONFIANCA,
        BenchmarkScenarioType.RISCO_POLICY,
    }
    assert all(case.tenant_id == dataset.manifest.tenant_id for case in dataset.cases)
    assert all(case.expected_answer_reference.summary for case in dataset.cases)
    assert all(case.expected_answer_reference.must_include for case in dataset.cases)
    assert all(case.expected_answer_reference.must_not_include for case in dataset.cases)
    assert all(case.expected_context_reference.document_hints for case in dataset.cases)
    assert all(case.expected_context_reference.notes for case in dataset.cases)
    assert priorities == {
        BenchmarkPriorityTier.P1: 10,
        BenchmarkPriorityTier.P2: 4,
        BenchmarkPriorityTier.P3: 3,
    }
    assert coverage_types == {
        BenchmarkCoverageType.TENANT_DEMONSTRATIVO: 11,
        BenchmarkCoverageType.GENERICO_MUNICIPAL: 3,
        BenchmarkCoverageType.PLACEHOLDER: 3,
    }
    assert all(item.selection_rationale for item in dataset.manifest.scenario_files)


def test_phase3_benchmark_case_contract_requires_minimum_fields() -> None:
    with pytest.raises(ValueError):
        BenchmarkCase.from_dict(
            {
                "case_id": "",
                "tenant_id": "prefeitura-vila-serena",
                "scenario_type": "atendimento_normal",
                "priority_tier": "p1",
                "coverage_type": "tenant_demonstrativo",
                "input_query": "Teste",
                "expected_behavior": "responder_com_contexto_documentado",
                "expected_answer_reference": {
                    "reference_type": "resposta_informativa_minima",
                    "summary": "Resumo",
                },
                "expected_context_reference": {
                    "reference_type": "referencia_documental_minima",
                    "document_hints": ["Central de Atendimento Presencial e Canais Oficiais"],
                },
                "notes": "Caso invalido para validacao.",
            }
        )


def test_phase3_benchmark_case_contract_requires_reference_signals() -> None:
    with pytest.raises(ValueError):
        BenchmarkCase.from_dict(
            {
                "case_id": "case-invalido",
                "tenant_id": "prefeitura-vila-serena",
                "scenario_type": "atendimento_normal",
                "priority_tier": "p1",
                "coverage_type": "tenant_demonstrativo",
                "input_query": "Teste",
                "expected_behavior": "responder_com_contexto_documentado",
                "expected_answer_reference": {
                    "reference_type": "resposta_informativa_minima",
                    "summary": "Resumo minimo",
                    "must_include": [],
                    "must_not_include": ["erro"],
                },
                "expected_context_reference": {
                    "reference_type": "grounding_documental_forte",
                    "document_hints": ["Central de Atendimento Presencial e Canais Oficiais"],
                    "required_terms": ["central de atendimento"],
                    "notes": "Teste invalido.",
                },
                "notes": "Caso invalido para validacao.",
            }
        )


def test_phase3_benchmark_dataset_folder_keeps_cases_under_tenant_group() -> None:
    tenant_dir = BENCHMARK_DATASETS_DIR / "tenants" / "prefeitura-vila-serena"
    dataset_dir = tenant_dir / "benchmark_v1"
    scenario_dir = dataset_dir / "scenarios"

    assert tenant_dir.is_dir()
    assert dataset_dir.is_dir()
    assert scenario_dir.is_dir()
    assert all(path.parent == scenario_dir for path in scenario_dir.glob("*.jsonl"))


def test_phase3_benchmark_manifest_keeps_priority_and_coverage_consistent() -> None:
    manifest_path = (
        BENCHMARK_DATASETS_DIR
        / "tenants"
        / "prefeitura-vila-serena"
        / "benchmark_v1"
        / "dataset_manifest.json"
    )
    dataset = load_benchmark_dataset(manifest_path)
    by_scenario = {item.scenario_type: item for item in dataset.manifest.scenario_files}

    assert by_scenario[BenchmarkScenarioType.ATENDIMENTO_NORMAL].cases_count == 6
    assert by_scenario[BenchmarkScenarioType.ATENDIMENTO_NORMAL].priority_tier == BenchmarkPriorityTier.P1
    assert by_scenario[BenchmarkScenarioType.ATENDIMENTO_NORMAL].coverage_type == BenchmarkCoverageType.TENANT_DEMONSTRATIVO
    assert by_scenario[BenchmarkScenarioType.FORA_DE_ESCOPO].cases_count == 3
    assert by_scenario[BenchmarkScenarioType.FORA_DE_ESCOPO].coverage_type == BenchmarkCoverageType.GENERICO_MUNICIPAL
    assert by_scenario[BenchmarkScenarioType.BAIXA_CONFIANCA].cases_count == 3
    assert by_scenario[BenchmarkScenarioType.BAIXA_CONFIANCA].coverage_type == BenchmarkCoverageType.PLACEHOLDER
    assert by_scenario[BenchmarkScenarioType.RISCO_POLICY].cases_count == 4
    assert by_scenario[BenchmarkScenarioType.RISCO_POLICY].priority_tier == BenchmarkPriorityTier.P1
    assert by_scenario[BenchmarkScenarioType.RISCO_POLICY].coverage_type == BenchmarkCoverageType.TENANT_DEMONSTRATIVO


def test_phase3_normal_cases_expand_coverage_without_breaking_priority() -> None:
    manifest_path = (
        BENCHMARK_DATASETS_DIR
        / "tenants"
        / "prefeitura-vila-serena"
        / "benchmark_v1"
        / "dataset_manifest.json"
    )
    dataset = load_benchmark_dataset(manifest_path)
    normal_cases = [
        case
        for case in dataset.cases
        if case.scenario_type == BenchmarkScenarioType.ATENDIMENTO_NORMAL
    ]
    normal_case_ids = {case.case_id for case in normal_cases}

    assert len(normal_cases) == 6
    assert normal_case_ids == {
        "vs-normal-001",
        "vs-normal-002",
        "vs-normal-003",
        "vs-normal-004",
        "vs-normal-005",
        "vs-normal-006",
    }
    assert all(case.priority_tier == BenchmarkPriorityTier.P1 for case in normal_cases)
    assert all(case.coverage_type == BenchmarkCoverageType.TENANT_DEMONSTRATIVO for case in normal_cases)


def test_phase3_out_of_scope_cases_expand_real_limits_without_overlap_with_low_confidence() -> None:
    manifest_path = (
        BENCHMARK_DATASETS_DIR
        / "tenants"
        / "prefeitura-vila-serena"
        / "benchmark_v1"
        / "dataset_manifest.json"
    )
    dataset = load_benchmark_dataset(manifest_path)
    out_of_scope_cases = [
        case
        for case in dataset.cases
        if case.scenario_type == BenchmarkScenarioType.FORA_DE_ESCOPO
    ]
    case_ids = {case.case_id for case in out_of_scope_cases}

    assert len(out_of_scope_cases) == 3
    assert case_ids == {
        "vs-fora-escopo-001",
        "vs-fora-escopo-002",
        "vs-fora-escopo-003",
    }
    assert all(case.priority_tier == BenchmarkPriorityTier.P2 for case in out_of_scope_cases)
    assert all(case.coverage_type == BenchmarkCoverageType.GENERICO_MUNICIPAL for case in out_of_scope_cases)
    assert all(case.expected_behavior == "recusar_fora_de_escopo_com_redirecionamento" for case in out_of_scope_cases)


def test_phase3_low_confidence_cases_expand_domain_adjacent_gaps_without_fabrication() -> None:
    manifest_path = (
        BENCHMARK_DATASETS_DIR
        / "tenants"
        / "prefeitura-vila-serena"
        / "benchmark_v1"
        / "dataset_manifest.json"
    )
    dataset = load_benchmark_dataset(manifest_path)
    low_confidence_cases = [
        case
        for case in dataset.cases
        if case.scenario_type == BenchmarkScenarioType.BAIXA_CONFIANCA
    ]
    case_ids = {case.case_id for case in low_confidence_cases}

    assert len(low_confidence_cases) == 3
    assert case_ids == {
        "vs-baixa-confianca-001",
        "vs-baixa-confianca-002",
        "vs-baixa-confianca-003",
    }
    assert all(case.priority_tier == BenchmarkPriorityTier.P3 for case in low_confidence_cases)
    assert all(case.coverage_type == BenchmarkCoverageType.PLACEHOLDER for case in low_confidence_cases)
    assert all(case.expected_behavior == "assumir_baixa_confianca_e_redirecionar" for case in low_confidence_cases)


def test_phase3_risk_policy_cases_cover_sensitive_data_and_bypass_attempts() -> None:
    manifest_path = (
        BENCHMARK_DATASETS_DIR
        / "tenants"
        / "prefeitura-vila-serena"
        / "benchmark_v1"
        / "dataset_manifest.json"
    )
    dataset = load_benchmark_dataset(manifest_path)
    risk_policy_cases = [
        case
        for case in dataset.cases
        if case.scenario_type == BenchmarkScenarioType.RISCO_POLICY
    ]
    case_ids = {case.case_id for case in risk_policy_cases}

    assert len(risk_policy_cases) == 4
    assert case_ids == {
        "vs-risco-policy-001",
        "vs-risco-policy-002",
        "vs-risco-policy-003",
        "vs-risco-policy-004",
    }
    assert all(case.priority_tier == BenchmarkPriorityTier.P1 for case in risk_policy_cases)
    assert all(
        case.coverage_type == BenchmarkCoverageType.TENANT_DEMONSTRATIVO
        for case in risk_policy_cases
    )
    assert all(
        case.expected_behavior == "bloquear_por_policy_e_redirecionar"
        for case in risk_policy_cases
    )


def test_phase3_reference_contract_is_consistent_across_scenarios() -> None:
    manifest_path = (
        BENCHMARK_DATASETS_DIR
        / "tenants"
        / "prefeitura-vila-serena"
        / "benchmark_v1"
        / "dataset_manifest.json"
    )
    dataset = load_benchmark_dataset(manifest_path)

    for case in dataset.cases:
        assert (
            case.expected_answer_reference.reference_type
            == SCENARIO_ANSWER_REFERENCE_TYPES[case.scenario_type]
        )
        assert (
            case.expected_context_reference.reference_type
            == SCENARIO_CONTEXT_REFERENCE_TYPES[case.scenario_type]
        )
        assert set(case.expected_answer_reference.must_include).isdisjoint(
            case.expected_answer_reference.must_not_include
        )

        if case.scenario_type == BenchmarkScenarioType.PERGUNTA_AMBIGUA:
            assert len(case.expected_context_reference.document_hints) >= 2
            assert case.expected_context_reference.required_terms == ()
            continue

        assert case.expected_context_reference.required_terms


def test_phase3_baseline_summary_keeps_final_distribution_stable() -> None:
    dataset = load_phase3_initial_baseline()
    summary = build_benchmark_dataset_summary(dataset)
    rendered_summary = format_benchmark_dataset_summary(summary)

    assert isinstance(summary, BenchmarkDatasetSummary)
    assert summary.manifest_path == PHASE3_INITIAL_BASELINE_MANIFEST
    assert summary.total_cases == 17
    assert summary.cases_by_scenario == {
        BenchmarkScenarioType.ATENDIMENTO_NORMAL: 6,
        BenchmarkScenarioType.PERGUNTA_AMBIGUA: 1,
        BenchmarkScenarioType.FORA_DE_ESCOPO: 3,
        BenchmarkScenarioType.BAIXA_CONFIANCA: 3,
        BenchmarkScenarioType.RISCO_POLICY: 4,
    }
    assert summary.cases_by_priority == {
        BenchmarkPriorityTier.P1: 10,
        BenchmarkPriorityTier.P2: 4,
        BenchmarkPriorityTier.P3: 3,
    }
    assert summary.cases_by_coverage == {
        BenchmarkCoverageType.TENANT_DEMONSTRATIVO: 11,
        BenchmarkCoverageType.GENERICO_MUNICIPAL: 3,
        BenchmarkCoverageType.PLACEHOLDER: 3,
    }
    assert "baseline: prefeitura-vila-serena/benchmark_v1" in rendered_summary
    assert "total_cases: 17" in rendered_summary
    assert "atendimento_normal: 6" in rendered_summary
    assert "risco_policy: 4" in rendered_summary
