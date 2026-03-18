import logging
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models.param import Param

logger = logging.getLogger(__name__)

def _ingest_stub(**context) -> None:
    """
    Função stub para representar a camada de ingestão de documentos offline.
    A regra de negócio pesada não deve residir aqui.
    O ideal é que este bloco execute o respectivo serviço via CLI, script
    ou API interna isolada.
    """
    tenant_id: str = context["params"]["tenant_id"]
    logger.info(f"[{tenant_id}] Iniciando job offline de ingestão.")
    logger.info("TODO: Invocar o script base de rag_ingest.py ou o wrapper de ingestão principal.")

with DAG(
    dag_id="offline_rag_ingest",
    schedule=None,  # Disparo manual via rotina ou trigger
    start_date=datetime(2024, 1, 1),
    catchup=False,
    params={
        "tenant_id": Param(
            "prefeitura-demo",
            type="string",
            description="Tenant alvo da ingestão documental"
        ),
    },
    tags=["rag", "ingest", "offline"],
    description="DAG offline para ingestão de documentos no RAG por tenant",
) as dag:

    task_ingest = PythonOperator(
        task_id="execute_ingest_stub",
        python_callable=_ingest_stub,
    )
