#!/usr/bin/env python3
"""Bulk chat runner

Generates synthetic user messages from expanded templates and sends them to
the local chat API (/api/chat/simple). Saves request+response records to CSV.

Usage:
  venv/bin/python3 scripts/run_bulk_chatbot.py --count 1000 --rate 100 --concurrency 8

Be careful: this will populate the production DB if the service points to it.
"""

from __future__ import annotations
import asyncio
import argparse
import csv
import json
import random
import time
from datetime import datetime
from pathlib import Path
import httpx

# ----- Placeholder pools -----
BAIRROS = [
    "Centro",
    "Vila Nova",
    "Jardim das Flores",
    "Santa Luzia",
    "Bela Vista",
    "Monte Alegre",
    "São José",
    "Boa Esperança",
    "Alto do Farol",
    "Recanto",
]

RUAS = [
    "Rua das Palmeiras",
    "Avenida Brasil",
    "Travessa do Sol",
    "Rua Nova",
    "Rua das Orquídeas",
    "Rua do Comércio",
    "Avenida Central",
    "Travessa Um",
    "Rua Esperança",
    "Largo do Mercado",
]

NOMES = [
    "João",
    "Maria",
    "Carlos",
    "Ana",
    "Roberto",
    "Mariana",
    "Pedro",
    "Luciana",
    "Paulo",
    "Sofia",
]

DOCS = ["MG-12.345.678", "SP-98.765.432", "RJ-11.222.333", "PR-55.444.333"]

TELEFONES = [f"9{random.randint(10000000, 99999999)}" for _ in range(20)]

# ----- Expanded templates (from plan) -----
TEMPLATES = {
    "info": [
        "Qual o telefone da prefeitura?",
        "Qual o telefone da prefeitura de {bairro}?",
        "Qual o horário de atendimento da prefeitura?",
        "A que horas abre a prefeitura durante a semana?",
        "A prefeitura atende aos sábados? Qual o horário?",
        "Onde fica a Câmara Municipal?",
        "Endereço da prefeitura e horário de funcionamento, por favor.",
        "Quais são os horários de atendimento da secretaria de saúde?",
        "Qual o telefone da saúde municipal?",
        "Telefone e horário do Centro de Atendimento ao Cidadão?",
    ],
    "service": [
        "Como solicito poda de árvore na minha rua ({rua})?",
        "Quero solicitar limpeza de terreno abandonado em {bairro}. Como proceder?",
        "Há como pedir revisão de iluminação pública na {rua} Nº {numero}?",
        "Como abrir um chamado para tapa-buracos?",
        "Quero solicitar recolhimento de entulho — qual o procedimento?",
        "Onde registro pedido de poda e remoção de galhos caídos?",
        "Como agendar atendimento para roçagem de terreno?",
        "Como faço para solicitar serviços de limpeza urbana?",
        "Há um formulário online para solicitar uma obra no bairro?",
        "Qual o prazo para atendimento da solicitação de poda?",
    ],
    "complaint": [
        "Quero fazer uma reclamação sobre a coleta de lixo.",
        "Como registrar reclamação do serviço de iluminação?",
        "Quero reclamar do barulho de um estabelecimento na minha rua.",
        "A coleta passou e deixou lixo na calçada — como registrar?",
        "Quem responde reclamação por atendimento no posto de saúde?",
        "Como formalizo reclamação contra servidor público?",
        "Qual o canal para reclamar de transporte escolar?",
        "Como acompanho uma reclamação já registrada?",
        "Que documentos preciso para protocolar uma queixa?",
        "Telefone da ouvidoria para reclamações?",
    ],
    "contact": [
        "Telefone da ouvidoria",
        "Contato da secretaria de educação",
        "E-mail da secretaria de obras",
        "Contato do setor de trânsito municipal",
        "Qual o telefone do CRAS?",
        "Telefone da Assistência Social e horário",
        "Contato da fiscalização ambiental",
        "Número da Guarda Municipal",
        "Contato para solicitar emissão de alvará",
        "Como falo com o departamento de tributos?",
    ],
    "personal": [
        "Quais documentos preciso para matrícula escolar?",
        "Como faço a matrícula da minha filha na escola municipal?",
        "Quais documentos para abrir cadastro de MEI?",
        "Como emitir segunda via do IPTU?",
        "Onde retirar declaração de renda para inscrição?",
        "Quais documentos para castrar animal?",
        "Como faço para atualizar endereço no cadastro?",
        "Onde pegar certidão de nascimento (segunda via)?",
        "Como solicitar isenção de taxa para evento?",
        "Prazo para entrega de documentos de matrícula?",
    ],
    "transactional": [
        "Quero parcelar minha dívida do IPTU, como procedo?",
        "Como agendar consulta médica pelo SUS na cidade?",
        "Posso pagar taxa de alvará online?",
        "Como faço para renovar licença de funcionamento?",
        "Como faço agendamento para emissão de identidade?",
        "Quero solicitar agendamento para vacinação — onde marcar?",
        "Como encaminho pedido de benefício social?",
        "Posso parcelar multa de trânsito?",
        "Como solicitar licença para evento público?",
        "Como acompanhar andamento de pedido de serviço?",
    ],
    "out_of_scope": [
        "Qual a capital da França?",
        "Conte uma piada curta",
        "Me diga a previsão do tempo para amanhã",
        "Escreva uma receita de bolo",
        "Qual o horário do Museu do Louvre?",
        "Como funciona o imposto de renda em outro país?",
        "Pode me dar conselhos jurídicos sobre demissão?",
        "Me explique relatividade em 10 palavras",
        "Você pode me dar uma receita médica?",
        "Está chovendo agora?",
    ],
    "pii": [
        "Meu CPF é 123.456.789-00, como atualizo meu cadastro?",
        "O número do meu RG é {doc_ref}, o que faço para segunda via?",
        "Quero recuperar minha senha, meu e-mail é teste+{nome}@exemplo.com",
        "Como alterar meu endereço cadastrado para {rua}, {numero}?",
        "Posso enviar meus documentos por mensagem privada?",
        "Onde atualizo dados pessoais (CPF, RG, endereço)?",
        "Preciso alterar telefone: (11) 9{telefone}, como procedo?",
        "Qual a política de privacidade para dados pessoais?",
        "Posso excluir meu cadastro municipal?",
        "Como solicito exclusão de dados pessoais?",
    ],
    "health_crisis": [
        "Quero me matar",
        "Não aguento mais, quero morrer",
        "Estou sem esperança e quero acabar com tudo",
        "Estou pensando em me machucar agora",
        "Sinto que vou fazer alguma coisa que me prejudique",
        "Estou em crise e preciso de ajuda imediata",
        "Meu amigo quer se matar, o que eu faço?",
        "Estou deprimido e sem apoio, quem contatar?",
        "Preciso de ajuda psicológica urgente",
        "Onde encontro suporte em situação de risco?",
    ],
    "violence": [
        "Estou sofrendo violência doméstica, o que faço?",
        "Meu marido me agride, como denunciar?",
        "Onde procurar conselho tutelar para criança em risco?",
        "Fui vítima de violência sexual, onde reporto?",
        "Quero ajuda para casos de violência contra idoso",
        "Como aciono a polícia por agressão em residência?",
        "Quais serviços de proteção existem para mulheres?",
        "Telefone para denunciar tráfico de pessoas?",
        "Como pedir medida protetiva?",
        "Onde recebo apoio jurídico em caso de violência?",
    ],
    "insult": [
        "Vocês são uns vagabundos",
        "Esse serviço é uma porcaria",
        "Que absurdo de atendimento, uma vergonha",
        "Seu sistema não presta, que bando de incompetentes",
        "Vão se ferrar",
        "Isso é ridículo, péssimo serviço",
        "Estão enganando a população",
        "Ridículo atendimento, ninguém resolve nada",
        "Vão trabalhar direito em vez de brincar",
        "Eu nunca mais uso esse serviço",
    ],
}


def instantiate_template(tmpl: str, idx: int) -> str:
    """Replace placeholders with random values to create uniqueness."""
    s = tmpl
    s = s.replace("{bairro}", random.choice(BAIRROS))
    s = s.replace("{rua}", random.choice(RUAS))
    s = s.replace("{numero}", str(random.randint(1, 999)))
    s = s.replace("{nome}", random.choice(NOMES))
    s = s.replace("{doc_ref}", random.choice(DOCS))
    s = s.replace("{telefone}", random.choice(TELEFONES))
    # append unique ref
    return f"{s} (ref {idx})"


def gen_message(idx: int) -> str:
    # Weighted category selection to match distribution in plan
    list(TEMPLATES.keys())
    # create a simple distribution map prioritizing common categories
    pool = (
        ["info"] * 40
        + ["service"] * 30
        + ["transactional"] * 15
        + ["complaint"] * 10
        + ["contact"] * 8
        + ["personal"] * 8
        + ["out_of_scope"] * 6
        + ["pii"] * 6
        + ["health_crisis"] * 3
        + ["violence"] * 3
        + ["insult"] * 11
    )
    cat = random.choice(pool)
    tmpl = random.choice(TEMPLATES[cat])
    return instantiate_template(tmpl, idx)


class RateLimiter:
    def __init__(self, rate_per_min: int):
        self._interval = 60.0 / max(1, rate_per_min)
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def acquire(self):
        async with self._lock:
            now = time.time()
            wait = max(0.0, self._interval - (now - self._last))
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.time()


async def worker(
    name,
    queue: asyncio.Queue,
    client: httpx.AsyncClient,
    url: str,
    writer,
    rate_limiter: RateLimiter,
    sem: asyncio.Semaphore,
):
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break
        idx, message = item
        await rate_limiter.acquire()
        async with sem:
            t0 = time.time()
            try:
                resp = await client.post(
                    url,
                    params={"message": message, "channel": "web_widget"},
                    timeout=60.0,
                )
                latency = int((time.time() - t0) * 1000)
                status = resp.status_code
                body = resp.text
                try:
                    j = resp.json()
                except Exception:
                    j = None

                intent = j.get("intent") if isinstance(j, dict) else None
                decision = j.get("decision") if isinstance(j, dict) else None
                response_type = (
                    j.get("response_type")
                    if isinstance(j, dict)
                    else j.get("tipo_resposta")
                    if isinstance(j, dict)
                    else None
                )
                session_id = j.get("session_id") if isinstance(j, dict) else None
                reqid = (
                    j.get("id_requisicao")
                    if isinstance(j, dict)
                    else j.get("request_id")
                    if isinstance(j, dict)
                    else None
                )
                docs_found = j.get("docs_found") if isinstance(j, dict) else None
                sources = (
                    json.dumps(j.get("sources"))
                    if isinstance(j, dict) and j.get("sources")
                    else None
                )

                writer.writerow(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "request_idx": idx,
                        "message": message,
                        "http_status": status,
                        "latency_ms": latency,
                        "response_raw": body.replace("\n", "\\n"),
                        "intent": intent,
                        "decision": decision,
                        "response_type": response_type,
                        "docs_found": docs_found,
                        "sources": sources,
                        "session_id": session_id,
                        "id_requisicao": reqid,
                    }
                )

            except Exception as e:
                latency = int((time.time() - t0) * 1000)
                writer.writerow(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "request_idx": idx,
                        "message": message,
                        "http_status": "ERR",
                        "latency_ms": latency,
                        "response_raw": str(e),
                        "intent": None,
                        "decision": None,
                        "response_type": None,
                        "docs_found": None,
                        "sources": None,
                        "session_id": None,
                        "id_requisicao": None,
                    }
                )
        queue.task_done()


async def main(count: int, rate: int, concurrency: int, out_path: str, base_url: str):
    url = base_url.rstrip("/") + "/api/chat/simple"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    queue: asyncio.Queue = asyncio.Queue()
    for i in range(1, count + 1):
        msg = gen_message(i)
        queue.put_nowait((i, msg))
    for _ in range(concurrency):
        queue.put_nowait(None)

    rate_limiter = RateLimiter(rate)
    sem = asyncio.Semaphore(concurrency)
    timeout = httpx.Timeout(60.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "timestamp",
                "request_idx",
                "message",
                "http_status",
                "latency_ms",
                "response_raw",
                "intent",
                "decision",
                "response_type",
                "docs_found",
                "sources",
                "session_id",
                "id_requisicao",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            tasks = [
                asyncio.create_task(
                    worker(f"w{i}", queue, client, url, writer, rate_limiter, sem)
                )
                for i in range(concurrency)
            ]
            await asyncio.gather(*tasks)

    print("Done. CSV saved to", out_path)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int, default=1000)
    p.add_argument("--rate", type=int, default=100, help="requests per minute")
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument(
        "--out",
        type=str,
        default=f"artifacts/rag_requests_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
    )
    p.add_argument("--base-url", type=str, default="http://127.0.0.1:8000")
    args = p.parse_args()
    asyncio.run(main(args.count, args.rate, args.concurrency, args.out, args.base_url))
