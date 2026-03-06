"""
RAG Ingest - Carrega documentos da base de conhecimento e cria embeddings no ChromaDB.

Responsabilidades:
- Ler arquivos Markdown da base de conhecimento
- Dividir em chunks otimizados para retrieval
- Gerar embeddings e armazenar no ChromaDB
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Generator, Optional

import chromadb
from chromadb.config import Settings

from app.settings import settings
from app.rag.embeddings import (
    get_embedding_function,
    get_collection_name,
    resolve_embedding_model,
)

# Configuracoes de chunking
CHUNK_SIZE = 500  # tokens aproximados (chars / 4)
CHUNK_OVERLAP = 150  # overlap aumentado para melhorar contexto entre chunks


def _compute_doc_hash(content: str) -> str:
    """Gera hash MD5 do conteudo para detectar mudancas."""
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def _split_into_chunks(
    text: str,
    doc_id: str,
    source_file: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> Generator[dict, None, None]:
    """
    Divide texto em chunks com overlap, preservando estrutura de secoes.

    Estrategia:
    1. Divide por secoes (##) quando possivel
    2. Se secao > chunk_size, divide por paragrafos
    3. Mantem overlap para contexto
    """
    sections = re.split(r"\n(?=#{2,3}\s)", text)
    chunk_idx = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue

        section_title = ""
        title_match = re.match(r"^(#{2,3})\s+(.+?)$", section, re.MULTILINE)
        if title_match:
            section_title = title_match.group(2).strip()

        if len(section) <= chunk_size * 4:  # chars aproximados
            yield {
                "id": f"{doc_id}_chunk_{chunk_idx:03d}",
                "text": section,
                "metadata": {
                    "source": source_file,
                    "doc_id": doc_id,
                    "section": section_title,
                    "chunk_idx": chunk_idx,
                },
            }
            chunk_idx += 1
        else:
            paragraphs = section.split("\n\n")
            current_chunk: list[str] = []
            current_len = 0

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                para_len = len(para)

                if current_len + para_len > chunk_size * 4 and current_chunk:
                    yield {
                        "id": f"{doc_id}_chunk_{chunk_idx:03d}",
                        "text": "\n\n".join(current_chunk),
                        "metadata": {
                            "source": source_file,
                            "doc_id": doc_id,
                            "section": section_title,
                            "chunk_idx": chunk_idx,
                        },
                    }
                    chunk_idx += 1

                    if overlap > 0 and current_chunk:
                        last_para = current_chunk[-1]
                        current_chunk = [last_para, para]
                        current_len = len(last_para) + para_len
                    else:
                        current_chunk = [para]
                        current_len = para_len
                else:
                    current_chunk.append(para)
                    current_len += para_len

            if current_chunk:
                yield {
                    "id": f"{doc_id}_chunk_{chunk_idx:03d}",
                    "text": "\n\n".join(current_chunk),
                    "metadata": {
                        "source": source_file,
                        "doc_id": doc_id,
                        "section": section_title,
                        "chunk_idx": chunk_idx,
                    },
                }
                chunk_idx += 1


def load_manifest(base_path: Path) -> dict:
    """Carrega manifest.json da base de conhecimento."""
    manifest_path = base_path / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest nao encontrado: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_chroma_client() -> chromadb.ClientAPI:
    """Retorna cliente ChromaDB configurado (HTTP, apontando para nexo-chromadb na rede compartilhada)."""
    from app.settings import settings as app_settings
    host_url = app_settings.CHROMA_URL  # ex: http://nexo-chromadb:8000
    # Extrair host e port da URL
    url_without_protocol = host_url.replace("http://", "").replace("https://", "")
    parts = url_without_protocol.split(":")
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 8000
    return chromadb.HttpClient(
        host=host,
        port=port,
        settings=Settings(anonymized_telemetry=False),
    )


def ingest_document(
    file_path: Path,
    doc_id: str,
    title: str,
    tags: Optional[list[str]] = None,
    collection_name: Optional[str] = None,
    force: bool = False,
    embedding_provider: Optional[str] = None,
) -> int:
    """
    Ingere um unico documento no ChromaDB.
    Retorna numero de chunks criados.
    """
    if not file_path.exists():
        print(f"[WARN] Arquivo nao encontrado: {file_path}")
        return 0

    # Determina collection e embedding function
    client = get_chroma_client()
    provider = embedding_provider or settings.EMBEDDING_PROVIDER
    embedding_model = resolve_embedding_model(provider)
    effective_tags = tags or []
    if not collection_name:
        collection_name = get_collection_name(settings.RAG_COLLECTION_NAME, provider)

    embedding_fn = get_embedding_function(provider)
    collection_kwargs = {"name": collection_name}
    if embedding_fn is not None:
        collection_kwargs["embedding_function"] = embedding_fn
    collection = client.get_or_create_collection(**collection_kwargs)

    # Leitura e Hash
    content = file_path.read_text(encoding="utf-8")
    content_hash = _compute_doc_hash(content)

    # Verifica duplicidade
    existing = collection.get(where={"doc_id": doc_id}, include=["metadatas"])
    if existing["ids"]:
        if not force:
            existing_hash = (
                existing["metadatas"][0].get("content_hash")
                if existing["metadatas"]
                else None
            )
            if existing_hash == content_hash:
                print(f"[SKIP] {doc_id}: sem alteracoes")
                return 0

        collection.delete(where={"doc_id": doc_id})
        action = "REINGEST" if force else "UPDATE"
        print(f"[{action}] {doc_id}: processando...")

    # Chunking
    chunks = list(
        _split_into_chunks(
            text=content,
            doc_id=doc_id,
            source_file=file_path.name,
        )
    )

    if not chunks:
        print(f"[SKIP] {doc_id}: nenhum chunk gerado")
        return 0

    # Metadados
    for chunk in chunks:
        chunk["metadata"]["content_hash"] = content_hash
        chunk["metadata"]["title"] = title
        chunk["metadata"]["tags"] = ",".join(effective_tags)
        chunk["metadata"]["embedding_provider"] = provider
        if embedding_model:
            chunk["metadata"]["embedding_model"] = embedding_model

    # Persistencia
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )

    print(f"[ADD] {doc_id}: {len(chunks)} chunks criados")
    return len(chunks)


def ingest_base(
    base_path: str | Path,
    force: bool = False,
    embedding_provider: Optional[str] = None,
) -> dict:
    """
    Ingere uma base de conhecimento completa no ChromaDB.

    Args:
        base_path: Caminho para a pasta da base (ex: base/BA-RAG-PILOTO-2026.01.v1)
        force: Se True, reprocessa mesmo se hash nao mudou
        embedding_provider: Provedor de embedding ("default", "gemini", "openai", "qwen")

    Returns:
        dict com estatisticas da ingestao
    """
    base_path = Path(base_path)
    manifest = load_manifest(base_path)

    base_id = manifest.get("base_id") or manifest.get("id")
    if not base_id:
        raise ValueError("Manifest deve ter 'id' ou 'base_id'")

    provider = embedding_provider or settings.EMBEDDING_PROVIDER
    embedding_model = resolve_embedding_model(provider)
    base_collection_name = f"rag_{base_id.replace('-', '_').replace('.', '_').lower()}"
    collection_name = get_collection_name(base_collection_name, provider)

    # Garante que collection existe com metadados da base
    client = get_chroma_client()
    embedding_fn = get_embedding_function(provider)
    collection_kwargs = {
        "name": collection_name,
        "metadata": {
            "base_id": base_id,
            "version": manifest.get("version", "1.0"),
            "hnsw:space": "cosine",
            "embedding_provider": provider,
            "embedding_model": embedding_model or "chromadb-default",
        },
    }
    if embedding_fn is not None:
        collection_kwargs["embedding_function"] = embedding_fn
    client.get_or_create_collection(**collection_kwargs)

    stats = {
        "base_id": base_id,
        "collection": collection_name,
        "documents_processed": 0,
        "chunks_created": 0,
        "chunks_skipped": 0,
    }

    items_path = base_path / "items"
    documents = manifest.get("documents") or manifest.get("items", [])

    for doc_info in documents:
        doc_file = items_path / doc_info["file"]

        chunks_count = ingest_document(
            file_path=doc_file,
            doc_id=doc_info["id"],
            title=doc_info["title"],
            tags=doc_info.get("tags", []),
            collection_name=collection_name,
            force=force,
            embedding_provider=provider,
        )

        stats["documents_processed"] += 1
        stats["chunks_created"] += chunks_count

    stats["total_chunks"] = client.get_collection(collection_name).count()
    return stats


def list_collections() -> list[str]:
    """Lista todas as collections RAG disponiveis."""
    client = get_chroma_client()
    return [c.name for c in client.list_collections()]


def delete_collection(collection_name: str) -> bool:
    """Remove uma collection do ChromaDB."""
    client = get_chroma_client()
    try:
        client.delete_collection(collection_name)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python -m app.rag.ingest <caminho_base>")
        print("Exemplo: python -m app.rag.ingest base/BA-RAG-PILOTO-2026.01.v1")
        sys.exit(1)

    base_path = sys.argv[1]
    force = "--force" in sys.argv

    print(f"\n[INGEST] Iniciando ingestao da base: {base_path}")
    print("-" * 50)

    result = ingest_base(base_path, force=force)

    print("-" * 50)
    print("[INGEST] Resumo:")
    print(f"   Base ID: {result['base_id']}")
    print(f"   Collection: {result['collection']}")
    print(f"   Documentos processados: {result['documents_processed']}")
    print(f"   Chunks criados: {result['chunks_created']}")
    print(f"   Chunks pulados: {result['chunks_skipped']}")
    print(f"   Total na collection: {result['total_chunks']}")
