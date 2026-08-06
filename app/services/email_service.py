"""Sends transactional email via the shared Logic App HTTP trigger.

Payload contract matches the existing PowerShell caller used elsewhere:
{"Message": ..., "Subject": ..., "ToEmail": ..., "Attachments": [...]}.
"""

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import NotificationLog

_TIMEOUT_SECONDS = 15.0


def send_email(
    db: Session,
    *,
    to_email: str,
    subject: str,
    message: str,
    template: str,
    request_id: int | None = None,
    attachments: list[dict] | None = None,
) -> None:
    """Posts to the Logic App trigger and records the outcome in notifications_log.

    Never raises — a failed notification must not block the caller's DB transaction.
    """
    payload: dict = {"Message": message, "Subject": subject, "ToEmail": to_email}
    if attachments:
        payload["Attachments"] = attachments

    status = "sent"
    error: str | None = None
    try:
        response = httpx.post(settings.logic_app_email_url, json=payload, timeout=_TIMEOUT_SECONDS)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        status = "failed"
        error = str(exc)

    db.add(
        NotificationLog(
            request_id=request_id,
            recipient=to_email,
            template=template,
            status=status,
            error=error,
        )
    )
    db.commit()
