from pathlib import Path

import pytest

from app.llmops.benchmark_dataset import (
    BENCHMARK_DATASETS_DIR,
    BenchmarkCase,
    BenchmarkScenarioType,
    discover_benchmark_manifests,
    load_benchmark_dataset,
)


def test_phase3_benchmark_manifests_are_discoverable() -> None:
    manifests = discover_benchmark_manifests()

    assert manifests
    assert all(path.is_file() for path in manifests)
    assert BENCHMARK_DATASETS_DIR.is_dir()


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

    assert dataset.manifest.dataset_version == "benchmark_v1"
    assert dataset.manifest.tenant_id == "prefeitura-vila-serena"
    assert len(dataset.cases) == 5
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
    assert all(case.expected_context_reference.document_hints for case in dataset.cases)


def test_phase3_benchmark_case_contract_requires_minimum_fields() -> None:
    with pytest.raises(ValueError):
        BenchmarkCase.from_dict(
            {
                "case_id": "",
                "tenant_id": "prefeitura-vila-serena",
                "scenario_type": "atendimento_normal",
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


def test_phase3_benchmark_dataset_folder_keeps_cases_under_tenant_group() -> None:
    tenant_dir = BENCHMARK_DATASETS_DIR / "tenants" / "prefeitura-vila-serena"
    dataset_dir = tenant_dir / "benchmark_v1"
    scenario_dir = dataset_dir / "scenarios"

    assert tenant_dir.is_dir()
    assert dataset_dir.is_dir()
    assert scenario_dir.is_dir()
    assert all(path.parent == scenario_dir for path in scenario_dir.glob("*.jsonl"))
