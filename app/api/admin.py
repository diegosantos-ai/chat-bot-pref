"""
API de Admin - Painel {bot_name}
=============================
Endpoints para gestão do painel administrativo.
Requer autenticação JWT.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import uuid4

import asyncpg
import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel

from app.rag.retriever import RAGRetriever
from app.rag.ingest import (
    ingest_base,
    list_collections,
    load_manifest,
    get_chroma_client,
)
from app.scraper.service import (
    get_scraper_service,
    FieldConfig,
    NodeConfig,
    WorkflowConfig,
    PaginationConfig,
)
from app.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tereziapi/tereziadmin", tags=["Admin"])

# Configurações JWT
JWT_SECRET = settings.ADMIN_API_KEY or "dev-secret-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24


# ========================================
# MODELOS (DTOs)
# ========================================


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    role: str
    expires_in: int


class RAGConfig(BaseModel):
    min_score: float = 0.35
    top_k: int = 7
    boost_enabled: bool = True
    boost_amount: float = 0.2
    model: str = "gemini-2.0-flash"
    model_temperature: float = 0.3
    model_max_tokens: int = 1024


class SaveRAGConfigRequest(BaseModel):
    min_score: float
    top_k: int
    boost_enabled: bool
    boost_amount: float
    model: str = "gemini-2.0-flash"
    model_temperature: float = 0.3
    model_max_tokens: int = 1024


def _get_config_path() -> Path:
    """Caminho do arquivo de configuração do admin."""
    return Path(settings.BASE_DIR) / "admin_config.json"


def _load_admin_config() -> dict:
    """Carrega configurações do admin."""
    config_path = _get_config_path()
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_admin_config(config: dict) -> None:
    """Salva configurações do admin."""
    config_path = _get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


class RAGQueryRequest(BaseModel):
    query: str
    min_score: float = 0.0
    top_k: int = 10
    boost_enabled: bool = True
    collection: Optional[str] = None


class DocumentContent(BaseModel):
    id: str
    title: str
    file: str
    content: str
    keywords: list[str] = []
    intents: list[str] = []


class CreateDocumentRequest(BaseModel):
    title: str
    content: str
    keywords: list[str] = []
    intents: list[str] = []


class UpdateDocumentRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    keywords: Optional[list[str]] = None
    intents: Optional[list[str]] = None


class RAGQueryResponse(BaseModel):
    query: str
    chunks: list[dict]
    total_chunks: int
    best_score: float
    params_used: dict


class DashboardStats(BaseModel):
    total_conversas: int
    total_sucesso: int
    total_fallback: int
    total_erro: int
    hit_rate: float
    intents_distribution: dict
    canais_distribution: dict
    ultimas_24h: dict


class LogEventFilter(BaseModel):
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    canal: Optional[str] = None
    intent: Optional[str] = None
    decision: Optional[str] = None
    limit: int = 50
    offset: int = 0


class LogConversaFilter(BaseModel):
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    canal: Optional[str] = None
    intent: Optional[str] = None
    decision: Optional[str] = None
    busca_texto: Optional[str] = None
    limit: int = 50
    offset: int = 0


class DocumentInfo(BaseModel):
    id: str
    title: str
    file: str
    tags: list[str]
    intents: list[str]


class IngestRequest(BaseModel):
    base_path: str = "data/knowledge_base/BA-RAG-PILOTO-2026.01.v1"
    force: bool = False


class BackupResponse(BaseModel):
    status: str
    message: str
    file_path: Optional[str] = None


class ConfigResponse(BaseModel):
    app_name: str
    env: str
    version: str
    rag_config: RAGConfig
    chroma_collections: list[str]
    database_connected: bool


# ========================================
# AUTENTICAÇÃO
# ========================================


async def get_current_user(authorization: str = Header(None)) -> dict:
    """Valida token JWT e retorna dados do usuário."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorização não fornecido",
        )

    try:
        # Bearer token
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Requer role admin."""
    if current_user.get("role") not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito",
        )
    return current_user


# ========================================
# ENDPOINTS
# ========================================


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Autentica usuário e retorna token JWT."""

    conn = None
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)

        # Buscar usuário
        user = await conn.fetchrow(
            "SELECT id, username, password_hash, role, ativo FROM admin_users WHERE username = $1",
            request.username,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário ou senha incorretos",
            )

        if not user["ativo"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário inativo",
            )

        # Verificar senha
        if not bcrypt.checkpw(
            request.password.encode("utf-8"), user["password_hash"].encode("utf-8")
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário ou senha incorretos",
            )

        # Atualizar último login
        await conn.execute(
            "UPDATE admin_users SET ultimo_login = NOW() WHERE id = $1",
            user["id"],
        )

        # Gerar token JWT
        payload = {
            "sub": user["username"],
            "role": user["role"],
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return LoginResponse(
            token=token,
            username=user["username"],
            role=user["role"],
            expires_in=JWT_EXPIRE_HOURS * 3600,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar login",
        )
    finally:
        if conn:
            await conn.close()


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: dict = Depends(require_admin)):
    """Retorna estatísticas do dashboard."""

    conn = None
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)

        # Total de conversas
        total = await conn.fetchval("SELECT COUNT(*) FROM conversas")

        # Total por tipo de resposta
        sucesso = await conn.fetchval(
            "SELECT COUNT(*) FROM conversas WHERE tipo_resposta = 'SUCCESS'"
        )
        fallback = await conn.fetchval(
            "SELECT COUNT(*) FROM conversas WHERE tipo_resposta = 'FALLBACK'"
        )
        erro = await conn.fetchval(
            "SELECT COUNT(*) FROM conversas WHERE tipo_resposta = 'ERROR'"
        )

        # Hit rate
        hit_rate = (sucesso / total * 100) if total > 0 else 0

        # Distribuição de intents
        intents_raw = await conn.fetch(
            "SELECT intencao, COUNT(*) as count FROM conversas GROUP BY intencao ORDER BY count DESC"
        )
        intents_dist = {r["intencao"]: r["count"] for r in intents_raw}

        # Distribuição de canais
        canais_raw = await conn.fetch(
            "SELECT canal, COUNT(*) as count FROM conversas GROUP BY canal ORDER BY count DESC"
        )
        canais_dist = {r["canal"]: r["count"] for r in canais_raw}

        # Últimas 24h
        ultimas_24h_count = await conn.fetchval(
            "SELECT COUNT(*) FROM conversas WHERE criado_em > NOW() - INTERVAL '24 hours'"
        )

        return DashboardStats(
            total_conversas=total or 0,
            total_sucesso=sucesso or 0,
            total_fallback=fallback or 0,
            total_erro=erro or 0,
            hit_rate=round(hit_rate, 2),
            intents_distribution=intents_dist,
            canais_distribution=canais_dist,
            ultimas_24h={"count": ultimas_24h_count or 0},
        )

    except Exception as e:
        logger.error(f"Erro ao buscar stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar estatísticas: {str(e)}",
        )
    finally:
        if conn:
            await conn.close()


@router.get("/config", response_model=ConfigResponse)
async def get_config(current_user: dict = Depends(require_admin)):
    """Retorna configuração atual do sistema."""

    # Listar collections ChromaDB
    try:
        collections = list_collections()
    except Exception as e:
        logger.warning(f"Erro ao listar collections: {e}")
        collections = []

    # Verificar conexão com banco
    db_connected = False
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        await conn.fetchval("SELECT 1")
        await conn.close()
        db_connected = True
    except Exception:
        pass

    return ConfigResponse(
        app_name=settings.APP_NAME,
        env=settings.ENV,
        version=settings.VERSION,
        rag_config=RAGConfig(
            min_score=settings.RAG_MIN_SCORE,
            top_k=settings.RAG_TOP_K,
            boost_enabled=True,
            boost_amount=0.2,
            model=settings.GEMINI_MODEL,
            model_temperature=settings.GEMINI_TEMPERATURE,
            model_max_tokens=settings.GEMINI_MAX_TOKENS,
        ),
        chroma_collections=collections,
        database_connected=db_connected,
    )


@router.post("/config/rag")
async def save_rag_config(
    request: SaveRAGConfigRequest, current_user: dict = Depends(require_admin)
):
    """Salva configuração do RAG."""

    try:
        admin_config = _load_admin_config()
        admin_config["rag_config"] = {
            "min_score": request.min_score,
            "top_k": request.top_k,
            "boost_enabled": request.boost_enabled,
            "boost_amount": request.boost_amount,
            "model": request.model,
            "model_temperature": request.model_temperature,
            "model_max_tokens": request.model_max_tokens,
        }
        _save_admin_config(admin_config)

        # Invalidate boost cache to reload with new settings
        from app.rag.boosts import invalidate_cache

        invalidate_cache()

        return {"status": "success", "message": "Configuração salva com sucesso"}

    except Exception as e:
        logger.error(f"Erro ao salvar config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar configuração: {str(e)}",
        )


@router.post("/rag/query", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest, current_user: dict = Depends(require_admin)
):
    """Testa uma query no RAG com parâmetros customizados."""

    try:
        # Criar retriever com parâmetros customizados
        retriever = RAGRetriever(
            collection_name=request.collection or settings.RAG_COLLECTION_NAME,
            top_k=request.top_k,
            min_score=request.min_score,
        )

        # Executar busca
        result = await retriever.retrieve(
            query=request.query,
            top_k=request.top_k,
            min_score=request.min_score,
        )

        # Serializar chunks
        chunks_data = []
        for chunk in result.chunks:
            chunks_data.append(
                {
                    "id": chunk.id,
                    "text": chunk.text,
                    "source": chunk.source,
                    "title": chunk.title,
                    "section": chunk.section,
                    "score": round(chunk.score, 4),
                    "tags": chunk.tags,
                }
            )

        return RAGQueryResponse(
            query=result.query,
            chunks=chunks_data,
            total_chunks=result.total_chunks_searched,
            best_score=round(result.best_score, 4),
            params_used={
                "min_score": request.min_score,
                "top_k": request.top_k,
                "boost_enabled": request.boost_enabled,
                "collection": request.collection or settings.RAG_COLLECTION_NAME,
            },
        )

    except Exception as e:
        logger.error(f"Erro na query RAG: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao executar query: {str(e)}",
        )


@router.get("/rag/documents")
async def rag_documents(current_user: dict = Depends(require_admin)):
    """Lista documentos da base de conhecimento."""

    try:
        # Carregar manifest
        base_path = (
            Path(settings.BASE_DIR) / "data/knowledge_base/BA-RAG-PILOTO-2026.01.v1"
        )
        manifest = load_manifest(base_path)

        documents = []
        for doc in manifest.get("items", []):
            documents.append(
                DocumentInfo(
                    id=doc["id"],
                    title=doc["title"],
                    file=doc["file"],
                    tags=doc.get("keywords", []),
                    intents=doc.get("intents", []),
                )
            )

        return {
            "base_id": manifest.get("id"),
            "version": manifest.get("version"),
            "documents": documents,
        }

    except Exception as e:
        logger.error(f"Erro ao listar documentos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar documentos: {str(e)}",
        )


def _get_base_path() -> Path:
    return Path(settings.BASE_DIR) / "data/knowledge_base/BA-RAG-PILOTO-2026.01.v1"


def _load_manifest_with_path(base_path: Path) -> dict:
    """Carrega manifest.json."""
    manifest_path = base_path / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest não encontrado: {manifest_path}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_manifest(base_path: Path, manifest: dict) -> None:
    """Salva manifest.json."""
    manifest_path = base_path / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


@router.get("/rag/documents/{doc_id}")
async def rag_document_detail(doc_id: str, current_user: dict = Depends(require_admin)):
    """Obtém conteúdo de um documento específico."""

    try:
        base_path = _get_base_path()
        manifest = _load_manifest_with_path(base_path)

        doc = next((d for d in manifest.get("items", []) if d["id"] == doc_id), None)
        if not doc:
            raise HTTPException(status_code=404, detail="Documento não encontrado")

        doc_path = base_path / "items" / doc["file"]
        if not doc_path.exists():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")

        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        return DocumentContent(
            id=doc["id"],
            title=doc["title"],
            file=doc["file"],
            content=content,
            keywords=doc.get("keywords", []),
            intents=doc.get("intents", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter documento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter documento: {str(e)}",
        )


@router.post("/rag/documents")
async def rag_document_create(
    request: CreateDocumentRequest, current_user: dict = Depends(require_admin)
):
    """Cria um novo documento."""

    try:
        base_path = _get_base_path()
        manifest = _load_manifest_with_path(base_path)

        items_dir = base_path / "items"
        items_dir.mkdir(exist_ok=True)

        doc_id = f"{len(manifest.get('items', [])) + 1:04d}"
        filename = f"{doc_id}_{request.title.lower().replace(' ', '_')[:30]}.md"
        filepath = items_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(request.content)

        new_doc = {
            "id": doc_id,
            "title": request.title,
            "file": filename,
            "keywords": request.keywords,
            "intents": request.intents,
        }

        if "items" not in manifest:
            manifest["items"] = []
        manifest["items"].append(new_doc)

        _save_manifest(base_path, manifest)

        return {
            "status": "success",
            "message": f"Documento criado: {request.title}",
            "id": doc_id,
        }

    except Exception as e:
        logger.error(f"Erro ao criar documento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar documento: {str(e)}",
        )


@router.put("/rag/documents/{doc_id}")
async def rag_document_update(
    doc_id: str,
    request: UpdateDocumentRequest,
    current_user: dict = Depends(require_admin),
):
    """Atualiza um documento existente."""

    try:
        base_path = _get_base_path()
        manifest = _load_manifest_with_path(base_path)

        doc = next((d for d in manifest.get("items", []) if d["id"] == doc_id), None)
        if not doc:
            raise HTTPException(status_code=404, detail="Documento não encontrado")

        doc_path = base_path / "items" / doc["file"]

        if request.content is not None:
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(request.content)

        if request.title is not None:
            doc["title"] = request.title

        if request.keywords is not None:
            doc["keywords"] = request.keywords

        if request.intents is not None:
            doc["intents"] = request.intents

        _save_manifest(base_path, manifest)

        return {"status": "success", "message": f"Documento atualizado: {doc['title']}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar documento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar documento: {str(e)}",
        )


@router.delete("/rag/documents/{doc_id}")
async def rag_document_delete(doc_id: str, current_user: dict = Depends(require_admin)):
    """Exclui um documento."""

    try:
        base_path = _get_base_path()
        manifest = _load_manifest_with_path(base_path)

        doc = next((d for d in manifest.get("items", []) if d["id"] == doc_id), None)
        if not doc:
            raise HTTPException(status_code=404, detail="Documento não encontrado")

        doc_path = base_path / "items" / doc["file"]
        if doc_path.exists():
            doc_path.unlink()

        manifest["items"] = [d for d in manifest.get("items", []) if d["id"] != doc_id]
        _save_manifest(base_path, manifest)

        return {"status": "success", "message": f"Documento excluído: {doc['title']}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir documento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao excluir documento: {str(e)}",
        )


@router.post("/rag/ingest")
async def rag_ingest(
    request: IngestRequest, current_user: dict = Depends(require_admin)
):
    """Executa ingestion da base de conhecimento."""

    try:
        base_path = Path(settings.BASE_DIR) / request.base_path
        result = ingest_base(base_path, force=request.force)

        return {
            "status": "success",
            "message": f"Ingestão concluída: {result['documents_processed']} documentos, {result['chunks_created']} chunks",
            "result": result,
        }

    except Exception as e:
        logger.error(f"Erro na ingestão: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na ingestão: {str(e)}",
        )


@router.get("/logs/events")
async def get_logs_events(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    canal: Optional[str] = None,
    intent: Optional[str] = None,
    decision: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_admin),
):
    """Lista eventos de auditoria com filtros."""

    conn = None
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)

        # Construir query
        query = """
            SELECT 
                e.id_requisicao,
                e.id_sessao,
                e.canal,
                e.tipo_superficie,
                e.intencao,
                e.decisao,
                e.tipo_resposta,
                e.motivo_fallback,
                e.tempo_resposta_ms,
                e.criado_em
            FROM audit_events e
            WHERE 1=1
        """
        params = []
        param_idx = 1

        if data_inicio:
            query += f" AND e.criado_em >= ${param_idx}"
            params.append(data_inicio)
            param_idx += 1

        if data_fim:
            query += f" AND e.criado_em <= ${param_idx}"
            params.append(data_fim)
            param_idx += 1

        if canal:
            query += f" AND e.canal = ${param_idx}"
            params.append(canal)
            param_idx += 1

        if intent:
            query += f" AND e.intencao = ${param_idx}"
            params.append(intent.upper())
            param_idx += 1

        if decision:
            query += f" AND e.decisao = ${param_idx}"
            params.append(decision.upper())
            param_idx += 1

        query += (
            f" ORDER BY e.criado_em DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        )
        params.extend([limit, offset])

        events = await conn.fetch(query, *params)

        return {
            "events": [dict(e) for e in events],
            "count": len(events),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Erro ao buscar logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar logs: {str(e)}",
        )
    finally:
        if conn:
            await conn.close()


@router.get("/logs/conversas")
async def get_logs_conversas(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    canal: Optional[str] = None,
    intent: Optional[str] = None,
    decision: Optional[str] = None,
    busca_texto: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_admin),
):
    """Lista conversas com filtros."""

    conn = None
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)

        # Construir query
        query = """
            SELECT 
                c.id_conversa,
                c.id_requisicao,
                c.canal,
                c.tipo_superficie,
                c.mensagem_usuario,
                c.mensagem_resposta,
                c.intencao,
                c.decisao,
                c.tipo_resposta,
                c.motivo_fallback,
                c.sentimento,
                c.encontrou_docs,
                c.melhor_score,
                c.criado_em
            FROM conversas c
            WHERE 1=1
        """
        params = []
        param_idx = 1

        if data_inicio:
            query += f" AND c.criado_em >= ${param_idx}"
            params.append(data_inicio)
            param_idx += 1

        if data_fim:
            query += f" AND c.criado_em <= ${param_idx}"
            params.append(data_fim)
            param_idx += 1

        if canal:
            query += f" AND c.canal = ${param_idx}"
            params.append(canal)
            param_idx += 1

        if intent:
            query += f" AND c.intencao = ${param_idx}"
            params.append(intent.upper())
            param_idx += 1

        if decision:
            query += f" AND c.decisao = ${param_idx}"
            params.append(decision.upper())
            param_idx += 1

        if busca_texto:
            query += f" AND (c.mensagem_usuario ILIKE ${param_idx} OR c.mensagem_resposta ILIKE ${param_idx})"
            params.append(f"%{busca_texto}%")
            param_idx += 1

        query += (
            f" ORDER BY c.criado_em DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        )
        params.extend([limit, offset])

        conversas = await conn.fetch(query, *params)

        return {
            "conversas": [dict(c) for c in conversas],
            "count": len(conversas),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Erro ao buscar conversas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar conversas: {str(e)}",
        )
    finally:
        if conn:
            await conn.close()


@router.post("/ops/validate")
async def ops_validate(current_user: dict = Depends(require_admin)):
    """Valida infraestrutura."""


    results = {
        "database": {"status": "unknown", "message": ""},
        "chroma": {"status": "unknown", "message": ""},
        "gemini": {"status": "unknown", "message": ""},
    }

    # Testar banco
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        await conn.fetchval("SELECT 1")
        await conn.close()
        results["database"] = {"status": "ok", "message": "Conectado"}
    except Exception as e:
        results["database"] = {"status": "error", "message": str(e)}

    # Testar ChromaDB
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        results["chroma"] = {
            "status": "ok",
            "message": f"{len(collections)} collections",
        }
    except Exception as e:
        results["chroma"] = {"status": "error", "message": str(e)}

    # Testar Gemini
    try:
        from google import genai

        genai.Client(api_key=settings.GEMINI_API_KEY)
        # Quick test - não gera conteúdo, só verifica key
        if settings.GEMINI_API_KEY:
            results["gemini"] = {"status": "ok", "message": "API Key configurada"}
        else:
            results["gemini"] = {"status": "warning", "message": "API Key vazia"}
    except Exception as e:
        results["gemini"] = {"status": "error", "message": str(e)}

    return results


# ========================================
# ENDPOINTS: SCRAPING
# ========================================


class ScrapConfigCreate(BaseModel):
    nome: str
    url_base: str
    workflow: dict


class ScrapConfigUpdate(BaseModel):
    nome: Optional[str] = None
    url_base: Optional[str] = None
    workflow: Optional[dict] = None
    ativo: Optional[bool] = None


class ScrapScheduleCreate(BaseModel):
    config_id: str
    schedule_type: str  # 'manual' ou 'periodic'
    interval_minutes: Optional[int] = None
    enabled: bool = True


class ScrapPreviewRequest(BaseModel):
    url: str
    list_selector: Optional[str] = None
    item_selector: Optional[str] = None
    limit: int = 5


class ScrapExecuteRequest(BaseModel):
    limit: int = 50


@router.post("/scrap/configs")
async def create_scrap_config(data: ScrapConfigCreate, _: str = Depends(require_admin)):
    """Cria uma nova configuração de scraping."""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        result = await conn.fetchrow(
            """
            INSERT INTO scrap_configs (nome, url_base, workflow)
            VALUES ($1, $2, $3)
            RETURNING id, nome, url_base, workflow, ativo, criado_em, atualizado_em
        """,
            data.nome,
            data.url_base,
            json.dumps(data.workflow),
        )
        return result
    finally:
        await conn.close()


@router.get("/scrap/configs")
async def list_scrap_configs(ativo: bool = True, _: str = Depends(require_admin)):
    """Lista configurações de scraping."""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        results = await conn.fetch(
            """
            SELECT id, nome, url_base, workflow, ativo, criado_em, atualizado_em
            FROM scrap_configs
            WHERE ativo = $1
            ORDER BY nome
        """,
            ativo,
        )
        return results
    finally:
        await conn.close()


@router.get("/scrap/configs/{config_id}")
async def get_scrap_config(config_id: str, _: str = Depends(require_admin)):
    """Obtém uma configuração específica."""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        result = await conn.fetchrow(
            """
            SELECT id, nome, url_base, workflow, ativo, criado_em, atualizado_em
            FROM scrap_configs
            WHERE id = $1
        """,
            config_id,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Configuração não encontrada")
        return result
    finally:
        await conn.close()


@router.put("/scrap/configs/{config_id}")
async def update_scrap_config(
    config_id: str, data: ScrapConfigUpdate, _: str = Depends(require_admin)
):
    """Atualiza uma configuração."""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        updates = []
        values = []
        idx = 1

        if data.nome is not None:
            updates.append(f"nome = ${idx}")
            values.append(data.nome)
            idx += 1
        if data.url_base is not None:
            updates.append(f"url_base = ${idx}")
            values.append(data.url_base)
            idx += 1
        if data.workflow is not None:
            updates.append(f"workflow = ${idx}")
            values.append(json.dumps(data.workflow))
            idx += 1
        if data.ativo is not None:
            updates.append(f"ativo = ${idx}")
            values.append(data.ativo)
            idx += 1

        updates.append(f"atualizado_em = ${idx}")
        values.append(datetime.utcnow())
        idx += 1

        values.append(config_id)

        result = await conn.fetchrow(
            f"""
            UPDATE scrap_configs
            SET {", ".join(updates)}
            WHERE id = ${idx}
            RETURNING id, nome, url_base, workflow, ativo, criado_em, atualizado_em
        """,
            *values,
        )

        if not result:
            raise HTTPException(status_code=404, detail="Configuração não encontrada")
        return result
    finally:
        await conn.close()


@router.delete("/scrap/configs/{config_id}")
async def delete_scrap_config(config_id: str, _: str = Depends(require_admin)):
    """Remove uma configuração (soft delete)."""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        await conn.execute(
            """
            UPDATE scrap_configs SET ativo = FALSE WHERE id = $1
        """,
            config_id,
        )
        return {"message": "Configuração removida"}
    finally:
        await conn.close()


@router.post("/scrap/preview")
async def preview_scrap(data: ScrapPreviewRequest, _: str = Depends(require_admin)):
    """Faz preview de uma URL para descobrir selectors."""
    scraper = get_scraper_service()
    try:
        result = await scraper.preview_url(
            url=data.url,
            list_selector=data.list_selector,
            item_selector=data.item_selector,
            limit=data.limit,
        )
        return result
    finally:
        pass


class ScrapInteractivePreviewRequest(BaseModel):
    url: str


class ScrapLinkPreviewRequest(BaseModel):
    url: str
    base_url: str = ""


@router.post("/scrap/preview/interactive")
async def preview_interactive_scrap(
    data: ScrapInteractivePreviewRequest, _: str = Depends(require_admin)
):
    """Gera preview interativo onde o usuário pode clicar nos elementos."""
    scraper = get_scraper_service()
    try:
        result = await scraper.generate_interactive_preview(url=data.url)
        return result
    finally:
        pass


@router.post("/scrap/preview/link")
async def preview_link_scrap(
    data: ScrapLinkPreviewRequest, _: str = Depends(require_admin)
):
    """Faz preview de um link clicado no preview interativo."""
    scraper = get_scraper_service()
    try:
        result = await scraper.preview_link(url=data.url, base_url=data.base_url)
        return result
    finally:
        pass


@router.post("/scrap/execute/{config_id}")
async def execute_scrap(
    config_id: str, data: ScrapExecuteRequest, _: str = Depends(require_admin)
):
    """Executa o scraping de uma configuração."""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        # Buscar configuração
        config = await conn.fetchrow(
            """
            SELECT * FROM scrap_configs WHERE id = $1 AND ativo = TRUE
        """,
            config_id,
        )

        if not config:
            raise HTTPException(status_code=404, detail="Configuração não encontrada")

        # Executar scraping
        scraper = get_scraper_service()

        # Parse workflow from JSON string
        import json

        workflow_data = (
            json.loads(config["workflow"])
            if isinstance(config["workflow"], str)
            else config["workflow"]
        )
        workflow = WorkflowConfig(
            nodes=[
                NodeConfig(
                    id=node["id"],
                    label=node.get("label", ""),
                    url=node.get("url"),
                    list_selector=node.get("listSelector"),
                    item_selector=node.get("itemSelector"),
                    fields=[
                        FieldConfig(
                            name=f["name"],
                            selector=f["selector"],
                            field_type=f.get("type", "text"),
                            attribute=f.get("attribute"),
                        )
                        for f in node.get("fields", [])
                    ],
                    follow_links=node.get("followLinks", False),
                    link_selector=node.get("linkSelector"),
                    next_node_id=node.get("nextNode"),
                    pagination=PaginationConfig(
                        enabled=node.get("pagination", {}).get("enabled", False),
                        type=node.get("pagination", {}).get("type", "none"),
                        next_button_selector=node.get("pagination", {}).get(
                            "nextButtonSelector"
                        ),
                        page_param_name=node.get("pagination", {}).get(
                            "pageParamName", "pag"
                        ),
                        max_pages=node.get("pagination", {}).get("maxPages", 5),
                        stop_when_empty=node.get("pagination", {}).get(
                            "stopWhenEmpty", True
                        ),
                    )
                    if node.get("pagination")
                    else None,
                )
                for node in workflow_data.get("nodes", [])
            ],
            start_node_id=workflow_data.get("startNodeId", "node_1"),
        )

        result = await scraper.execute_workflow(
            workflow=workflow, base_url=config["url_base"], limit=data.limit
        )

        # Salvar resultado
        result_id = uuid4()
        await conn.execute(
            """
            INSERT INTO scrap_results (id, config_id, status, items_count, data)
            VALUES ($1, $2, $3, $4, $5)
        """,
            result_id,
            config_id,
            "success" if result.success else "error",
            len(result.items),
            json.dumps(
                [{**item.data, "detail": item.detail_data} for item in result.items]
            ),
        )

        return {
            "result_id": str(result_id),
            "success": result.success,
            "items_count": len(result.items),
            "items": [
                {**item.data, "detail": item.detail_data} for item in result.items
            ],
            "error": result.error,
            "nodes_executed": result.nodes_executed,
        }
    finally:
        await conn.close()


# Schedules
@router.post("/scrap/schedules")
async def create_scrap_schedule(
    data: ScrapScheduleCreate, _: str = Depends(require_admin)
):
    """Cria um agendamento."""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        # Validar config existe
        config = await conn.fetchrow(
            "SELECT id FROM scrap_configs WHERE id = $1", data.config_id
        )
        if not config:
            raise HTTPException(status_code=404, detail="Configuração não encontrada")

        next_run = None
        if data.schedule_type == "periodic" and data.interval_minutes:
            next_run = datetime.utcnow() + timedelta(minutes=data.interval_minutes)

        result = await conn.fetchrow(
            """
            INSERT INTO scrap_schedules (config_id, schedule_type, interval_minutes, enabled, next_run)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """,
            data.config_id,
            data.schedule_type,
            data.interval_minutes,
            data.enabled,
            next_run,
        )
        return result
    finally:
        await conn.close()


@router.get("/scrap/schedules")
async def list_scrap_schedules(
    config_id: Optional[str] = None, _: str = Depends(require_admin)
):
    """Lista agendamentos."""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        if config_id:
            results = await conn.fetch(
                """
                SELECT s.*, c.nome as config_nome
                FROM scrap_schedules s
                JOIN scrap_configs c ON s.config_id = c.id
                WHERE s.config_id = $1
                ORDER BY s.criado_em DESC
            """,
                config_id,
            )
        else:
            results = await conn.fetch("""
                SELECT s.*, c.nome as config_nome
                FROM scrap_schedules s
                JOIN scrap_configs c ON s.config_id = c.id
                ORDER BY s.criado_em DESC
            """)
        return results
    finally:
        await conn.close()


@router.put("/scrap/schedules/{schedule_id}")
async def update_scrap_schedule(
    schedule_id: str, enabled: bool, _: str = Depends(require_admin)
):
    """Atualiza agendamento (habilitar/desabilitar)."""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        result = await conn.fetchrow(
            """
            UPDATE scrap_schedules 
            SET enabled = $1
            WHERE id = $2
            RETURNING *
        """,
            enabled,
            schedule_id,
        )
        return result
    finally:
        await conn.close()


@router.delete("/scrap/schedules/{schedule_id}")
async def delete_scrap_schedule(schedule_id: str, _: str = Depends(require_admin)):
    """Remove agendamento."""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        await conn.execute("DELETE FROM scrap_schedules WHERE id = $1", schedule_id)
        return {"message": "Agendamento removido"}
    finally:
        await conn.close()


# Results
@router.get("/scrap/results")
async def list_scrap_results(
    config_id: Optional[str] = None, limit: int = 20, _: str = Depends(require_admin)
):
    """Lista resultados de scraping."""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        if config_id:
            results = await conn.fetch(
                """
                SELECT r.*, c.nome as config_nome
                FROM scrap_results r
                JOIN scrap_configs c ON r.config_id = c.id
                WHERE r.config_id = $1
                ORDER BY r.executed_at DESC
                LIMIT $2
            """,
                config_id,
                limit,
            )
        else:
            results = await conn.fetch(
                """
                SELECT r.*, c.nome as config_nome
                FROM scrap_results r
                JOIN scrap_configs c ON r.config_id = c.id
                ORDER BY r.executed_at DESC
                LIMIT $1
            """,
                limit,
            )
        return results
    finally:
        await conn.close()


@router.get("/scrap/results/{result_id}")
async def get_scrap_result(result_id: str, _: str = Depends(require_admin)):
    """Obtém um resultado específico."""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        result = await conn.fetchrow(
            """
            SELECT r.*, c.nome as config_nome
            FROM scrap_results r
            JOIN scrap_configs c ON r.config_id = c.id
            WHERE r.id = $1
        """,
            result_id,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Resultado não encontrado")
        return result
    finally:
        await conn.close()


# ========================================
# ENDPOINTS: CONVERTER RESULT TO RAG
# ========================================


class ConvertToRAGRequest(BaseModel):
    result_id: str
    mode: str = "create"  # 'create' ou 'add'
    document_id: Optional[str] = None
    title_template: str = "{titulo}"  # Template para título


@router.post("/scrap/results/{result_id}/to-rag")
async def convert_result_to_rag(
    result_id: str, data: ConvertToRAGRequest, _: str = Depends(require_admin)
):
    """Converte resultado de scraping para documento RAG."""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        # Buscar resultado
        result = await conn.fetchrow(
            "SELECT * FROM scrap_results WHERE id = $1", result_id
        )
        if not result:
            raise HTTPException(status_code=404, detail="Resultado não encontrado")

        items = result["data"]
        if not items:
            raise HTTPException(status_code=400, detail="Nenhum dado para converter")

        # Converter items para markdown
        markdown_parts = []

        for item in items:
            # Criar título a partir do template
            titulo = data.title_template.format(**item)

            # Criar conteúdo
            content_parts = []
            for key, value in item.items():
                if key != "detail" and value:
                    content_parts.append(f"**{key.upper()}**: {value}")

            # Se tem detail, adicionar também
            if item.get("detail"):
                content_parts.append("\n---")
                content_parts.append("**DETALHES:**\n")
                for key, value in item["detail"].items():
                    if value:
                        content_parts.append(f"- **{key}**: {value}")

            markdown = f"## {titulo}\n\n" + "\n".join(content_parts)
            markdown_parts.append(markdown)

        full_content = "\n\n---\n\n".join(markdown_parts)

        # Se modo é criar, criar novo documento
        if data.mode == "create":
            return {
                "mode": "create",
                "content": full_content,
                "items_count": len(items),
                "document": None,  # Frontend will create via /rag/documents
            }
        else:
            # Modo add - buscar documento existente e adicionar
            if not data.document_id:
                raise HTTPException(
                    status_code=400, detail="document_id requerido para modo 'add'"
                )

            doc = await conn.fetchrow(
                "SELECT * FROM rag_documents WHERE id = $1", data.document_id
            )
            if not doc:
                raise HTTPException(status_code=404, detail="Documento não encontrado")

            # Concatenar conteúdo
            new_content = doc["content"] + "\n\n" + full_content

            await conn.execute(
                """
                UPDATE rag_documents 
                SET content = $1, atualizado_em = now()
                WHERE id = $2
            """,
                new_content,
                data.document_id,
            )

            return {
                "mode": "add",
                "document_id": data.document_id,
                "content": full_content,
                "items_count": len(items),
            }
    finally:
        await conn.close()


# ========================================
# ENDPOINTS: BOOSTS
# ========================================


class BoostConfigCreate(BaseModel):
    nome: str
    tipo: str  # 'sigla' | 'palavra_chave' | 'categoria'
    valor: str
    boost_value: float = 0.2
    prioridade: int = 0
    ativo: bool = True


class BoostConfigUpdate(BaseModel):
    nome: Optional[str] = None
    valor: Optional[str] = None
    boost_value: Optional[float] = None
    prioridade: Optional[int] = None
    ativo: Optional[bool] = None


@router.get("/admin/boosts")
async def list_boosts(
    tipo: Optional[str] = None,
    ativo: Optional[bool] = None,
    _: str = Depends(require_admin),
):
    """Lista configurações de boost."""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        query = "SELECT * FROM boost_configs WHERE 1=1"
        params = []

        if tipo:
            params.append(tipo)
            query += f" AND tipo = ${len(params)}"

        if ativo is not None:
            params.append(ativo)
            query += f" AND ativo = ${len(params)}"

        query += " ORDER BY prioridade DESC, nome"

        results = await conn.fetch(query, *params)
        return results
    finally:
        await conn.close()


@router.post("/admin/boosts")
async def create_boost(data: BoostConfigCreate, _: str = Depends(require_admin)):
    """Cria um novo boost."""
    from app.rag.boosts import invalidate_cache

    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        result = await conn.fetchrow(
            """
            INSERT INTO boost_configs (nome, tipo, valor, boost_value, prioridade, ativo)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """,
            data.nome,
            data.tipo,
            data.valor,
            data.boost_value,
            data.prioridade,
            data.ativo,
        )

        invalidate_cache()
        return result
    finally:
        await conn.close()


@router.put("/admin/boosts/{boost_id}")
async def update_boost(
    boost_id: str, data: BoostConfigUpdate, _: str = Depends(require_admin)
):
    """Atualiza um boost."""
    from app.rag.boosts import invalidate_cache

    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        updates = []
        values = []
        idx = 1

        if data.nome is not None:
            updates.append(f"nome = ${idx}")
            values.append(data.nome)
            idx += 1
        if data.valor is not None:
            updates.append(f"valor = ${idx}")
            values.append(data.valor)
            idx += 1
        if data.boost_value is not None:
            updates.append(f"boost_value = ${idx}")
            values.append(data.boost_value)
            idx += 1
        if data.prioridade is not None:
            updates.append(f"prioridade = ${idx}")
            values.append(data.prioridade)
            idx += 1
        if data.ativo is not None:
            updates.append(f"ativo = ${idx}")
            values.append(data.ativo)
            idx += 1

        if not updates:
            raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

        updates.append(f"atualizado_em = ${idx}")
        values.append(datetime.utcnow())
        idx += 1

        values.append(boost_id)

        result = await conn.fetchrow(
            f"""
            UPDATE boost_configs
            SET {", ".join(updates)}
            WHERE id = ${idx}
            RETURNING *
        """,
            *values,
        )

        if not result:
            raise HTTPException(status_code=404, detail="Boost não encontrado")

        invalidate_cache()
        return result
    finally:
        await conn.close()


@router.delete("/admin/boosts/{boost_id}")
async def delete_boost(boost_id: str, _: str = Depends(require_admin)):
    """Remove um boost (soft delete)."""
    from app.rag.boosts import invalidate_cache

    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        result = await conn.fetchrow(
            """
            UPDATE boost_configs SET ativo = FALSE, atualizado_em = now()
            WHERE id = $1
            RETURNING *
        """,
            boost_id,
        )

        if not result:
            raise HTTPException(status_code=404, detail="Boost não encontrado")

        invalidate_cache()
        return {"message": "Boost removido"}
    finally:
        await conn.close()


@router.get("/admin/boosts/templates")
async def get_boost_templates(_: str = Depends(require_admin)):
    """Retorna lista de siglas disponíveis (do arquivo atual)."""
    from app.rag.acronyms import ALL_ACRONYMS

    return [{"sigla": k, "descricao": v} for k, v in ALL_ACRONYMS.items()]


@router.post("/admin/boosts/import")
async def import_acronyms_boosts(_: str = Depends(require_admin)):
    """Importa siglas do arquivo hardcoded para o banco."""
    from app.rag.acronyms import ALL_ACRONYM_KEYS
    from app.rag.boosts import invalidate_cache

    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        imported = 0
        skipped = 0

        for i, sigla in enumerate(sorted(ALL_ACRONYM_KEYS)):
            # Verificar se já existe
            existing = await conn.fetchval(
                "SELECT COUNT(*) FROM boost_configs WHERE valor = $1 AND tipo = 'sigla'",
                sigla,
            )

            if existing == 0:
                await conn.execute(
                    """
                    INSERT INTO boost_configs (nome, tipo, valor, boost_value, prioridade, ativo)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    sigla,
                    "sigla",
                    sigla,
                    0.2,
                    i + 1,
                    True,
                )
                imported += 1
            else:
                skipped += 1

        invalidate_cache()
        return {"imported": imported, "skipped": skipped}
    finally:
        await conn.close()
