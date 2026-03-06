import asyncio
import os
import sys

# Setup path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.rag.retriever import RAGRetriever
from app.nlp.query_expander import expand_query

async def debug_rag():
    print("🔍 Debug RAG Scores & Retrieval")
    print("===============================")
    
    retriever = RAGRetriever()
    
    test_queries = [
        "Onde fika a upa mais pertu?",
        "Quando vai ser a Festa da Polenta?",
        "Tem vaga para curso de informática?",
        "Buraco na rua quem chamo?",
        "Quais os documentos para vacinar filho?",
        "Como funciona o REFIS?",
    ]
    
    for q in test_queries:
        print(f"\n❓ Pergunta Original: '{q}'")
        
        # 1. Expansão
        expanded = expand_query(q)
        print(f"   ✨ Expandida: '{expanded}'")
        
        # 2. Retrieval
        # Retrieve sem filtro de score para ver tudo
        # Mas o método retrieve já aplica o settings.RAG_MIN_SCORE.
        # Vamos chamar retrieve e ver o que vem.
        
        result = retriever.retrieve(expanded)
        
        print(f"   🔎 Chunks encontrados: {len(result.chunks)}")
        print(f"   🏆 Melhor Score: {result.best_score:.4f}" if result.best_score else "   🏆 Melhor Score: N/A")
        
        if result.chunks:
            for i, chunk in enumerate(result.chunks):
                print(f"      [{i+1}] Score: {chunk.score:.4f} | Doc: {chunk.title} > {chunk.section}")
                print(f"          Texto: {chunk.text[:100]}...")
        else:
            print("      ⚠️ Nenhum chunk passou no filtro atual.")

if __name__ == "__main__":
    asyncio.run(debug_rag())
