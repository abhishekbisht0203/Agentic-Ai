"""
API routers module.

Centralizes all API route registration.
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .documents import router as documents_router
from .knowledge_bases import router as knowledge_bases_router
from .chat import router as chat_router
from .memory import router as memory_router
from .workflows import router as workflows_router
from .tasks import router as tasks_router
from .agents import router as agents_router
from .analytics import router as analytics_router
from .admin import router as admin_router
from .settings import router as settings_router
from .public_stats import router as public_stats_router
from .agent_ws import router as agent_ws_router
from .usage_analytics import router as usage_analytics_router
from .agent_platform import router as agent_platform_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(documents_router)
api_router.include_router(knowledge_bases_router)
api_router.include_router(chat_router)
api_router.include_router(memory_router)
api_router.include_router(workflows_router)
api_router.include_router(tasks_router)
api_router.include_router(agents_router)
api_router.include_router(analytics_router)
api_router.include_router(usage_analytics_router)
api_router.include_router(agent_platform_router)
api_router.include_router(admin_router)
api_router.include_router(settings_router)
api_router.include_router(public_stats_router)
api_router.include_router(agent_ws_router)

__all__ = ["api_router"]
