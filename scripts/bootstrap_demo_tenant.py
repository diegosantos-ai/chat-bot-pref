import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.contracts.dto import RagIngestRequest
from app.services.demo_tenant_service import DemoTenantService
from app.services.rag_service import RagService
from app.storage.document_repository import FileDocumentRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Materializa o tenant demonstrativo no runtime local.")
    parser.add_argument(
        "--manifest",
        required=True,
        help="Caminho para o tenant.json do tenant demonstrativo.",
    )
    parser.add_argument(
        "--base-dir",
        default="data/knowledge_base",
        help="Diretorio alvo para os documentos materializados.",
    )
    parser.add_argument(
        "--purge-documents",
        action="store_true",
        help="Remove documentos existentes do tenant antes de copiar os documentos do bundle.",
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Executa a ingestao ao final da materializacao.",
    )
    args = parser.parse_args()

    service = DemoTenantService()
    validation = service.validate_bundle(args.manifest)
    managerial_report = service.build_managerial_report(args.manifest)
    if validation["status"] != "passed":
        raise SystemExit(json.dumps(managerial_report, ensure_ascii=True, indent=2))

    summary = service.bootstrap_bundle(
        manifest_path=args.manifest,
        target_base_dir=args.base_dir,
        purge_documents=args.purge_documents,
    )
    summary["managerial_report"] = managerial_report

    if args.ingest:
        rag_service = RagService(
            document_repository=FileDocumentRepository(base_dir=args.base_dir),
        )
        summary["ingest"] = rag_service.ingest(
            RagIngestRequest(
                tenant_id=summary["tenant_id"],
                reset_collection=True,
            )
        ).model_dump(mode="json")

    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
