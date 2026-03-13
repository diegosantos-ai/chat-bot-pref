import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.rag_service import RagService


def main() -> None:
    parser = argparse.ArgumentParser(description="Mostra o status da base RAG por tenant.")
    parser.add_argument("--tenant-id", required=True, help="Tenant alvo da consulta.")
    args = parser.parse_args()

    service = RagService()
    payload = service.status(args.tenant_id).model_dump(mode="json")
    print(json.dumps(payload, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
