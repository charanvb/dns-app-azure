"""Initial schema — users, roles/scopes, requests, approvals, queue, audit, notifications.

Revision ID: 0001
Revises:
Create Date: 2026-08-06

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    role_enum = sa.Enum("requester", "zone_admin", "cloudops_admin", name="role_enum")
    request_action_enum = sa.Enum("create", "modify", "delete", name="request_action_enum")
    request_status_enum = sa.Enum(
        "pending_approval", "approved", "rejected", "auto_rejected",
        "queued", "implemented", "failed", name="request_status_enum",
    )
    approval_decision_enum = sa.Enum("approved", "rejected", name="approval_decision_enum")
    queue_status_enum = sa.Enum("queued", "processing", "done", "failed", name="queue_status_enum")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "zone_admin_scopes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("zone_name", sa.String(255), nullable=False),
        sa.UniqueConstraint("user_id", "zone_name", name="uq_zone_admin_scope"),
    )
    op.create_index("ix_zone_admin_scopes_zone_name", "zone_admin_scopes", ["zone_name"])

    op.create_table(
        "critical_zones",
        sa.Column("zone_name", sa.String(255), primary_key=True),
        sa.Column("is_critical", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("requester_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("zone_name", sa.String(255), nullable=False),
        sa.Column("action", request_action_enum, nullable=False),
        sa.Column("status", request_status_enum, nullable=False, server_default="queued"),
        sa.Column("is_critical_snapshot", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("requester_ip", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reject_reason", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_requests_zone_name", "requests", ["zone_name"])
    op.create_index("ix_requests_status", "requests", ["status"])
    op.create_index("ix_requests_created_at", "requests", ["created_at"])

    op.create_table(
        "request_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(253), nullable=False),
        sa.Column("record_type", sa.String(10), nullable=False),
        sa.Column("ttl", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("result_status", sa.String(20), nullable=True),
        sa.Column("result_message", sa.Text(), nullable=True),
    )

    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approver_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", approval_decision_enum, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "execution_queue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("status", queue_status_enum, nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_execution_queue_status", "execution_queue", ["status"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("requests.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])

    op.create_table(
        "notifications_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("requests.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recipient", sa.String(254), nullable=False),
        sa.Column("template", sa.String(64), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
    )

    op.create_table(
        "rate_limit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_rate_limit_log_user_id", "rate_limit_log", ["user_id"])
    op.create_index("ix_rate_limit_log_action_at", "rate_limit_log", ["action_at"])


def downgrade() -> None:
    op.drop_table("rate_limit_log")
    op.drop_table("notifications_log")
    op.drop_table("audit_log")
    op.drop_table("execution_queue")
    op.drop_table("approvals")
    op.drop_table("request_items")
    op.drop_table("requests")
    op.drop_table("critical_zones")
    op.drop_table("zone_admin_scopes")
    op.drop_table("users")

    sa.Enum(name="queue_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="approval_decision_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="request_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="request_action_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="role_enum").drop(op.get_bind(), checkfirst=True)
