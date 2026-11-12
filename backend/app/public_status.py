"""Privacy-limited response fields for unauthenticated correction requesters."""

from typing import Any


_CORRECTION_STATUS_MESSAGES = {
    "received": "Your request has been received and is awaiting review.",
    "investigating": "Your request is being reviewed.",
    "resolved": "The review is complete. Any applicable record correction has been applied.",
    "rejected": "The review is complete. No correction was applied based on the available information.",
}


def public_correction_status(request: Any) -> dict[str, str]:
    """Return a minimal public status; never serialize investigator free text."""
    status = request.status if request.status in _CORRECTION_STATUS_MESSAGES else "investigating"
    return {
        "request_ref": request.request_ref,
        "status": status,
        "status_message": _CORRECTION_STATUS_MESSAGES.get(
            status, "Your request status is being reviewed."
        ),
        "created_at": request.created_at.isoformat(),
        "updated_at": request.updated_at.isoformat(),
    }
