import json
from pathlib import Path

from app.contracts.dto import ChatExchangeRecord
from app.observability.logging import log_event
from app.observability.tracing import annotate_current_span, get_tracer
from app.settings import settings


class FileChatRepository:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        root = Path(base_dir or settings.DATA_DIR)
        self.base_dir = root
        self.tracer = get_tracer(__name__)

    def append_exchange(self, record: ChatExchangeRecord) -> Path:
        with self.tracer.start_as_current_span("response.persist"):
            annotate_current_span(
                request_id=record.request_id,
                tenant_id=record.tenant_id,
                session_id=record.session_id,
                channel=record.channel,
            )
            tenant_dir = self.base_dir / record.tenant_id
            tenant_dir.mkdir(parents=True, exist_ok=True)
            file_path = tenant_dir / f"{record.session_id}.jsonl"

            with file_path.open("a", encoding="utf-8") as handle:
                handle.write(record.model_dump_json())
                handle.write("\n")

        log_event(
            "chat.exchange.persisted",
            request_id=record.request_id,
            tenant_id=record.tenant_id,
            session_id=record.session_id,
            channel=record.channel,
        )

        return file_path
