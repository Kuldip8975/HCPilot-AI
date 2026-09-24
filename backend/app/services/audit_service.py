"""Audit service - a thin, easy-to-call wrapper around AuditRepository.

The AuditLog model and repository already existed in this codebase but
were never actually used anywhere (dead scaffolding). This service is
what other services/endpoints call after a write succeeds, so every
create/update to sensitive data (interactions, follow-ups, HCPs) leaves
an immutable record of who did what and when - the compliance/audit
trail a real pharma CRM needs.
"""

import logging
from typing import Any, Dict, Optional

from app.repositories.audit_repository import AuditRepository
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Writes audit log entries. Never raises - a failed audit write
    should never break the actual business operation that triggered it."""

    def __init__(self, audit_repo: AuditRepository):
        self.audit_repo = audit_repo

    async def log(
        self,
        user_id: Optional[str],
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record one audit event.

        action: short verb, e.g. "create", "update", "complete".
        resource: what kind of thing, e.g. "interaction", "followup", "hcp".
        resource_id: the affected row's id.
        changes: the new/changed field values (kept small and JSON-safe).
        """
        try:
            entry = AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                resource_id=str(resource_id) if resource_id else None,
                changes=changes,
                details=details,
            )
            await self.audit_repo.create(entry)
        except Exception as e:
            # Audit logging is best-effort - a logging failure must never
            # roll back or fail the actual operation the user is doing.
            logger.error(f"Failed to write audit log ({action} {resource}): {str(e)}", exc_info=True)