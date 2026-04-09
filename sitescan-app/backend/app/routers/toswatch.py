"""ToSWatch API endpoints."""

from fastapi import APIRouter

from app.services.toswatch.monitor import (
    get_monitored_services,
    get_recent_changes,
    run_tos_check,
)
from app.services.toswatch.targets import TARGETS

router = APIRouter(prefix="/api/toswatch", tags=["toswatch"])


@router.get("/services")
async def list_services():
    """List all monitored services."""
    return await get_monitored_services()


@router.get("/changes")
async def list_changes(limit: int = 20):
    """List recent ToS changes."""
    return await get_recent_changes(limit=limit)


@router.get("/targets")
async def list_targets():
    """List monitoring targets (static config)."""
    return TARGETS


@router.post("/check")
async def trigger_check():
    """Manually trigger a ToS check for all targets."""
    changes = await run_tos_check()
    return {
        "checked": len(TARGETS),
        "changes_detected": len(changes),
        "changes": changes,
    }
