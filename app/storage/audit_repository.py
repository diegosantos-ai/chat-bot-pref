from pathlib import Path

from app.contracts.dto import AuditEventRecord
from app.settings import settings


class FileAuditRepository:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        root = Path(base_dir or settings.DATA_DIR)
        self.base_dir = root

    def append_event(self, record: AuditEventRecord) -> Path:
        audit_dir = self.base_dir / "audit" / record.tenant_id
        audit_dir.mkdir(parents=True, exist_ok=True)
        file_path = audit_dir / f"{record.session_id}.jsonl"

        with file_path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json())
            handle.write("\n")

        return file_path
