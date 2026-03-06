"""Admin API — Cross-Tenant Audit Logs + CSV Export."""
import io
import csv
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from api import get_conn

router = APIRouter(prefix="/api/admin/logs", tags=["Logs"])


@router.get("")
async def get_logs(
    tenant_id: Optional[str] = None,
    channel: Optional[str] = None,
    intent: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, le=200),
):
    conn = await get_conn()
    try:
        conditions = []
        args = []

        if tenant_id:
            args.append(tenant_id)
            conditions.append(f"tenant_id = ${len(args)}")
        if channel:
            args.append(channel)
            conditions.append(f"channel = ${len(args)}")
        if intent:
            args.append(f"%{intent}%")
            conditions.append(f"intent ILIKE ${len(args)}")
        if date_from:
            args.append(date_from)
            conditions.append(f"created_at >= ${len(args)}::timestamptz")
        if date_to:
            args.append(date_to)
            conditions.append(f"created_at <= ${len(args)}::timestamptz")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        offset = (page - 1) * per_page

        count_row = await conn.fetchrow(f"SELECT COUNT(*) FROM audit_logs {where}", *args)
        total = count_row["count"] if count_row else 0

        rows = await conn.fetch(
            f"""SELECT id, session_id, tenant_id, channel, user_message,
                       bot_response, intent, status, created_at
                FROM audit_logs {where}
                ORDER BY created_at DESC
                LIMIT {per_page} OFFSET {offset}""",
            *args,
        )

        return {
            "items": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": max(1, -(-total // per_page)),
        }
    except Exception as e:
        return {"items": [], "total": 0, "page": page, "per_page": per_page, "pages": 1, "warning": str(e)}
    finally:
        await conn.close()


@router.get("/export")
async def export_csv(
    tenant_id: Optional[str] = None,
    channel: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    conn = await get_conn()
    try:
        conditions = []
        args = []
        if tenant_id:
            args.append(tenant_id)
            conditions.append(f"tenant_id = ${len(args)}")
        if channel:
            args.append(channel)
            conditions.append(f"channel = ${len(args)}")
        if date_from:
            args.append(date_from)
            conditions.append(f"created_at >= ${len(args)}::timestamptz")
        if date_to:
            args.append(date_to)
            conditions.append(f"created_at <= ${len(args)}::timestamptz")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = await conn.fetch(
            f"""SELECT session_id, tenant_id, channel, user_message,
                       bot_response, intent, status, created_at
                FROM audit_logs {where}
                ORDER BY created_at DESC LIMIT 10000""",
            *args,
        )

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "session_id", "tenant_id", "channel", "user_message",
            "bot_response", "intent", "status", "created_at"
        ])
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))

        output.seek(0)
        filename = f"logs_{tenant_id or 'all'}_{date_from or 'all'}.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        await conn.close()
