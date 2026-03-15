"""Contratos e validacoes locais para o dataset de benchmark da Fase 3."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from pathlib import Path
from typing import Any, Final, Mapping

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
BENCHMARK_DATASETS_DIR: Final[Path] = REPO_ROOT / "benchmark_datasets"


class BenchmarkScenarioType(StrEnum):
    """Classifica os cenarios minimos do benchmark reproduzivel."""

    ATENDIMENTO_NORMAL = "atendimento_normal"
    PERGUNTA_AMBIGUA = "pergunta_ambigua"
    FORA_DE_ESCOPO = "fora_de_escopo"
    BAIXA_CONFIANCA = "baixa_confianca"
    RISCO_POLICY = "risco_policy"


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

    def __post_init__(self) -> None:
        """Valida a declaracao minima do arquivo de cenario."""

        _require_non_empty_text("scenario_files.relative_path", self.relative_path)
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
        )


@dataclass(frozen=True, slots=True)
class BenchmarkDatasetManifest:
    """Representa o manifest minimo de um dataset versionado de benchmark."""

    dataset_version: str
    tenant_id: str
    description: str
    scenario_files: tuple[BenchmarkScenarioFile, ...]
    notes: str
    manifest_path: Path

    def __post_init__(self) -> None:
        """Valida os campos obrigatorios do manifest do dataset."""

        _require_non_empty_text("dataset_version", self.dataset_version)
        _require_non_empty_text("tenant_id", self.tenant_id)
        _require_non_empty_text("description", self.description)
        _require_non_empty_text("notes", self.notes)
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
            scenario_files=tuple(BenchmarkScenarioFile.from_dict(item) for item in raw_files),
            notes=_require_non_empty_text("notes", str(payload.get("notes", ""))),
            manifest_path=manifest_path,
        )


@dataclass(frozen=True, slots=True)
class LoadedBenchmarkDataset:
    """Agrupa o manifest e os casos carregados de um dataset local."""

    manifest: BenchmarkDatasetManifest
    cases: tuple[BenchmarkCase, ...]


def discover_benchmark_manifests(base_dir: Path | None = None) -> tuple[Path, ...]:
    """Descobre manifests de benchmark seguindo a estrutura tenant/version."""

    root_dir = base_dir or BENCHMARK_DATASETS_DIR
    return tuple(sorted(root_dir.glob("tenants/*/*/dataset_manifest.json")))


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

        counts_by_scenario[case.scenario_type] = counts_by_scenario.get(case.scenario_type, 0) + 1

    for scenario_file in dataset.manifest.scenario_files:
        actual_count = counts_by_scenario.get(scenario_file.scenario_type, 0)
        if actual_count != scenario_file.cases_count:
            raise ValueError(
                "Contagem divergente para o cenario "
                f"{scenario_file.scenario_type.value}: {actual_count} != {scenario_file.cases_count}"
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
