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
    python scripts/smoke_tests.py --env prod --tenant-id prefeitura-vila-serena --tenant-manifest tenants/prefeitura-vila-serena/tenant.json --phase-report fase8

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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.demo_tenant_service import ControlledRetrievalCheck, DemoTenantService


BASE_URL: str = "http://127.0.0.1:8000"
DEFAULT_TENANT_ID: str = "prefeitura-demo"
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
    tenant_id: str
    tenant_manifest: str | None = None
    phase_report: str = "fase7"
    print_json: bool = False
    json_out: str | None = None
    results: list[TestResult] = field(default_factory=list)
    bundle_validation: dict[str, Any] | None = None
    managerial_report: dict[str, Any] | None = None
    empty_state_validation: dict[str, Any] | None = None
    ingest_validation: dict[str, Any] | None = None
    controlled_retrieval_report: dict[str, Any] | None = None

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


def _bundle_service(context: TestContext) -> DemoTenantService:
    if not context.tenant_manifest:
        raise RuntimeError("tenant_manifest não informado.")
    return DemoTenantService()


def _controlled_checks(context: TestContext) -> list[ControlledRetrievalCheck]:
    if not context.tenant_manifest:
        return []
    return _bundle_service(context).load_retrieval_checks(context.tenant_manifest)


def _default_rag_question(context: TestContext) -> str:
    checks = _controlled_checks(context)
    if context.phase_report == "fase8" and checks:
        return checks[0].question
    return "horario do alvara"


def _default_chat_check(context: TestContext) -> ControlledRetrievalCheck | None:
    checks = _controlled_checks(context)
    if not checks:
        return None
    for check in checks:
        if check.use_in_chat:
            return check
    return checks[0]


def _build_phase_report(context: TestContext) -> dict[str, Any] | None:
    if not context.tenant_manifest:
        return None

    service = _bundle_service(context)
    if context.phase_report == "fase8":
        return service.build_phase8_managerial_report(
            context.tenant_manifest,
            runtime_validation={
                "empty_state_validation": context.empty_state_validation or {
                    "ok": False,
                    "evidence": "validacao de base vazia nao executada",
                },
                "ingest_validation": context.ingest_validation or {
                    "ok": False,
                    "evidence": "ingest nao executada",
                },
                "retrieval_validation": context.controlled_retrieval_report or {
                    "ok": False,
                    "evidence": "retrieval controlado nao executado",
                },
            },
        )

    return service.build_managerial_report(context.tenant_manifest)


def validate_tenant_bundle(context: TestContext) -> None:
    """
    Valida o bundle versionado do tenant demonstrativo e gera relatorio gerencial.
    """
    if not context.tenant_manifest:
        return

    service = _bundle_service(context)
    if context.phase_report == "fase8":
        report = service.validate_knowledge_base_bundle(context.tenant_manifest)
        nome = "Bundle da base documental"
        explicacao = (
            "Confirma documentos ficticios, organizacao da base e cobertura tematica minima da prefeitura ficticia."
        )
    else:
        report = service.build_managerial_report(context.tenant_manifest)
        nome = "Bundle do tenant demonstrativo"
        explicacao = (
            "Confirma nome, identidade, configuracao, escopo e estrutura inicial do tenant ficticio."
        )

    context.bundle_validation = report

    ok = report["status"] == "passed"
    details_lines = [
        f"Tenant: {report['tenant_id']}",
        f"Cliente: {report['client_name']}",
        (
            f"Criterios aprovados: {report['criteria_passed']}/{report['criteria_total']}"
            if "criteria_passed" in report
            else f"Criterios estruturais: {sum(1 for item in report['criteria'] if item['ok'])}/{len(report['criteria'])}"
        ),
    ]
    for criterion in report["criteria"]:
        status = "OK" if criterion["ok"] else "ERR"
        details_lines.append(f"- [{status}] {criterion['criterion']} | {criterion['evidence']}")

    record_step(
        context=context,
        nome=nome,
        ok=ok,
        explicacao=explicacao,
        detalhes="\n".join(details_lines),
    )
    if not ok:
        raise RuntimeError("Bundle do tenant demonstrativo invalido.")


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
    status, payload = http_request("GET", f"/api/rag/status?tenant_id={context.tenant_id}")
    ok = (
        status == 200
        and isinstance(payload, dict)
        and payload.get("ready") is False
        and payload.get("documents_count") == 0
    )
    context.empty_state_validation = {
        "ok": ok,
        "evidence": (
            f"ready={payload.get('ready') if isinstance(payload, dict) else 'n/a'} | "
            f"documents_count={payload.get('documents_count') if isinstance(payload, dict) else 'n/a'} | "
            f"message={payload.get('message') if isinstance(payload, dict) else payload}"
        ),
    }

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
    Cria a base documental de teste.
    """
    payloads: list[dict[str, Any]]
    if context.tenant_manifest:
        service = _bundle_service(context)
        payloads = [
            {
                "tenant_id": context.tenant_id,
                "title": document.title,
                "content": document.content,
                "keywords": document.keywords,
                "intents": document.intents,
            }
            for document in service.list_source_documents(context.tenant_manifest)
        ]
    else:
        payloads = [
            {
                "tenant_id": context.tenant_id,
                "title": "Atendimento Alvara",
                "content": (
                    "O setor de alvara atende das 8h as 17h.\n\n"
                    "Documentos podem ser protocolados ate as 16h."
                ),
                "keywords": ["alvara", "horario"],
                "intents": ["INFO_REQUEST"],
            }
        ]

    responses: list[dict[str, Any] | str] = []
    ok = True
    for payload in payloads:
        status, response = http_request("POST", "/api/rag/documents", payload)
        responses.append(response)
        if not (
            status in {200, 201}
            and isinstance(response, dict)
            and response.get("tenant_id") == context.tenant_id
        ):
            ok = False

    record_step(
        context=context,
        nome="Criação da base documental",
        ok=ok,
        explicacao="Cria os documentos iniciais do tenant para validar ingest e retrieval.",
        detalhes=pretty_json(
            {
                "tenant_id": context.tenant_id,
                "documents_created": len(payloads),
                "titles": [payload["title"] for payload in payloads],
                "responses": responses,
            }
        ),
    )
    if not ok:
        raise RuntimeError("Falha ao criar a base documental.")


def ingest_documents(context: TestContext) -> None:
    """
    Executa ingest do tenant.
    """
    payload = {
        "tenant_id": context.tenant_id,
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
    context.ingest_validation = {
        "ok": (
            ok
            and isinstance(response, dict)
            and context.tenant_id in str(response.get("source_dir", ""))
            and context.tenant_id.replace("-", "_") in str(response.get("collection_name", ""))
        ),
        "evidence": (
            f"collection={response.get('collection_name') if isinstance(response, dict) else 'n/a'} | "
            f"source_dir={response.get('source_dir') if isinstance(response, dict) else 'n/a'} | "
            f"documents={response.get('documents_count') if isinstance(response, dict) else 'n/a'} | "
            f"chunks={response.get('chunks_count') if isinstance(response, dict) else 'n/a'}"
        ),
    }

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
        "tenant_id": context.tenant_id,
        "query": _default_rag_question(context),
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


def validate_controlled_retrievals(context: TestContext) -> None:
    """
    Executa perguntas controladas de retrieval definidas no bundle da fase.
    """
    if context.phase_report != "fase8" or not context.tenant_manifest:
        return

    checks = _controlled_checks(context)
    if not checks:
        context.controlled_retrieval_report = {
            "ok": False,
            "evidence": "nenhuma pergunta controlada configurada no bundle",
            "checks": [],
        }
        raise RuntimeError("Bundle sem perguntas controladas de retrieval.")

    check_results: list[dict[str, Any]] = []
    passed = 0
    for check in checks:
        status, response = http_request(
            "POST",
            "/api/rag/query",
            {
                "tenant_id": context.tenant_id,
                "query": check.question,
                "top_k": 8,
                "min_score": 0.1,
                "boost_enabled": False,
            },
        )
        matched_chunk: dict[str, Any] | None = None
        if status == 200 and isinstance(response, dict):
            for chunk in response.get("chunks", []):
                title = str(chunk.get("title", "")).lower()
                text = str(chunk.get("text", "")).lower()
                if (
                    check.expected_title_contains.lower() in title
                    and all(term.lower() in text for term in check.expected_terms)
                ):
                    matched_chunk = chunk
                    break

        ok = matched_chunk is not None
        if ok:
            passed += 1

        check_results.append(
            {
                "id": check.id,
                "question": check.question,
                "ok": ok,
                "matched_title": matched_chunk.get("title") if matched_chunk else None,
                "expected_title_contains": check.expected_title_contains,
                "expected_terms": check.expected_terms,
            }
        )

    total = len(check_results)
    overall_ok = passed == total
    context.controlled_retrieval_report = {
        "ok": overall_ok,
        "passed": passed,
        "total": total,
        "evidence": f"checks_passed={passed}/{total}",
        "checks": check_results,
    }

    record_step(
        context=context,
        nome="Retrieval controlado",
        ok=overall_ok,
        explicacao="Valida perguntas controladas contra a base ficticia apos a ingest limpa.",
        detalhes=pretty_json(context.controlled_retrieval_report),
    )
    if not overall_ok:
        raise RuntimeError("Falha na validacao controlada de retrieval.")


def query_chat(context: TestContext) -> None:
    """
    Consulta o endpoint principal de chat.
    """
    chat_check = _default_chat_check(context)
    payload = {
        "tenant_id": context.tenant_id,
        "message": (
            chat_check.question
            if context.phase_report == "fase8" and chat_check is not None
            else (
                "O assistente emite protocolo?"
                if context.tenant_manifest
                else "Qual o horario do alvara?"
            )
        ),
    }
    status, response = http_request("POST", "/api/chat", payload)
    ok = (
        status == 200
        and isinstance(response, dict)
        and response.get("tenant_id") == context.tenant_id
        and isinstance(response.get("message"), str)
        and len(response["message"]) > 0
    )
    if ok and context.phase_report == "fase8" and chat_check is not None and chat_check.chat_expected_terms:
        lower_message = response["message"].lower()
        ok = all(term.lower() in lower_message for term in chat_check.chat_expected_terms)

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
        "tenant_id": context.tenant_id,
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
        "tenant_id": context.tenant_id,
        "tenant_manifest": context.tenant_manifest,
        "phase_report": context.phase_report,
        "container_name": context.container_name,
        "total_steps": total,
        "successes": success,
        "failures": failed,
        "status": "passed" if failed == 0 else "failed",
        "results": [asdict(result) for result in context.results],
        "managerial_report": _build_phase_report(context),
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

    if summary["managerial_report"]:
        report = summary["managerial_report"]
        print("RELATORIO GERENCIAL")
        print(f"Fase: {report['phase']}")
        print(f"Tenant: {report['tenant_id']}")
        print(f"Status: {report['status']}")
        print(f"Criterios aprovados: {report['criteria_passed']}/{report['criteria_total']}")
        for criterion in report["criteria"]:
            icon = "OK " if criterion["ok"] else "ERR"
            print(f"- [{icon}] {criterion['criterion']}")
            print(f"  Evidencia: {criterion['evidence']}")
        print()

    if summary["status"] == "passed":
        print("Resultado geral: ✅ SMOKE TEST APROVADO")
        print("Leitura humana: o backend subiu, respondeu health, tratou base vazia,")
        if context.phase_report == "fase8":
            print("ingeriu a base ficticia, validou retrieval controlado e respondeu no fluxo principal.")
        else:
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
            tenant_id=args.tenant_id,
            tenant_manifest=args.tenant_manifest,
            phase_report=args.phase_report,
            print_json=args.json,
            json_out=args.json_out,
        )

    return TestContext(
        env=args.env,
        compose_files=["docker-compose.yml", "docker-compose.local.yml"],
        container_name="chat-pref-api-dev",
        tenant_id=args.tenant_id,
        tenant_manifest=args.tenant_manifest,
        phase_report=args.phase_report,
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
    parser.add_argument(
        "--tenant-id",
        type=str,
        default=DEFAULT_TENANT_ID,
        help="Tenant usado no fluxo ponta a ponta.",
    )
    parser.add_argument(
        "--tenant-manifest",
        type=str,
        default=None,
        help="Caminho do bundle versionado do tenant demonstrativo para validar e materializar no smoke.",
    )
    parser.add_argument(
        "--phase-report",
        choices=["fase7", "fase8"],
        default="fase7",
        help="Fase cujos criterios de aceite devem ser consolidados no relatorio gerencial.",
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
        validate_tenant_bundle(context)
        docker_up(context)
        wait_for_health(context)
        test_root(context)
        test_health(context)
        test_rag_empty(context)
        create_document(context)
        ingest_documents(context)
        query_rag(context)
        validate_controlled_retrievals(context)
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
