
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_usage import LLMRequest

logger = logging.getLogger(__name__)


class UsageTrackingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record_llm_request(
        self,
        user_id: Any,
        conversation_id: Any | None,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: int,
        status: str = "success",
        error_message: str | None = None,
        cached: bool = False,
        streaming: bool = False,
        agent_type: str | None = None,
        request_type: str = "chat",
        cost_usd: float = 0.0,
        metadata: dict | None = None,
    ) -> LLMRequest:
        total = prompt_tokens + completion_tokens
        record = LLMRequest(
            user_id=user_id,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            request_type=request_type,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            cached=1 if cached else 0,
            streaming=1 if streaming else 0,
            agent_type=agent_type,
            metadata_=metadata,
            requested_at=datetime.now(timezone.utc),
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_usage_summary(self, user_id: Any | None = None, days: int = 30) -> dict:
        base = select(func.count(), func.sum(LLMRequest.total_tokens), func.sum(LLMRequest.cost_usd), func.avg(LLMRequest.duration_ms), func.sum(LLMRequest.prompt_tokens), func.sum(LLMRequest.completion_tokens))
        if user_id:
            base = base.where(LLMRequest.user_id == user_id)
        row = (await self.db.execute(base.where(LLMRequest.requested_at >= datetime.now(timezone.utc) - timedelta(days=days)))).one()
        return {
            "total_requests": row[0] or 0,
            "total_tokens": row[1] or 0,
            "total_cost": round(float(row[2] or 0), 6),
            "avg_duration_ms": round(float(row[3] or 0), 2),
            "prompt_tokens": row[4] or 0,
            "completion_tokens": row[5] or 0,
        }

    async def get_cost_breakdown(self, user_id: Any | None = None) -> list[dict]:
        base = select(LLMRequest.provider, LLMRequest.model, func.sum(LLMRequest.cost_usd), func.count(), func.sum(LLMRequest.total_tokens))
        if user_id:
            base = base.where(LLMRequest.user_id == user_id)
        rows = (await self.db.execute(base.group_by(LLMRequest.provider, LLMRequest.model).order_by(func.sum(LLMRequest.cost_usd).desc()))).all()
        return [{"provider": r[0], "model": r[1], "cost": round(float(r[2] or 0), 6), "requests": r[3] or 0, "tokens": r[4] or 0} for r in rows]

    async def get_token_trend(self, user_id: Any | None = None, days: int = 30) -> list[dict]:
        base = select(func.date_trunc("day", LLMRequest.requested_at).label("day"), func.sum(LLMRequest.prompt_tokens), func.sum(LLMRequest.completion_tokens), func.count())
        if user_id:
            base = base.where(LLMRequest.user_id == user_id)
        rows = (await self.db.execute(base.where(LLMRequest.requested_at >= datetime.now(timezone.utc) - timedelta(days=days)).group_by(text("day")).order_by(text("day")))).all()
        return [{"date": str(r[0].date()) if hasattr(r[0], "date") else str(r[0]), "prompt_tokens": r[1] or 0, "completion_tokens": r[2] or 0, "requests": r[3] or 0} for r in rows]

    async def get_model_performance(self, user_id: Any | None = None) -> list[dict]:
        base = select(LLMRequest.provider, LLMRequest.model, func.count(), func.avg(LLMRequest.duration_ms), func.sum(LLMRequest.total_tokens), func.sum(LLMRequest.cost_usd))
        if user_id:
            base = base.where(LLMRequest.user_id == user_id)
        rows = (await self.db.execute(base.group_by(LLMRequest.provider, LLMRequest.model).order_by(func.count().desc()))).all()
        return [{"provider": r[0], "model": r[1], "requests": r[2] or 0, "avg_duration_ms": round(float(r[3] or 0), 2), "total_tokens": r[4] or 0, "cost": round(float(r[5] or 0), 6)} for r in rows]

    async def get_error_rate(self, user_id: Any | None = None) -> dict:
        total_q = select(func.count()).select_from(LLMRequest)
        failed_q = select(func.count()).select_from(LLMRequest).where(LLMRequest.status == "failed")
        if user_id:
            total_q = total_q.where(LLMRequest.user_id == user_id)
            failed_q = failed_q.where(LLMRequest.user_id == user_id)
        total = (await self.db.execute(total_q)).scalar() or 0
        failed = (await self.db.execute(failed_q)).scalar() or 0
        return {"total": total, "failed": failed, "error_rate": round(failed / total * 100, 2) if total > 0 else 0}

    async def get_dashboard_stats(self, user_id: Any) -> dict:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)

        base = LLMRequest.user_id == user_id

        today_q = select(func.count()).select_from(LLMRequest).where(base, LLMRequest.requested_at >= today_start)
        week_q = select(func.count()).select_from(LLMRequest).where(base, LLMRequest.requested_at >= week_start)
        month_q = select(func.count()).select_from(LLMRequest).where(base, LLMRequest.requested_at >= month_start)
        total_q = select(func.count()).select_from(LLMRequest).where(base)
        tokens_q = select(func.sum(LLMRequest.total_tokens), func.sum(LLMRequest.prompt_tokens), func.sum(LLMRequest.completion_tokens)).where(base)
        cost_q = select(func.sum(LLMRequest.cost_usd)).where(base)
        failed_q = select(func.count()).select_from(LLMRequest).where(base, LLMRequest.status == "failed")
        streaming_q = select(func.count()).select_from(LLMRequest).where(base, LLMRequest.streaming == 1)
        cached_q = select(func.count()).select_from(LLMRequest).where(base, LLMRequest.cached == 1)
        avg_dur_q = select(func.avg(LLMRequest.duration_ms)).where(base)
        today_cost_q = select(func.sum(LLMRequest.cost_usd)).where(base, LLMRequest.requested_at >= today_start)
        week_cost_q = select(func.sum(LLMRequest.cost_usd)).where(base, LLMRequest.requested_at >= week_start)
        month_cost_q = select(func.sum(LLMRequest.cost_usd)).where(base, LLMRequest.requested_at >= month_start)
        cost_per_conv_q = select(func.avg(LLMRequest.cost_usd)).where(base)

        today = (await self.db.execute(today_q)).scalar() or 0
        week = (await self.db.execute(week_q)).scalar() or 0
        month = (await self.db.execute(month_q)).scalar() or 0
        total = (await self.db.execute(total_q)).scalar() or 0
        tokens_row = (await self.db.execute(tokens_q)).one()
        total_cost = (await self.db.execute(cost_q)).scalar() or 0
        failed = (await self.db.execute(failed_q)).scalar() or 0
        streaming = (await self.db.execute(streaming_q)).scalar() or 0
        cached = (await self.db.execute(cached_q)).scalar() or 0
        avg_dur = (await self.db.execute(avg_dur_q)).scalar() or 0
        today_cost = (await self.db.execute(today_cost_q)).scalar() or 0
        week_cost = (await self.db.execute(week_cost_q)).scalar() or 0
        month_cost = (await self.db.execute(month_cost_q)).scalar() or 0
        avg_cost = (await self.db.execute(cost_per_conv_q)).scalar() or 0

        return {
            "total_requests": total,
            "today_requests": today,
            "weekly_requests": week,
            "monthly_requests": month,
            "total_tokens": tokens_row[0] or 0,
            "prompt_tokens": tokens_row[1] or 0,
            "completion_tokens": tokens_row[2] or 0,
            "total_cost": round(float(total_cost), 6),
            "today_cost": round(float(today_cost), 6),
            "weekly_cost": round(float(week_cost), 6),
            "monthly_cost": round(float(month_cost), 6),
            "failed_requests": failed,
            "streaming_requests": streaming,
            "cached_requests": cached,
            "avg_duration_ms": round(float(avg_dur), 2),
            "avg_cost_per_conversation": round(float(avg_cost), 6),
        }

    async def get_storage_stats(self, user_id: Any) -> dict:
        from app.models.document import Document
        total_q = select(func.sum(Document.file_size)).where(Document.user_id == user_id, Document.is_deleted == False)
        count_q = select(func.count()).select_from(Document).where(Document.user_id == user_id, Document.is_deleted == False)
        today_q = select(func.count()).select_from(Document).where(Document.user_id == user_id, Document.is_deleted == False, Document.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0))
        total_size = (await self.db.execute(total_q)).scalar() or 0
        total_docs = (await self.db.execute(count_q)).scalar() or 0
        today_uploads = (await self.db.execute(today_q)).scalar() or 0
        return {
            "total_storage_bytes": total_size,
            "total_documents": total_docs,
            "uploaded_today": today_uploads,
        }
