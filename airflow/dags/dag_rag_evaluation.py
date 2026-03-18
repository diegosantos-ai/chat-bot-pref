import logging
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models.param import Param

logger = logging.getLogger(__name__)

def _evaluation_stub(**context) -> None:
    """
    Função stub para disparar a camada de avaliação formal de RAG
    (ex: run_phase4_rag_evaluation.py).
    """
    tenant_id: str = context["params"]["tenant_id"]
    logger.info(f"[{tenant_id}] Iniciando job offline de avaliação formal de contexto RAG.")
    logger.info("TODO: Invocar benchmark/scripts de eval offline que consolidam as métricas de Retrieval e LLM-Judge.")

with DAG(
    dag_id="offline_rag_evaluation",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    params={
        "tenant_id": Param(
            "prefeitura-demo",
            type="string",
            description="Tenant alvo da avaliação do RAG"
        ),
    },
    tags=["rag", "evaluation", "offline", "llmops"],
    description="DAG offline para avaliar precisão e recall do RAG baseando-se no tenant",
) as dag:

    task_evaluate = PythonOperator(
        task_id="execute_evaluation_stub",
        python_callable=_evaluation_stub,
    )
