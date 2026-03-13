import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.contracts.dto import RagResetRequest
from app.services.rag_service import RagService


def main() -> None:
    parser = argparse.ArgumentParser(description="Reseta a base RAG de um tenant.")
    parser.add_argument("--tenant-id", required=True, help="Tenant alvo do reset.")
    parser.add_argument(
        "--purge-documents",
        action="store_true",
        help="Remove tambem os documentos fonte do tenant.",
    )
    args = parser.parse_args()

    service = RagService()
    payload = service.reset(
        RagResetRequest(
            tenant_id=args.tenant_id,
            purge_documents=args.purge_documents,
            remove_legacy_collections=True,
        )
    ).model_dump(mode="json")
    print(json.dumps(payload, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
