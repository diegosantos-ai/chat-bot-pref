import sys
import os
import chromadb

# Setup path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.settings import settings

def debug_chroma():
    print(f"📂 Debug ChromaDB: {settings.CHROMA_PERSIST_DIR}")
    print(f"📚 Collection: {settings.RAG_COLLECTION_NAME}")
    
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    collection = client.get_collection(name=settings.RAG_COLLECTION_NAME)
    
    count = collection.count()
    print(f"📊 Total de chunks: {count}")
    
    # Busca chunks que contenham 'buraco' no texto ou metadata
    results = collection.get(
        where_document={"$contains": "buraco"},
        include=["metadatas", "documents"]
    )
    
    print(f"\n🔍 Chunks contendo 'buraco': {len(results['ids'])}")
    for i, doc_id in enumerate(results['ids']):
        print(f"   [{i+1}] ID: {doc_id}")
        print(f"       Source: {results['metadatas'][i].get('source')}")
        print(f"       Section: {results['metadatas'][i].get('section')}")
        print(f"       Text: {results['documents'][i][:100]}...")

if __name__ == "__main__":
    debug_chroma()
