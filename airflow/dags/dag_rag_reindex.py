import logging
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models.param import Param

logger = logging.getLogger(__name__)

def _reindex_stub(**context) -> None:
    """
    Função stub para representar a camada de reindexação (limpeza e recriação da base vetorial do tenant).
    """
    tenant_id: str = context["params"]["tenant_id"]
    logger.info(f"[{tenant_id}] Iniciando job offline de reindexação.")
    logger.info("TODO: Invocar o script de reset de coleção e reprocessamento das fontes ou invocar job equivalente.")

with DAG(
    dag_id="offline_rag_reindex",
    schedule=None,  # Disparo sob demanda ou semanal
    start_date=datetime(2024, 1, 1),
    catchup=False,
    params={
        "tenant_id": Param(
            "prefeitura-demo",
            type="string",
            description="Tenant alvo da reindexação"
        ),
    },
    tags=["rag", "reindex", "offline"],
    description="DAG offline para recriar base vetorial/RAG (reindex) por tenant",
) as dag:

    task_reindex = PythonOperator(
        task_id="execute_reindex_stub",
        python_callable=_reindex_stub,
    )
