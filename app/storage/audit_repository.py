from pathlib import Path

from app.contracts.dto import AuditEventRecord
from app.observability.logging import log_event
from app.observability.tracing import annotate_current_span, get_tracer
from app.settings import settings


class FileAuditRepository:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        root = Path(base_dir or settings.DATA_DIR)
        self.base_dir = root
        self.tracer = get_tracer(__name__)

    def append_event(self, record: AuditEventRecord) -> Path:
        with self.tracer.start_as_current_span("audit.persist"):
            annotate_current_span(
                request_id=record.request_id,
                tenant_id=record.tenant_id,
                session_id=record.session_id,
                channel=record.channel,
                event_type=record.event_type,
            )
            audit_dir = self.base_dir / "audit" / record.tenant_id
            audit_dir.mkdir(parents=True, exist_ok=True)
            file_path = audit_dir / f"{record.session_id}.jsonl"

            with file_path.open("a", encoding="utf-8") as handle:
                handle.write(record.model_dump_json())
                handle.write("\n")

        log_event(
            "audit.event.persisted",
            request_id=record.request_id,
            tenant_id=record.tenant_id,
            session_id=record.session_id,
            channel=record.channel,
            event_type=record.event_type,
            schema_version=record.schema_version,
            policy_stage=record.policy_decision.stage if record.policy_decision else "",
            decision=record.policy_decision.decision if record.policy_decision else "",
            reason_codes=record.policy_decision.reason_codes if record.policy_decision else [],
        )

        return file_path
