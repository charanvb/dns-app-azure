"""SQLAlchemy ORM models for the DNS self-service portal.

All tables live in a dedicated, isolated Postgres database — see
db/provision_dns_selfservice_db.sql. Nothing here is shared with any other app.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Role(str, enum.Enum):
    """The 3 AD groups map 1:1 to these roles."""

    REQUESTER = "requester"
    ZONE_ADMIN = "zone_admin"
    CLOUDOPS_ADMIN = "cloudops_admin"


class RequestAction(str, enum.Enum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


class RequestStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_REJECTED = "auto_rejected"
    QUEUED = "queued"
    IMPLEMENTED = "implemented"
    FAILED = "failed"


class ApprovalDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class QueueStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, name="role_enum"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    zone_scopes: Mapped[list["ZoneAdminScope"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class ZoneAdminScope(Base):
    """Zones a zone_admin user is permitted to approve requests for.

    cloudops_admin users are not listed here — they implicitly approve all zones.
    """

    __tablename__ = "zone_admin_scopes"
    __table_args__ = (UniqueConstraint("user_id", "zone_name", name="uq_zone_admin_scope"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    zone_name: Mapped[str] = mapped_column(String(255), index=True)

    user: Mapped["User"] = relationship(back_populates="zone_scopes")


class CriticalZone(Base):
    """Zones that require admin approval before changes are implemented.

    Absence of a row (or is_critical=False) means the zone is non-critical and
    requests auto-implement.
    """

    __tablename__ = "critical_zones"

    zone_name: Mapped[str] = mapped_column(String(255), primary_key=True)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DnsRequest(Base):
    """A user-submitted DNS change request, possibly bundling several record items."""

    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    zone_name: Mapped[str] = mapped_column(String(255), index=True)
    action: Mapped[RequestAction] = mapped_column(Enum(RequestAction, name="request_action_enum"))
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status_enum"), default=RequestStatus.QUEUED, index=True
    )
    is_critical_snapshot: Mapped[bool] = mapped_column(Boolean, default=False)
    justification: Mapped[str] = mapped_column(Text)
    requester_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list["RequestItem"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )
    approvals: Mapped[list["Approval"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )


class RequestItem(Base):
    """A single record change within a request (create/modify/delete of one label+type)."""

    __tablename__ = "request_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(253))
    record_type: Mapped[str] = mapped_column(String(10))
    ttl: Mapped[int] = mapped_column(Integer, default=300)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    result_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    request: Mapped["DnsRequest"] = relationship(back_populates="items")


class Approval(Base):
    """Decision history for a request (supports multiple approvers / resubmission)."""

    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"))
    approver_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[ApprovalDecision] = mapped_column(
        Enum(ApprovalDecision, name="approval_decision_enum")
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    request: Mapped["DnsRequest"] = relationship(back_populates="approvals")


class ExecutionQueueItem(Base):
    """DB-backed work queue drained by the background poller (no Celery/Redis needed)."""

    __tablename__ = "execution_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("requests.id", ondelete="CASCADE"), unique=True
    )
    status: Mapped[QueueStatus] = mapped_column(
        Enum(QueueStatus, name="queue_status_enum"), default=QueueStatus.QUEUED, index=True
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AuditLog(Base):
    """Full compliance trail — every state change and admin action."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int | None] = mapped_column(
        ForeignKey("requests.id", ondelete="SET NULL"), nullable=True
    )
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class NotificationLog(Base):
    """Records every email sent via the Logic App trigger, for troubleshooting/audit."""

    __tablename__ = "notifications_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int | None] = mapped_column(
        ForeignKey("requests.id", ondelete="SET NULL"), nullable=True
    )
    recipient: Mapped[str] = mapped_column(String(254))
    template: Mapped[str] = mapped_column(String(64))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(20))
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class RateLimitEntry(Base):
    """Persisted submission timestamps for per-user rate limiting (2 changes / 24h)."""

    __tablename__ = "rate_limit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    action_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
