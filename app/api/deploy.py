"""
Deploy Webhook - Pilot Atendimento
==================================
Endpoint para deploy automático via CI/CD.
Executa git fetch, git pull e reinicia o serviço terezia-api.
"""

from pathlib import Path
import sys

from fastapi import APIRouter, HTTPException, Request, Header

from app.settings import settings
import subprocess
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Deploy"])
WORK_DIR = str(Path(__file__).resolve().parents[2])


def get_git_hash(work_dir: str) -> str:
    """Retorna o hash curto do commit atual."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def get_git_log_oneline(work_dir: str) -> str:
    """Retorna o último commit em formato oneline."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--oneline"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


@router.post("/updateAPI")
async def trigger_deploy(
    request: Request,
    x_deploy_token: str = Header(None, alias="X-Deploy-Token"),
):
    """
    Webhook para deploy automático.

    Requer header X-Deploy-Token com token válido.
    Executa: git fetch, git pull, systemctl restart terezia-api
    """
    # 1. Validar token
    if not settings.DEPLOY_WEBHOOK_TOKEN:
        logger.error("DEPLOY_WEBHOOK_TOKEN não configurado")
        raise HTTPException(status_code=503, detail="Deploy não configurado")

    if x_deploy_token != settings.DEPLOY_WEBHOOK_TOKEN:
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(f"Deploy rejeitado: token inválido de {client_ip}")
        raise HTTPException(status_code=401, detail="Token inválido")

    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Deploy autorizado de {client_ip}")

    work_dir = WORK_DIR
    results = {"steps": []}

    # Capturar hash ANTES do pull
    hash_before = get_git_hash(work_dir)
    commit_before = get_git_log_oneline(work_dir)
    logger.info(f"Commit atual (antes): {commit_before}")

    try:
        # 2. Git fetch
        fetch_result = subprocess.run(
            ["git", "fetch", "--all"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        results["steps"].append(
            {
                "step": "git fetch",
                "success": fetch_result.returncode == 0,
                "output": fetch_result.stdout.strip() or fetch_result.stderr.strip(),
            }
        )
        if fetch_result.returncode != 0:
            raise Exception(f"git fetch falhou: {fetch_result.stderr}")

        # 3. Git pull
        pull_result = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        pull_output = pull_result.stdout.strip() or pull_result.stderr.strip()
        results["steps"].append(
            {
                "step": "git pull",
                "success": pull_result.returncode == 0,
                "output": pull_output,
            }
        )
        if pull_result.returncode != 0:
            raise Exception(f"git pull falhou: {pull_result.stderr}")

        # Capturar hash DEPOIS do pull
        hash_after = get_git_hash(work_dir)
        commit_after = get_git_log_oneline(work_dir)

        # Log detalhado da atualização
        if hash_before != hash_after:
            logger.info(f"Código atualizado: {hash_before} -> {hash_after}")
            logger.info(f"Commit anterior: {commit_before}")
            logger.info(f"Commit novo: {commit_after}")
            results["update"] = {
                "changed": True,
                "before": {"hash": hash_before, "commit": commit_before},
                "after": {"hash": hash_after, "commit": commit_after},
            }
        else:
            logger.info(f"Código já estava atualizado: {hash_after}")
            results["update"] = {
                "changed": False,
                "hash": hash_after,
                "commit": commit_after,
            }

        # 4. Instalar dependências do requirements.txt
        pip_result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=300,
        )
        results["steps"].append(
            {
                "step": "pip install requirements",
                "success": pip_result.returncode == 0,
                "output": pip_result.stdout.strip()[-500:]
                if pip_result.returncode == 0
                else pip_result.stderr.strip()[-500:],
            }
        )
        if pip_result.returncode != 0:
            logger.error(f"pip install falhou: {pip_result.stderr}")
            # Não falha o deploy, apenas loga o erro

        # 5. Restart service em BACKGROUND (com delay para resposta ser enviada)
        subprocess.Popen(
            ["bash", "-c", "sleep 2 && systemctl restart terezia-api"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        results["steps"].append(
            {
                "step": "systemctl restart",
                "success": True,
                "output": "Restart agendado (2s delay)",
            }
        )

        logger.info("Deploy concluído com sucesso - restart agendado")
        return {
            "status": "success",
            "message": "Deploy realizado com sucesso. Serviço reiniciando em 2s.",
            **results,
        }

    except subprocess.TimeoutExpired as e:
        logger.error(f"Deploy timeout: {e}")
        raise HTTPException(status_code=500, detail=f"Timeout: {e}")
    except Exception as e:
        logger.error(f"Deploy falhou: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
            headers={"X-Deploy-Steps": str(results)},
        )
