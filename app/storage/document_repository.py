import json
from pathlib import Path

from app.contracts.dto import RagDocumentRecord
from app.settings import settings


class FileDocumentRepository:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir or settings.KNOWLEDGE_BASE_DIR)

    def source_dir(self, tenant_id: str) -> Path:
        directory = self.base_dir / tenant_id / "documents"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def save_document(self, record: RagDocumentRecord) -> Path:
        file_path = self.source_dir(record.tenant_id) / f"{record.id}.json"
        payload = record.model_dump(mode="json")
        file_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return file_path

    def get_document(self, tenant_id: str, document_id: str) -> RagDocumentRecord | None:
        file_path = self.source_dir(tenant_id) / f"{document_id}.json"
        if not file_path.exists():
            return None
        return RagDocumentRecord.model_validate_json(file_path.read_text(encoding="utf-8"))

    def list_documents(self, tenant_id: str) -> list[RagDocumentRecord]:
        documents: list[RagDocumentRecord] = []
        for file_path in sorted(self.source_dir(tenant_id).glob("*.json")):
            documents.append(
                RagDocumentRecord.model_validate_json(file_path.read_text(encoding="utf-8"))
            )
        documents.sort(key=lambda item: (item.updated_at, item.title.lower()), reverse=True)
        return documents

    def delete_document(self, tenant_id: str, document_id: str) -> bool:
        file_path = self.source_dir(tenant_id) / f"{document_id}.json"
        if not file_path.exists():
            return False
        file_path.unlink()
        return True

    def reset_documents(self, tenant_id: str) -> int:
        removed = 0
        for file_path in self.source_dir(tenant_id).glob("*.json"):
            file_path.unlink()
            removed += 1
        return removed

    def ingest_status_path(self, tenant_id: str) -> Path:
        tenant_dir = self.base_dir / tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir / "ingest_status.json"

    def write_ingest_status(self, tenant_id: str, payload: dict[str, object]) -> None:
        status_path = self.ingest_status_path(tenant_id)
        status_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def read_ingest_status(self, tenant_id: str) -> dict[str, object]:
        status_path = self.ingest_status_path(tenant_id)
        if not status_path.exists():
            return {}
        return json.loads(status_path.read_text(encoding="utf-8"))

