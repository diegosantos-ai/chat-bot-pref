"""
Setup Demo Tenant — Nexo Basis Governador SaaS
================================================
Script de seed para GTM/Vendas.

Provisiona um tenant demo completo "Prefeitura de Nova Esperança" com:
  ✅ Registro na tabela `tenants`
  ✅ Credenciais Meta placeholder em `tenant_credentials`
  ✅ Base RAG demo com documentos fictícios em data/demo/nova_esperanca/
  ✅ Ingestão automática na collection ChromaDB {tenant_id}_knowledge_base

Uso:
    python scripts/setup_demo_tenant.py
    python scripts/setup_demo_tenant.py --reset   # apaga e recria do zero
    python scripts/setup_demo_tenant.py --dry-run # só mostra o que faria
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("setup_demo_tenant")

# ──────────────────────────────────────────────────────────────
# Configuração do demo tenant
# ──────────────────────────────────────────────────────────────

DEMO_TENANT = {
    "tenant_id": "prefeitura_nova_esperanca",
    "bot_name": "EsperBot",
    "client_name": "Prefeitura de Nova Esperança",
    "fallback_url": "https://novaesperanca.gov.br",
    "contact_phone": "(19) 3456-7890",
    "contact_address": "Praça das Flores, 100 – Centro – Nova Esperança/SP",
    "support_email": "atendimento@novaesperanca.gov.br",
    "rag_base_path": "data/demo/nova_esperanca",
    "is_active": True,
}

DEMO_CREDENTIALS = {
    # Placeholders para demo — não funcionam na API real
    "meta_ig_page_id":       "111111111111111",
    "meta_fb_page_id":       "222222222222222",
    "meta_access_token_ig":  "DEMO_IG_TOKEN_REPLACE_ME",
    "meta_access_token_fb":  "DEMO_FB_TOKEN_REPLACE_ME",
    "meta_webhook_verify_token": "nova_esperanca_verify_token_demo",
}

# Documentos demo: conteúdo mínimo mas representativo para GTM
DEMO_DOCUMENTS = {
    "manifest.json": json.dumps({
        "id": "nova-esperanca-demo-v1",
        "version": "1.0.0",
        "client": "Prefeitura de Nova Esperança",
        "created_at": datetime.utcnow().strftime("%Y-%m-%d"),
        "documents": [
            {"id": "horarios_secretarias", "file": "horarios_secretarias.md",
             "title": "Horários das Secretarias", "tags": ["horarios", "atendimento"]},
            {"id": "iptu_2026",            "file": "iptu_2026.md",
             "title": "IPTU 2026 — Datas e Formas de Pagamento", "tags": ["iptu", "tributos"]},
            {"id": "programas_sociais",    "file": "programas_sociais.md",
             "title": "Programas Sociais da Prefeitura", "tags": ["social", "beneficios"]},
            {"id": "alvara_funcionamento", "file": "alvara_funcionamento.md",
             "title": "Alvará de Funcionamento — Requisitos", "tags": ["alvara", "comercio"]},
            {"id": "iluminacao_publica",   "file": "iluminacao_publica.md",
             "title": "Troca de Lâmpadas e Iluminação Pública", "tags": ["iluminacao", "zeladoria"]},
            {"id": "matricula_creche",    "file": "matricula_creche.md",
             "title": "Fila de Espera e Vagas em Creches (CMEI)", "tags": ["creche", "educacao", "cmei"]},
        ],
    }, ensure_ascii=False, indent=2),

    "items/horarios_secretarias.md": """\
## Horários das Secretarias

A Prefeitura de Nova Esperança funciona de **segunda a sexta-feira**, das 8h às 17h.

### Secretaria de Educação
- Endereço: Rua das Palmeiras, 50 – Centro
- Telefone: (19) 3456-7891
- Horário: 8h – 17h

### Secretaria de Saúde
- Endereço: Av. Brasil, 200 – Centro
- Telefone: (19) 3456-7892
- Horário: 7h – 19h (plantão 24h no pronto-socorro)

### Secretaria de Obras
- Endereço: Rua dos Ipês, 10 – Bairro Industrial
- Telefone: (19) 3456-7893
- Horário: 8h – 17h
""",

    "items/iptu_2026.md": """\
## IPTU 2026 — Prefeitura de Nova Esperança

### Datas de Vencimento
| Parcela | Vencimento  |
|---------|-------------|
| Cota única (10% desconto) | 28/02/2026 |
| 1ª parcela | 28/02/2026 |
| 2ª parcela | 31/03/2026 |
| 3ª parcela | 30/04/2026 |
| 4ª–10ª     | Último dia útil de cada mês |

### Formas de Pagamento
- Boleto bancário (disponível no portal do contribuinte)
- PIX: chave CNPJ 12.345.678/0001-00
- Caixas eletrônicos do Banco do Brasil e Bradesco
- Presencialmente na Praça das Flores, 100 – setor tributário

### Segunda via do boleto
Acesse: **portal.novaesperanca.gov.br/iptu** ou ligue (19) 3456-7890
""",

    "items/programas_sociais.md": """\
## Programas Sociais da Prefeitura de Nova Esperança

### Cesta Básica Solidária
- Público-alvo: Famílias em vulnerabilidade com renda per capita até ½ salário mínimo.
- Inscrições: CRAS – Rua das Acácias, 30 – Vila Operária
- Documentos: RG, CPF, comprovante de renda e residência

### Passe Livre Municipal
- Gratuidade de passagem para estudantes matriculados na rede pública.
- Solicitação: Secretaria de Educação (Rua das Palmeiras, 50)

### Farmácia Popular
- Medicamentos com até 90% de desconto para beneficiários do Bolsa Família.
- Local: UBS Central – Av. Brasil, 200

### Habitação
- Programa Minha Casa Nova Esperança: cadastro aberto para famílias sem imóvel próprio.
- Mais informações: habitacao@novaesperanca.gov.br
""",

    "items/alvara_funcionamento.md": """\
## Alvará de Funcionamento — Nova Esperança

### Documentos Necessários
1. Requerimento padrão (disponível no portal da prefeitura)
2. Contrato social ou MEI
3. CNPJ ativo na Receita Federal
4. Comprovante de endereço comercial
5. Laudo do Corpo de Bombeiros (para estabelecimentos com público > 50 pessoas)
6. Alvará sanitário (para alimentação, saúde e estética)

### Prazo de Emissão
- Alvará provisório: em até **3 dias úteis**
- Alvará definitivo: em até **30 dias úteis** (após vistoria)

### Taxa
- MEI: isento
- Demais: R$ 150,00 – R$ 800,00 conforme área e atividade

### Onde solicitar
- Presencial: Secretaria de Desenvolvimento Econômico – Praça das Flores, 100
- Online: portal.novaesperanca.gov.br/alvara
- Telefone: (19) 3456-7894
""",

    "items/iluminacao_publica.md": """\
## Troca de Lâmpadas e Manutenção de Iluminação Pública

### Procedimento para Solicitação
A prefeitura realiza a troca de lâmpadas queimadas em vias públicas através da Secretaria de Obras e Zeladoria Urbana.
Para solicitar manutenção, certifique-se de ter as seguintes informações:
1. Endereço completo (Rua, Número, Bairro)
2. Ponto de referência
3. Número de identificação do poste (numeração amarela na altura dos olhos)

### Prazos e Condições
- **Troca de lâmpada simples:** Até 48 horas úteis após a abertura do chamado.
- **Braço do poste danificado:** Até 5 dias úteis (requer equipe especializada).
- **Poste com risco de queda:** Atendimento EMERGENCIAL 24h (Ligue para a Defesa Civil no 199).

Lembrando que a manutenção da iluminação DENTRO de condomínios fechados é de responsabilidade da administração do condomínio.
""",

    "items/matricula_creche.md": """\
## Fila de Espera e Vagas em Creches (CMEI)

O cadastramento para a fila de espera dos Centros Municipais de Educação Infantil (CMEIs) ocorre o ano todo via Central de Vagas.

### Como Cadastrar a Criança na Fila
1. Compareça à Secretaria da Educação (Rua das Palmeiras, 50 - Centro) portando:
    - Certidão de Nascimento da criança
    - CPF dos pais ou responsáveis legais
    - Comprovante de residência atualizado (conta de água ou luz)
    - Comprovante de trabalho da mãe (para critério de prioridade) e carteira de vacinação da criança.

### Critérios de Prioridade (Lei Municipal 1234/2020)
As vagas não são distribuídas apenas por ondem de chegada. Os seguintes critérios garantem maior pontuação na fila:
- Mãe trabalhadora (comprovado via carteira de trabalho)
- Família cadastrada e beneficiária do Bolsa Família
- Crianças sob medida de proteção (encaminhadas pelo Conselho Tutelar)
- Crianças com laudo médico de deficiência ou TEA.

A lista contendo a posição na fila de espera pode ser consultada a qualquer momento no nosso portal educacao.novaesperanca.gov.br/fila-creche utilizando o protocolo gerado no momento do cadastro.
""",
}


# ──────────────────────────────────────────────────────────────
# Criação dos arquivos demo
# ──────────────────────────────────────────────────────────────

def create_demo_files(base_dir: Path, dry_run: bool = False) -> None:
    """Cria os arquivos da base de conhecimento demo localmente."""
    base_dir / "items"

    for filename, content in DEMO_DOCUMENTS.items():
        file_path = base_dir / filename
        if dry_run:
            logger.info("[DRY-RUN] Criaria: %s", file_path)
            continue
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        logger.info("  ✅ Criado: %s", file_path)


# ──────────────────────────────────────────────────────────────
# Banco de dados
# ──────────────────────────────────────────────────────────────

async def seed_database(pool: asyncpg.Pool, reset: bool = False, dry_run: bool = False) -> None:  # noqa: F821
    """Insere o tenant demo no PostgreSQL."""
    tenant_id = DEMO_TENANT["tenant_id"]

    if dry_run:
        logger.info("[DRY-RUN] Inseriria tenant_id=%s no banco", tenant_id)
        return

    async with pool.acquire() as conn:
        if reset:
            await conn.execute("DELETE FROM tenant_credentials WHERE tenant_id = $1", tenant_id)
            await conn.execute("DELETE FROM tenants WHERE tenant_id = $1", tenant_id)
            logger.info("♻️  Tenant removido para reinserção")

        # Upsert tenant
        await conn.execute("""
            INSERT INTO tenants (
                tenant_id, bot_name, client_name, fallback_url,
                contact_phone, contact_address, support_email,
                rag_base_path, is_active
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            ON CONFLICT (tenant_id) DO UPDATE SET
                bot_name         = EXCLUDED.bot_name,
                client_name      = EXCLUDED.client_name,
                fallback_url     = EXCLUDED.fallback_url,
                contact_phone    = EXCLUDED.contact_phone,
                contact_address  = EXCLUDED.contact_address,
                support_email    = EXCLUDED.support_email,
                rag_base_path    = EXCLUDED.rag_base_path,
                is_active        = EXCLUDED.is_active
        """,
            tenant_id,
            DEMO_TENANT["bot_name"],
            DEMO_TENANT["client_name"],
            DEMO_TENANT["fallback_url"],
            DEMO_TENANT["contact_phone"],
            DEMO_TENANT["contact_address"],
            DEMO_TENANT["support_email"],
            DEMO_TENANT["rag_base_path"],
            DEMO_TENANT["is_active"],
        )
        logger.info("✅ Tenant inserido/atualizado: %s", tenant_id)

        # Upsert credentials
        await conn.execute("""
            INSERT INTO tenant_credentials (
                tenant_id, meta_ig_page_id, meta_fb_page_id,
                meta_access_token_ig, meta_access_token_fb,
                meta_webhook_verify_token
            ) VALUES ($1,$2,$3,$4,$5,$6)
            ON CONFLICT (tenant_id) DO UPDATE SET
                meta_ig_page_id          = EXCLUDED.meta_ig_page_id,
                meta_fb_page_id          = EXCLUDED.meta_fb_page_id,
                meta_access_token_ig     = EXCLUDED.meta_access_token_ig,
                meta_access_token_fb     = EXCLUDED.meta_access_token_fb,
                meta_webhook_verify_token = EXCLUDED.meta_webhook_verify_token
        """,
            tenant_id,
            DEMO_CREDENTIALS["meta_ig_page_id"],
            DEMO_CREDENTIALS["meta_fb_page_id"],
            DEMO_CREDENTIALS["meta_access_token_ig"],
            DEMO_CREDENTIALS["meta_access_token_fb"],
            DEMO_CREDENTIALS["meta_webhook_verify_token"],
        )
        logger.info("✅ Credenciais Meta inseridas: %s", tenant_id)


# ──────────────────────────────────────────────────────────────
# Ingestão RAG
# ──────────────────────────────────────────────────────────────

def run_demo_ingest(base_path: Path, dry_run: bool = False) -> None:
    """Executa a ingestão da base demo na collection ChromaDB do tenant."""
    if dry_run:
        logger.info("[DRY-RUN] Faria ingestão em %s", base_path)
        return

    from scripts.rag_etl_job import run_ingest_for_tenant
    tenant_id = DEMO_TENANT["tenant_id"]
    result = run_ingest_for_tenant(tenant_id, str(base_path), force=True)

    if "error" in result:
        logger.error("❌ Ingestão falhou: %s", result["error"])
    else:
        logger.info("✅ Ingestão concluída: %d chunks criados", result["chunks"])


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

async def main(reset: bool = False, dry_run: bool = False) -> None:
    from app.settings import settings

    logger.info("=" * 60)
    logger.info("Setup Demo Tenant — Prefeitura de Nova Esperança")
    logger.info("=" * 60)

    base_path = Path(DEMO_TENANT["rag_base_path"])

    # 1. Arquivos da base de conhecimento
    logger.info("\n[1/3] Criando arquivos da base de conhecimento demo...")
    create_demo_files(base_path, dry_run=dry_run)

    # 2. Banco de dados
    logger.info("\n[2/3] Semeando banco de dados...")
    if not dry_run:
        pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=1, max_size=3)  # noqa: F821
        try:
            await seed_database(pool, reset=reset, dry_run=dry_run)
        finally:
            await pool.close()
    else:
        await seed_database(None, reset=reset, dry_run=dry_run)

    # 3. Ingestão ChromaDB
    logger.info("\n[3/3] Ingerindo base demo no ChromaDB...")
    run_demo_ingest(base_path, dry_run=dry_run)

    logger.info("\n" + "=" * 60)
    if dry_run:
        logger.info("✅ DRY-RUN completo — nenhuma mudança foi feita.")
    else:
        logger.info("✅ Demo tenant pronto!")
        logger.info("   tenant_id : %s", DEMO_TENANT["tenant_id"])
        logger.info("   bot_name  : %s", DEMO_TENANT["bot_name"])
        logger.info("   collection: %s_knowledge_base", DEMO_TENANT["tenant_id"])
        logger.info("\n👉 Para testar via webhook:")
        logger.info("   page_id simulado: %s", DEMO_CREDENTIALS["meta_ig_page_id"])
        logger.info("   python scripts/ops/simulate_webhook.py --page-id %s",
                    DEMO_CREDENTIALS["meta_ig_page_id"])
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup do tenant demo para GTM/Sales.")
    parser.add_argument("--reset",   action="store_true", help="Remove e recria o tenant do zero.")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem escrever nada.")
    args = parser.parse_args()
    asyncio.run(main(reset=args.reset, dry_run=args.dry_run))
