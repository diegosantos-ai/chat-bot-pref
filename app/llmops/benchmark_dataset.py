"""Contratos e validacoes locais para o dataset de benchmark da Fase 3."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
import json
from pathlib import Path
from typing import Any, Final, Mapping

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
BENCHMARK_DATASETS_DIR: Final[Path] = REPO_ROOT / "benchmark_datasets"
PHASE3_INITIAL_BASELINE_MANIFEST: Final[Path] = (
    BENCHMARK_DATASETS_DIR
    / "tenants"
    / "prefeitura-vila-serena"
    / "benchmark_v1"
    / "dataset_manifest.json"
)


class BenchmarkScenarioType(StrEnum):
    """Classifica os cenarios minimos do benchmark reproduzivel."""

    ATENDIMENTO_NORMAL = "atendimento_normal"
    PERGUNTA_AMBIGUA = "pergunta_ambigua"
    FORA_DE_ESCOPO = "fora_de_escopo"
    BAIXA_CONFIANCA = "baixa_confianca"
    RISCO_POLICY = "risco_policy"


class BenchmarkPriorityTier(StrEnum):
    """Classifica a prioridade metodologica do caso ou grupo de casos."""

    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class BenchmarkCoverageType(StrEnum):
    """Diferencia a aderencia do cenario ao tenant demonstrativo."""

    TENANT_DEMONSTRATIVO = "tenant_demonstrativo"
    GENERICO_MUNICIPAL = "generico_municipal"
    PLACEHOLDER = "placeholder"


SCENARIO_ANSWER_REFERENCE_TYPES: Final[Mapping[BenchmarkScenarioType, str]] = {
    BenchmarkScenarioType.ATENDIMENTO_NORMAL: "resposta_informativa_minima",
    BenchmarkScenarioType.PERGUNTA_AMBIGUA: "resposta_de_desambiguacao_minima",
    BenchmarkScenarioType.FORA_DE_ESCOPO: "recusa_fora_de_escopo_minima",
    BenchmarkScenarioType.BAIXA_CONFIANCA: "resposta_de_baixa_confianca_controlada",
    BenchmarkScenarioType.RISCO_POLICY: "bloqueio_por_policy_minimo",
}

SCENARIO_CONTEXT_REFERENCE_TYPES: Final[Mapping[BenchmarkScenarioType, str]] = {
    BenchmarkScenarioType.ATENDIMENTO_NORMAL: "grounding_documental_forte",
    BenchmarkScenarioType.PERGUNTA_AMBIGUA: "grounding_de_desambiguacao",
    BenchmarkScenarioType.FORA_DE_ESCOPO: "grounding_em_limite_institucional",
    BenchmarkScenarioType.BAIXA_CONFIANCA: "grounding_limitado_com_lacuna_controlada",
    BenchmarkScenarioType.RISCO_POLICY: "grounding_em_policy_e_limite",
}


@dataclass(frozen=True, slots=True)
class BenchmarkAnswerReference:
    """Define a referencia minima de resposta esperada para um caso."""

    reference_type: str
    summary: str
    must_include: tuple[str, ...] = ()
    must_not_include: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Valida a estrutura minima da referencia de resposta."""

        _require_non_empty_text("expected_answer_reference.reference_type", self.reference_type)
        _require_non_empty_text("expected_answer_reference.summary", self.summary)
        if not self.must_include:
            raise ValueError("expected_answer_reference.must_include deve conter ao menos um sinal obrigatorio.")
        if not self.must_not_include:
            raise ValueError(
                "expected_answer_reference.must_not_include deve conter ao menos um sinal proibido."
            )
        if set(self.must_include).intersection(self.must_not_include):
            raise ValueError(
                "expected_answer_reference.must_include e must_not_include nao podem se sobrepor."
            )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BenchmarkAnswerReference":
        """Reconstrui a referencia de resposta a partir de um dicionario."""

        return cls(
            reference_type=_require_non_empty_text(
                "expected_answer_reference.reference_type",
                str(payload.get("reference_type", "")),
            ),
            summary=_require_non_empty_text(
                "expected_answer_reference.summary",
                str(payload.get("summary", "")),
            ),
            must_include=_normalize_string_tuple(payload.get("must_include", [])),
            must_not_include=_normalize_string_tuple(payload.get("must_not_include", [])),
        )


@dataclass(frozen=True, slots=True)
class BenchmarkContextReference:
    """Define a referencia minima de contexto esperado para um caso."""

    reference_type: str
    document_hints: tuple[str, ...]
    required_terms: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        """Valida a estrutura minima da referencia de contexto."""

        _require_non_empty_text("expected_context_reference.reference_type", self.reference_type)
        if not self.document_hints:
            raise ValueError("expected_context_reference.document_hints deve conter ao menos um indicio.")
        _require_non_empty_text("expected_context_reference.notes", self.notes)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BenchmarkContextReference":
        """Reconstrui a referencia de contexto a partir de um dicionario."""

        return cls(
            reference_type=_require_non_empty_text(
                "expected_context_reference.reference_type",
                str(payload.get("reference_type", "")),
            ),
            document_hints=_normalize_string_tuple(payload.get("document_hints", [])),
            required_terms=_normalize_string_tuple(payload.get("required_terms", [])),
            notes=str(payload.get("notes", "")).strip(),
        )


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    """Representa o contrato minimo de um caso de avaliacao do benchmark."""

    case_id: str
    tenant_id: str
    scenario_type: BenchmarkScenarioType
    priority_tier: BenchmarkPriorityTier
    coverage_type: BenchmarkCoverageType
    input_query: str
    expected_behavior: str
    expected_answer_reference: BenchmarkAnswerReference
    expected_context_reference: BenchmarkContextReference
    notes: str

    def __post_init__(self) -> None:
        """Valida a presenca dos campos obrigatorios do caso."""

        _require_non_empty_text("case_id", self.case_id)
        _require_non_empty_text("tenant_id", self.tenant_id)
        _require_non_empty_text("input_query", self.input_query)
        _require_non_empty_text("expected_behavior", self.expected_behavior)
        _require_non_empty_text("notes", self.notes)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BenchmarkCase":
        """Reconstrui um caso de benchmark a partir de um dicionario."""

        return cls(
            case_id=_require_non_empty_text("case_id", str(payload.get("case_id", ""))),
            tenant_id=_require_non_empty_text("tenant_id", str(payload.get("tenant_id", ""))),
            scenario_type=BenchmarkScenarioType(str(payload.get("scenario_type", ""))),
            priority_tier=BenchmarkPriorityTier(str(payload.get("priority_tier", ""))),
            coverage_type=BenchmarkCoverageType(str(payload.get("coverage_type", ""))),
            input_query=_require_non_empty_text("input_query", str(payload.get("input_query", ""))),
            expected_behavior=_require_non_empty_text(
                "expected_behavior",
                str(payload.get("expected_behavior", "")),
            ),
            expected_answer_reference=BenchmarkAnswerReference.from_dict(
                _require_mapping("expected_answer_reference", payload.get("expected_answer_reference"))
            ),
            expected_context_reference=BenchmarkContextReference.from_dict(
                _require_mapping("expected_context_reference", payload.get("expected_context_reference"))
            ),
            notes=_require_non_empty_text("notes", str(payload.get("notes", ""))),
        )


@dataclass(frozen=True, slots=True)
class BenchmarkScenarioFile:
    """Descreve um arquivo de casos agrupados por cenario."""

    scenario_type: BenchmarkScenarioType
    relative_path: str
    cases_count: int
    priority_tier: BenchmarkPriorityTier
    coverage_type: BenchmarkCoverageType
    selection_rationale: str

    def __post_init__(self) -> None:
        """Valida a declaracao minima do arquivo de cenario."""

        _require_non_empty_text("scenario_files.relative_path", self.relative_path)
        _require_non_empty_text("scenario_files.selection_rationale", self.selection_rationale)
        if self.cases_count < 1:
            raise ValueError("scenario_files.cases_count deve ser maior ou igual a 1.")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BenchmarkScenarioFile":
        """Reconstrui um descritor de arquivo de cenario a partir do manifest."""

        return cls(
            scenario_type=BenchmarkScenarioType(str(payload.get("scenario_type", ""))),
            relative_path=_require_non_empty_text(
                "scenario_files.relative_path",
                str(payload.get("relative_path", "")),
            ),
            cases_count=int(payload.get("cases_count", 0)),
            priority_tier=BenchmarkPriorityTier(str(payload.get("priority_tier", ""))),
            coverage_type=BenchmarkCoverageType(str(payload.get("coverage_type", ""))),
            selection_rationale=_require_non_empty_text(
                "scenario_files.selection_rationale",
                str(payload.get("selection_rationale", "")),
            ),
        )


@dataclass(frozen=True, slots=True)
class BenchmarkDatasetManifest:
    """Representa o manifest minimo de um dataset versionado de benchmark."""

    dataset_version: str
    tenant_id: str
    description: str
    selection_hypotheses: tuple[str, ...]
    scenario_files: tuple[BenchmarkScenarioFile, ...]
    notes: str
    manifest_path: Path

    def __post_init__(self) -> None:
        """Valida os campos obrigatorios do manifest do dataset."""

        _require_non_empty_text("dataset_version", self.dataset_version)
        _require_non_empty_text("tenant_id", self.tenant_id)
        _require_non_empty_text("description", self.description)
        _require_non_empty_text("notes", self.notes)
        if not self.selection_hypotheses:
            raise ValueError("selection_hypotheses deve conter ao menos uma hipotese.")
        if not self.scenario_files:
            raise ValueError("scenario_files deve conter ao menos um arquivo de cenario.")

    def dataset_dir(self) -> Path:
        """Retorna o diretorio raiz do dataset a partir do manifest."""

        return self.manifest_path.parent

    def scenario_path(self, scenario_file: BenchmarkScenarioFile) -> Path:
        """Resolve o caminho absoluto de um arquivo de cenario do dataset."""

        return self.dataset_dir() / scenario_file.relative_path

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        manifest_path: Path,
    ) -> "BenchmarkDatasetManifest":
        """Reconstrui o manifest a partir do JSON versionado."""

        raw_files = payload.get("scenario_files", [])
        if not isinstance(raw_files, list):
            raise ValueError("scenario_files deve ser uma lista.")

        return cls(
            dataset_version=_require_non_empty_text(
                "dataset_version",
                str(payload.get("dataset_version", "")),
            ),
            tenant_id=_require_non_empty_text("tenant_id", str(payload.get("tenant_id", ""))),
            description=_require_non_empty_text("description", str(payload.get("description", ""))),
            selection_hypotheses=_normalize_string_tuple(payload.get("selection_hypotheses", [])),
            scenario_files=tuple(BenchmarkScenarioFile.from_dict(item) for item in raw_files),
            notes=_require_non_empty_text("notes", str(payload.get("notes", ""))),
            manifest_path=manifest_path,
        )


@dataclass(frozen=True, slots=True)
class LoadedBenchmarkDataset:
    """Agrupa o manifest e os casos carregados de um dataset local."""

    manifest: BenchmarkDatasetManifest
    cases: tuple[BenchmarkCase, ...]


@dataclass(frozen=True, slots=True)
class BenchmarkDatasetSummary:
    """Consolida o resumo agregador de um dataset local de benchmark."""

    tenant_id: str
    dataset_version: str
    manifest_path: Path
    total_cases: int
    cases_by_scenario: dict[BenchmarkScenarioType, int]
    cases_by_priority: dict[BenchmarkPriorityTier, int]
    cases_by_coverage: dict[BenchmarkCoverageType, int]


def discover_benchmark_manifests(base_dir: Path | None = None) -> tuple[Path, ...]:
    """Descobre manifests de benchmark seguindo a estrutura tenant/version."""

    root_dir = base_dir or BENCHMARK_DATASETS_DIR
    return tuple(sorted(root_dir.glob("tenants/*/*/dataset_manifest.json")))


def load_phase3_initial_baseline() -> LoadedBenchmarkDataset:
    """Carrega o benchmark baseline inicial consolidado da Fase 3."""

    return load_benchmark_dataset(PHASE3_INITIAL_BASELINE_MANIFEST)


def build_benchmark_dataset_summary(dataset: LoadedBenchmarkDataset) -> BenchmarkDatasetSummary:
    """Gera um resumo agregador estavel de um dataset de benchmark carregado."""

    return BenchmarkDatasetSummary(
        tenant_id=dataset.manifest.tenant_id,
        dataset_version=dataset.manifest.dataset_version,
        manifest_path=dataset.manifest.manifest_path,
        total_cases=len(dataset.cases),
        cases_by_scenario=dict(Counter(case.scenario_type for case in dataset.cases)),
        cases_by_priority=dict(Counter(case.priority_tier for case in dataset.cases)),
        cases_by_coverage=dict(Counter(case.coverage_type for case in dataset.cases)),
    )


def format_benchmark_dataset_summary(summary: BenchmarkDatasetSummary) -> str:
    """Renderiza um resumo textual simples e reproduzivel do benchmark."""

    lines = [
        f"baseline: {summary.tenant_id}/{summary.dataset_version}",
        f"manifest: {summary.manifest_path.relative_to(REPO_ROOT)}",
        f"total_cases: {summary.total_cases}",
        "cases_by_scenario:",
    ]
    for scenario_type in BenchmarkScenarioType:
        lines.append(f"  - {scenario_type.value}: {summary.cases_by_scenario.get(scenario_type, 0)}")

    lines.append("cases_by_priority:")
    for priority_tier in BenchmarkPriorityTier:
        lines.append(f"  - {priority_tier.value}: {summary.cases_by_priority.get(priority_tier, 0)}")

    lines.append("cases_by_coverage:")
    for coverage_type in BenchmarkCoverageType:
        lines.append(f"  - {coverage_type.value}: {summary.cases_by_coverage.get(coverage_type, 0)}")

    return "\n".join(lines)


def load_benchmark_manifest(manifest_path: Path) -> BenchmarkDatasetManifest:
    """Carrega o manifest versionado de um dataset de benchmark."""

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = BenchmarkDatasetManifest.from_dict(payload, manifest_path=manifest_path)
    validate_benchmark_manifest(manifest)
    return manifest


def load_benchmark_cases(manifest: BenchmarkDatasetManifest) -> tuple[BenchmarkCase, ...]:
    """Carrega todos os casos JSONL declarados no manifest do dataset."""

    loaded_cases: list[BenchmarkCase] = []
    for scenario_file in manifest.scenario_files:
        file_path = manifest.scenario_path(scenario_file)
        line_number = 0
        with file_path.open("r", encoding="utf-8") as handler:
            for raw_line in handler:
                line_number += 1
                stripped_line = raw_line.strip()
                if not stripped_line:
                    continue
                case = BenchmarkCase.from_dict(json.loads(stripped_line))
                if case.scenario_type != scenario_file.scenario_type:
                    raise ValueError(
                        "scenario_type divergente entre o manifest e o arquivo "
                        f"{file_path}:{line_number}."
                    )
                if case.priority_tier != scenario_file.priority_tier:
                    raise ValueError(
                        "priority_tier divergente entre o manifest e o arquivo "
                        f"{file_path}:{line_number}."
                    )
                if case.coverage_type != scenario_file.coverage_type:
                    raise ValueError(
                        "coverage_type divergente entre o manifest e o arquivo "
                        f"{file_path}:{line_number}."
                    )
                loaded_cases.append(case)

    return tuple(loaded_cases)


def load_benchmark_dataset(manifest_path: Path) -> LoadedBenchmarkDataset:
    """Carrega e valida um dataset completo de benchmark."""

    manifest = load_benchmark_manifest(manifest_path)
    cases = load_benchmark_cases(manifest)
    dataset = LoadedBenchmarkDataset(manifest=manifest, cases=cases)
    validate_loaded_benchmark_dataset(dataset)
    return dataset


def validate_benchmark_manifest(manifest: BenchmarkDatasetManifest) -> None:
    """Valida a estrutura local e tenant-aware do manifest do dataset."""

    expected_dataset_dir = BENCHMARK_DATASETS_DIR / "tenants" / manifest.tenant_id / manifest.dataset_version
    if manifest.dataset_dir() != expected_dataset_dir:
        raise ValueError(
            "Manifest fora da estrutura esperada benchmark_datasets/tenants/<tenant_id>/<dataset_version>/."
        )

    for scenario_file in manifest.scenario_files:
        scenario_path = manifest.scenario_path(scenario_file)
        if not scenario_path.is_file():
            raise ValueError(f"Arquivo de cenario ausente: {scenario_path}")


def validate_loaded_benchmark_dataset(dataset: LoadedBenchmarkDataset) -> None:
    """Valida consistencia estrutural e segregacao por tenant do dataset carregado."""

    seen_case_ids: set[str] = set()
    counts_by_scenario: dict[BenchmarkScenarioType, int] = {}

    for case in dataset.cases:
        if case.case_id in seen_case_ids:
            raise ValueError(f"case_id duplicado no dataset: {case.case_id}")
        seen_case_ids.add(case.case_id)

        if case.tenant_id != dataset.manifest.tenant_id:
            raise ValueError(
                "Caso com tenant_id divergente do manifest: "
                f"{case.case_id} -> {case.tenant_id} != {dataset.manifest.tenant_id}"
            )

        _validate_case_reference_contract(case)
        counts_by_scenario[case.scenario_type] = counts_by_scenario.get(case.scenario_type, 0) + 1

    for scenario_file in dataset.manifest.scenario_files:
        actual_count = counts_by_scenario.get(scenario_file.scenario_type, 0)
        if actual_count != scenario_file.cases_count:
            raise ValueError(
                "Contagem divergente para o cenario "
                f"{scenario_file.scenario_type.value}: {actual_count} != {scenario_file.cases_count}"
            )


def _validate_case_reference_contract(case: BenchmarkCase) -> None:
    """Valida a consistencia minima da referencia de resposta e contexto por cenario."""

    expected_answer_type = SCENARIO_ANSWER_REFERENCE_TYPES[case.scenario_type]
    if case.expected_answer_reference.reference_type != expected_answer_type:
        raise ValueError(
            "expected_answer_reference.reference_type divergente para o cenario "
            f"{case.scenario_type.value}: {case.expected_answer_reference.reference_type} != "
            f"{expected_answer_type}"
        )

    expected_context_type = SCENARIO_CONTEXT_REFERENCE_TYPES[case.scenario_type]
    if case.expected_context_reference.reference_type != expected_context_type:
        raise ValueError(
            "expected_context_reference.reference_type divergente para o cenario "
            f"{case.scenario_type.value}: {case.expected_context_reference.reference_type} != "
            f"{expected_context_type}"
        )

    if case.scenario_type == BenchmarkScenarioType.PERGUNTA_AMBIGUA:
        if len(case.expected_context_reference.document_hints) < 2:
            raise ValueError(
                "Casos de pergunta_ambigua devem apontar ao menos dois indicios documentais."
            )
        return

    if not case.expected_context_reference.required_terms:
        raise ValueError(
            "required_terms deve conter ao menos um termo esperado para cenarios "
            f"{case.scenario_type.value}."
        )


def _normalize_string_tuple(raw_value: Any) -> tuple[str, ...]:
    """Normaliza listas textuais do contrato em tuplas estaveis."""

    if raw_value is None:
        return ()
    if not isinstance(raw_value, list):
        raise ValueError("Valor esperado como lista textual.")
    normalized_items = [str(item).strip() for item in raw_value if str(item).strip()]
    return tuple(normalized_items)


def _require_mapping(field_name: str, raw_value: Any) -> Mapping[str, Any]:
    """Garante que um campo obrigatorio do contrato seja um objeto JSON."""

    if not isinstance(raw_value, Mapping):
        raise ValueError(f"{field_name} deve ser um objeto JSON.")
    return raw_value


def _require_non_empty_text(field_name: str, raw_value: str) -> str:
    """Garante a presenca de texto obrigatorio no contrato local."""

    normalized_value = str(raw_value).strip()
    if not normalized_value:
        raise ValueError(f"Campo obrigatorio ausente: {field_name}")
    return normalized_value
