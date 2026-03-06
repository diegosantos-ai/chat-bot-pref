"""
Analytics API — Endpoints para visualizar métricas RAG
======================================================
"""

from fastapi import APIRouter, HTTPException
from app.analytics import RAGMetrics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def get_rag_summary():
    """
    GET /analytics/summary
    
    Retorna resumo de métricas RAG:
    - Hit rate (% de respostas bem-sucedidas)
    - Distribuição de fallbacks
    - Queries que falharam
    - Confiança média do classifier
    """
    return RAGMetrics.generate_summary()


@router.get("/export-csv")
async def export_metrics_csv():
    """
    GET /analytics/export-csv
    
    Exporta todas as queries em formato CSV para análise em Excel.
    """
    filepath = RAGMetrics.export_csv_report()
    
    if not filepath:
        raise HTTPException(status_code=500, detail="Erro ao exportar CSV")
    
    return {
        "status": "ok",
        "file": filepath,
        "message": "Abra este arquivo no Excel para análise detalhada",
    }


@router.post("/save-summary")
async def save_metrics_summary():
    """
    POST /analytics/save-summary
    
    Salva resumo atual em JSON para histórico.
    """
    RAGMetrics.save_summary()
    
    return {
        "status": "ok",
        "message": "Resumo salvo com sucesso",
    }
