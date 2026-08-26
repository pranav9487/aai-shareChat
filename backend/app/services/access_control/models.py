"""Access-control domain types: tiers, roles, and the user record.

Tier names intentionally mirror ``ALLOWED_ACCESS_LEVELS`` in
``app.services.rag.ingestion`` — those strings are what land in chunk
metadata, so the RBAC vocabulary must never drift from them (a unit test
asserts the two sets stay identical).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AccessTier(StrEnum):
    """Document sensitivity levels, matching stored chunk metadata."""

    GENERAL = "general"
    HR = "hr"
    RESTRICTED = "restricted"
    MANAGEMENT = "management"


class Role(StrEnum):
    """Employee roles recognized by the v1 directory."""

    EMPLOYEE = "employee"
    HR = "hr"
    MANAGER = "manager"
    EXECUTIVE = "executive"


#: Role → tiers that role may read. Single source of truth for RBAC mapping.
ROLE_ALLOWED_TIERS: dict[Role, frozenset[AccessTier]] = {
    Role.EMPLOYEE: frozenset({AccessTier.GENERAL}),
    Role.HR: frozenset({AccessTier.GENERAL, AccessTier.HR}),
    Role.MANAGER: frozenset({AccessTier.GENERAL, AccessTier.MANAGEMENT}),
    Role.EXECUTIVE: frozenset(set(AccessTier)),
}


@dataclass(frozen=True)
class User:
    """An identified application user and their access role."""

    user_id: str
    display_name: str
    role: Role

    @property
    def allowed_tiers(self) -> frozenset[str]:
        """Tier names this user may read, as plain strings for store filters."""
        return frozenset(tier.value for tier in ROLE_ALLOWED_TIERS[self.role])
