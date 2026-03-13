import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.contracts.dto import RagIngestRequest
from app.services.rag_service import RagService


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa a ingestao RAG por tenant.")
    parser.add_argument("--tenant-id", required=True, help="Tenant alvo da ingestao.")
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Nao reseta a collection antes de ingerir.",
    )
    args = parser.parse_args()

    service = RagService()
    payload = service.ingest(
        RagIngestRequest(
            tenant_id=args.tenant_id,
            reset_collection=not args.no_reset,
        )
    ).model_dump(mode="json")
    print(json.dumps(payload, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
