"""Safe follow-up handling (roadmap Now §4). See ADR-0009."""

from app.services.followup.models import ResolvedQuestion
from app.services.followup.resolver import (
    FollowUpResolver,
    HeuristicFollowUpResolver,
    get_heuristic_resolver,
)

__all__ = [
    "ResolvedQuestion",
    "FollowUpResolver",
    "HeuristicFollowUpResolver",
    "get_heuristic_resolver",
]
