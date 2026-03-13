import asyncio
import sys
import os

# Adiciona diretório raiz ao path para encontrar o módulo 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag.retriever import RAGRetriever


async def main():
    if len(sys.argv) < 2:
        print('Uso: python scripts/query_rag.py "Sua pergunta aqui" [--min-score 0.0]')
        return

    query = sys.argv[1]
    min_score = 0.0 if "--min-score" in sys.argv else 0.3

    print(f"\n🔍 Consultando RAG para: '{query}'...")
    print(f"   Min score: {min_score}\n")

    retriever = RAGRetriever()
    result = await asyncio.to_thread(retriever.retrieve, query, min_score=min_score)

    if not result.chunks:
        print("❌ Nenhum resultado encontrado.")
        return

    print(f"✅ Encontrados {len(result.chunks)} documentos relevantes:\n")
    for i, chunk in enumerate(result.chunks, 1):
        print(f"--- Rumo {i} (Score: {chunk.score:.4f}) ---")
        print(f"📄 Fonte: {chunk.source} > {chunk.title}")
        print(f"📝 Conteúdo: {chunk.text[:300]}...\n")


if __name__ == "__main__":
    asyncio.run(main())
