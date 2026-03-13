import json
from pathlib import Path

from app.contracts.dto import ChatExchangeRecord
from app.settings import settings


class FileChatRepository:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        root = Path(base_dir or settings.DATA_DIR)
        self.base_dir = root

    def append_exchange(self, record: ChatExchangeRecord) -> Path:
        tenant_dir = self.base_dir / record.tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        file_path = tenant_dir / f"{record.session_id}.jsonl"

        with file_path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json())
            handle.write("\n")

        return file_path
