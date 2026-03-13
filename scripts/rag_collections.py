import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.storage.chroma_repository import TenantChromaRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Lista collections e contagens do Chroma.")
    parser.add_argument(
        "--contains",
        default="",
        help="Filtra collections pelo trecho informado.",
    )
    args = parser.parse_args()

    repository = TenantChromaRepository()
    stats = [
        {"collection": name, "chunks_count": count}
        for name, count in repository.collection_stats()
        if args.contains in name
    ]
    print(json.dumps({"collections": stats}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
