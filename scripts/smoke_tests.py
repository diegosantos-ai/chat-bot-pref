#!/usr/bin/env python3
"""
Script de smoke tests do projeto Chat Pref.

Executa validações ponta a ponta do ambiente Docker local,
incluindo subida da API, healthcheck, fluxo mínimo de RAG,
chat e reset da base documental.

Exemplos:
    python scripts/smoke_tests.py --env prod
    python scripts/smoke_tests.py --env prod --json
    python scripts/smoke_tests.py --env prod --json-out artifacts/smoke-prod.json
    python scripts/smoke_tests.py --env dev --json --json-out artifacts/smoke-dev.json

Requisitos:
    - Docker e Docker Compose disponíveis
    - API configurada para expor a porta 8000 localmente
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


BASE_URL: str = "http://127.0.0.1:8000"
TENANT_ID: str = "prefeitura-demo"
TIMEOUT_SECONDS: int = 10
HEALTH_WAIT_SECONDS: int = 60


@dataclass
class TestResult:
    """
    Representa o resultado de uma etapa de teste.
    """

    nome: str
    ok: bool
    explicacao: str
    detalhes: str = ""


@dataclass
class TestContext:
    """
    Contexto compartilhado entre os testes.
    """

    env: str
    compose_files: list[str]
    container_name: str
    print_json: bool = False
    json_out: str | None = None
    results: list[TestResult] = field(default_factory=list)

    def add_result(self, result: TestResult) -> None:
        """
        Adiciona um resultado à lista consolidada.

        Args:
            result: Resultado de teste executado.
        """
        self.results.append(result)

    @property
    def failed(self) -> bool:
        """
        Indica se houve alguma falha.

        Returns:
            True se ao menos um teste falhou.
        """
        return any(not result.ok for result in self.results)


def run_command(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """
    Executa um comando shell e retorna o resultado.

    Args:
        command: Lista com comando e argumentos.
        check: Se True, lança exceção em caso de erro.

    Returns:
        Resultado do subprocesso.
    """
    return subprocess.run(
        command,
        check=check,
        text=True,
        capture_output=True,
    )


def http_request(
    method: str,
    path: str,
    data: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any] | str]:
    """
    Executa uma requisição HTTP simples e tenta parsear JSON.

    Args:
        method: Método HTTP.
        path: Caminho relativo da API.
        data: Payload JSON opcional.

    Returns:
        Tupla contendo status code e resposta JSON ou texto.
    """
    url = f"{BASE_URL}{path}"
    body: bytes | None = None
    headers = {"Content-Type": "application/json"}

    if data is not None:
        body = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
            try:
                return response.status, json.loads(raw)
            except json.JSONDecodeError:
                return response.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
        return exc.code, parsed


def pretty_json(data: Any) -> str:
    """
    Formata estrutura em JSON legível.

    Args:
        data: Estrutura serializável.

    Returns:
        String formatada.
    """
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except TypeError:
        return str(data)


def record_step(
    context: TestContext,
    nome: str,
    ok: bool,
    explicacao: str,
    detalhes: str = "",
) -> None:
    """
    Registra e imprime o resultado de uma etapa.

    Args:
        context: Contexto da execução.
        nome: Nome curto da etapa.
        ok: Indicador de sucesso.
        explicacao: Explicação humana do que a etapa valida.
        detalhes: Detalhes técnicos adicionais.
    """
    icon = "✅" if ok else "❌"
    print(f"{icon} {nome}")
    print(f"   {explicacao}")
    if detalhes:
        for line in detalhes.strip().splitlines():
            print(f"   {line}")
    print()
    context.add_result(
        TestResult(
            nome=nome,
            ok=ok,
            explicacao=explicacao,
            detalhes=detalhes,
        )
    )


def docker_up(context: TestContext) -> None:
    """
    Sobe o ambiente Docker.
    """
    command = ["docker", "compose"]
    for compose_file in context.compose_files:
        command.extend(["-f", compose_file])
    command.extend(["up", "-d", "--build"])

    result = run_command(command)
    record_step(
        context=context,
        nome="Subida do ambiente",
        ok=True,
        explicacao="Os containers foram criados/inicializados com sucesso.",
        detalhes=result.stdout.strip(),
    )


def wait_for_health(context: TestContext) -> None:
    """
    Aguarda o container ficar healthy.
    """
    start = time.time()

    while time.time() - start < HEALTH_WAIT_SECONDS:
        result = run_command(
            [
                "docker",
                "inspect",
                "-f",
                "{{.State.Health.Status}}",
                context.container_name,
            ],
            check=False,
        )

        status = result.stdout.strip()
        if status == "healthy":
            record_step(
                context=context,
                nome="Healthcheck do container",
                ok=True,
                explicacao="A API ficou saudável dentro do tempo esperado.",
                detalhes=f"Container: {context.container_name} | Health: healthy",
            )
            return

        time.sleep(1)

    record_step(
        context=context,
        nome="Healthcheck do container",
        ok=False,
        explicacao="A API não ficou saudável dentro do tempo limite.",
        detalhes=f"Container: {context.container_name}",
    )
    raise RuntimeError("Container não ficou healthy no tempo esperado.")


def test_root(context: TestContext) -> None:
    """
    Valida endpoint raiz.
    """
    status, payload = http_request("GET", "/")
    ok = status == 200 and isinstance(payload, dict) and bool(payload.get("message"))

    record_step(
        context=context,
        nome="GET /",
        ok=ok,
        explicacao="Confirma que a API está no ar e responde metadados básicos.",
        detalhes=pretty_json(payload),
    )
    if not ok:
        raise RuntimeError("Falha no endpoint raiz.")


def test_health(context: TestContext) -> None:
    """
    Valida endpoint de health.
    """
    status, payload = http_request("GET", "/health")
    ok = status == 200 and isinstance(payload, dict) and payload.get("status") == "healthy"

    record_step(
        context=context,
        nome="GET /health",
        ok=ok,
        explicacao="Confirma que o backend reporta estado saudável para uso operacional.",
        detalhes=pretty_json(payload),
    )
    if not ok:
        raise RuntimeError("Falha no health endpoint.")


def test_rag_empty(context: TestContext) -> None:
    """
    Valida comportamento sem base carregada.
    """
    status, payload = http_request("GET", f"/api/rag/status?tenant_id={TENANT_ID}")
    ok = (
        status == 200
        and isinstance(payload, dict)
        and payload.get("ready") is False
        and payload.get("documents_count") == 0
    )

    record_step(
        context=context,
        nome="RAG vazio",
        ok=ok,
        explicacao="Confirma que o sistema trata explicitamente a ausência de base documental.",
        detalhes=pretty_json(payload),
    )
    if not ok:
        raise RuntimeError("Estado inicial do RAG não corresponde ao esperado.")


def create_document(context: TestContext) -> None:
    """
    Cria documento de teste.
    """
    payload = {
        "tenant_id": TENANT_ID,
        "title": "Atendimento Alvara",
        "content": (
            "O setor de alvara atende das 8h as 17h.\n\n"
            "Documentos podem ser protocolados ate as 16h."
        ),
        "keywords": ["alvara", "horario"],
        "intents": ["INFO_REQUEST"],
    }
    status, response = http_request("POST", "/api/rag/documents", payload)
    ok = status in {200, 201} and isinstance(response, dict) and response.get("tenant_id") == TENANT_ID

    record_step(
        context=context,
        nome="Criação de documento",
        ok=ok,
        explicacao="Cria uma base mínima de conhecimento para validar ingest e retrieval.",
        detalhes=pretty_json(response),
    )
    if not ok:
        raise RuntimeError("Falha ao criar documento.")


def ingest_documents(context: TestContext) -> None:
    """
    Executa ingest do tenant.
    """
    payload = {
        "tenant_id": TENANT_ID,
        "reset_collection": True,
    }
    status, response = http_request("POST", "/api/rag/ingest", payload)
    ok = (
        status == 200
        and isinstance(response, dict)
        and response.get("ready") is True
        and response.get("documents_count", 0) >= 1
        and response.get("chunks_count", 0) >= 1
    )

    record_step(
        context=context,
        nome="Ingest da base",
        ok=ok,
        explicacao="Transforma o documento salvo em chunks recuperáveis no RAG.",
        detalhes=pretty_json(response),
    )
    if not ok:
        raise RuntimeError("Falha na ingestão.")


def query_rag(context: TestContext) -> None:
    """
    Consulta diretamente o RAG.
    """
    payload = {
        "tenant_id": TENANT_ID,
        "query": "horario do alvara",
    }
    status, response = http_request("POST", "/api/rag/query", payload)
    ok = (
        status == 200
        and isinstance(response, dict)
        and response.get("status") == "ready"
        and response.get("total_chunks", 0) >= 1
    )

    record_step(
        context=context,
        nome="Consulta direta ao RAG",
        ok=ok,
        explicacao="Valida que a recuperação semântica encontra contexto útil para a pergunta.",
        detalhes=pretty_json(response),
    )
    if not ok:
        raise RuntimeError("Falha na consulta RAG.")


def query_chat(context: TestContext) -> None:
    """
    Consulta o endpoint principal de chat.
    """
    payload = {
        "tenant_id": TENANT_ID,
        "message": "Qual o horario do alvara?",
    }
    status, response = http_request("POST", "/api/chat", payload)
    ok = (
        status == 200
        and isinstance(response, dict)
        and response.get("tenant_id") == TENANT_ID
        and isinstance(response.get("message"), str)
        and len(response["message"]) > 0
    )

    record_step(
        context=context,
        nome="Consulta no /api/chat",
        ok=ok,
        explicacao="Valida o fluxo principal de atendimento usando tenant e contexto recuperado.",
        detalhes=pretty_json(response),
    )
    if not ok:
        raise RuntimeError("Falha no endpoint de chat.")


def reset_rag(context: TestContext) -> None:
    """
    Reseta a base do tenant.
    """
    payload = {
        "tenant_id": TENANT_ID,
        "purge_documents": True,
        "remove_legacy_collections": True,
    }
    status, response = http_request("POST", "/api/rag/reset", payload)
    ok = status == 200 and isinstance(response, dict)

    record_step(
        context=context,
        nome="Reset da base",
        ok=ok,
        explicacao="Limpa a collection e os documentos do tenant de teste.",
        detalhes=pretty_json(response),
    )
    if not ok:
        raise RuntimeError("Falha no reset do RAG.")


def docker_down(context: TestContext) -> None:
    """
    Derruba o ambiente Docker.
    """
    command = ["docker", "compose"]
    for compose_file in context.compose_files:
        command.extend(["-f", compose_file])
    command.extend(["down", "-v"])

    result = run_command(command, check=False)
    ok = result.returncode == 0

    record_step(
        context=context,
        nome="Encerramento do ambiente",
        ok=ok,
        explicacao="Finaliza os containers e remove volumes do teste.",
        detalhes=result.stdout.strip() or result.stderr.strip(),
    )


def build_summary(context: TestContext) -> dict[str, Any]:
    """
    Monta o resumo estruturado da execução.

    Args:
        context: Contexto da execução.

    Returns:
        Dicionário serializável com o resumo final.
    """
    total = len(context.results)
    success = sum(1 for result in context.results if result.ok)
    failed = total - success

    return {
        "env": context.env,
        "base_url": BASE_URL,
        "tenant_id": TENANT_ID,
        "container_name": context.container_name,
        "total_steps": total,
        "successes": success,
        "failures": failed,
        "status": "passed" if failed == 0 else "failed",
        "results": [asdict(result) for result in context.results],
    }


def print_summary(context: TestContext) -> dict[str, Any]:
    """
    Exibe resumo consolidado da execução e retorna a versão estruturada.

    Args:
        context: Contexto da execução.

    Returns:
        Resumo estruturado da execução.
    """
    summary = build_summary(context)

    print("=" * 72)
    print("RESUMO FINAL")
    print("=" * 72)
    print(f"Ambiente: {summary['env']}")
    print(f"Total de etapas: {summary['total_steps']}")
    print(f"Sucessos: {summary['successes']}")
    print(f"Falhas: {summary['failures']}")
    print()

    if summary["status"] == "passed":
        print("Resultado geral: ✅ SMOKE TEST APROVADO")
        print("Leitura humana: o backend subiu, respondeu health, tratou base vazia,")
        print("ingeriu documento, recuperou contexto e respondeu no fluxo principal.")
    else:
        print("Resultado geral: ❌ SMOKE TEST COM FALHAS")
        print("Leitura humana: pelo menos uma etapa crítica do fluxo quebrou.")
        print("As falhas acima mostram exatamente em qual ponto o bicho tropeçou.")

    print()
    print("Checklist das etapas:")
    for result in context.results:
        icon = "OK " if result.ok else "ERR"
        print(f"- [{icon}] {result.nome}")

    print()

    if context.print_json:
        print("=" * 72)
        print("JSON")
        print("=" * 72)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print()

    if context.json_out:
        output_path = Path(context.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Arquivo JSON salvo em: {output_path}")

    return summary


def build_context(args: argparse.Namespace) -> TestContext:
    """
    Monta o contexto com base nos argumentos recebidos.

    Args:
        args: Argumentos de linha de comando.

    Returns:
        Contexto configurado.
    """
    if args.env == "prod":
        return TestContext(
            env=args.env,
            compose_files=["docker-compose.yml"],
            container_name="chat-pref-api",
            print_json=args.json,
            json_out=args.json_out,
        )

    return TestContext(
        env=args.env,
        compose_files=["docker-compose.yml", "docker-compose.local.yml"],
        container_name="chat-pref-api-dev",
        print_json=args.json,
        json_out=args.json_out,
    )


def parse_args() -> argparse.Namespace:
    """
    Faz parse dos argumentos de linha de comando.

    Returns:
        Namespace com argumentos.
    """
    parser = argparse.ArgumentParser(description="Executa smoke tests do Chat Pref.")
    parser.add_argument(
        "--env",
        choices=["prod", "dev"],
        default="prod",
        help="Ambiente Docker a validar.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime o resumo final também em JSON no stdout.",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default=None,
        help="Salva o resumo final em um arquivo JSON.",
    )
    return parser.parse_args()


def main() -> int:
    """
    Fluxo principal da execução.

    Returns:
        Código de saída do processo.
    """
    args = parse_args()
    context = build_context(args)

    try:
        docker_up(context)
        wait_for_health(context)
        test_root(context)
        test_health(context)
        test_rag_empty(context)
        create_document(context)
        ingest_documents(context)
        query_rag(context)
        query_chat(context)
        reset_rag(context)
        return_code = 0
    except Exception as exc:
        record_step(
            context=context,
            nome="Execução interrompida",
            ok=False,
            explicacao="O fluxo foi interrompido por uma falha em etapa crítica.",
            detalhes=str(exc),
        )
        return_code = 1
    finally:
        docker_down(context)
        print_summary(context)

    return return_code


if __name__ == "__main__":
    sys.exit(main())