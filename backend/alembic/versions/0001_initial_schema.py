"""Initial schema for agents, scripts, jobs, artifacts, detections

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-30 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. agents table
    op.create_table(
        "agents",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("os", sa.String(length=64), nullable=False),
        sa.Column("arch", sa.String(length=32), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("version", sa.String(length=32), nullable=True),
        sa.Column("cert_fingerprint", sa.String(length=128), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agents_id", "agents", ["id"], unique=False)
    op.create_index("ix_agents_hostname", "agents", ["hostname"], unique=False)
    op.create_index("ix_agents_os", "agents", ["os"], unique=False)
    op.create_index("ix_agents_status", "agents", ["status"], unique=False)
    op.create_index("ix_agents_last_seen", "agents", ["last_seen"], unique=False)

    # 2. scripts table
    op.create_table(
        "scripts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scripts_id", "scripts", ["id"], unique=False)
    op.create_index("ix_scripts_name", "scripts", ["name"], unique=False)

    # 3. jobs table
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("script_id", sa.String(length=64), nullable=True),
        sa.Column("agent_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("target_agents", sa.JSON(), nullable=True),
        sa.Column("plan", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_id", "jobs", ["id"], unique=False)
    op.create_index("ix_jobs_script_id", "jobs", ["script_id"], unique=False)
    op.create_index("ix_jobs_agent_id", "jobs", ["agent_id"], unique=False)
    op.create_index("ix_jobs_status", "jobs", ["status"], unique=False)
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"], unique=False)

    # 4. artifacts table
    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=True),
        sa.Column("agent_id", sa.String(length=64), nullable=True),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("target", sa.String(length=128), nullable=True),
        sa.Column("host_id", sa.String(length=128), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("collected_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_artifacts_id", "artifacts", ["id"], unique=False)
    op.create_index("ix_artifacts_job_id", "artifacts", ["job_id"], unique=False)
    op.create_index("ix_artifacts_agent_id", "artifacts", ["agent_id"], unique=False)
    op.create_index("ix_artifacts_type", "artifacts", ["type"], unique=False)
    op.create_index("ix_artifacts_target", "artifacts", ["target"], unique=False)
    op.create_index("ix_artifacts_collected_at", "artifacts", ["collected_at"], unique=False)

    # 5. detections table
    op.create_table(
        "detections",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=True),
        sa.Column("agent_id", sa.String(length=64), nullable=True),
        sa.Column("rule_id", sa.String(length=255), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("dedup_key", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_detections_id", "detections", ["id"], unique=False)
    op.create_index("ix_detections_job_id", "detections", ["job_id"], unique=False)
    op.create_index("ix_detections_agent_id", "detections", ["agent_id"], unique=False)
    op.create_index("ix_detections_rule_id", "detections", ["rule_id"], unique=False)
    op.create_index("ix_detections_severity", "detections", ["severity"], unique=False)
    op.create_index("ix_detections_status", "detections", ["status"], unique=False)
    op.create_index("ix_detections_dedup_key", "detections", ["dedup_key"], unique=False)
    op.create_index("ix_detections_created_at", "detections", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("detections")
    op.drop_table("artifacts")
    op.drop_table("jobs")
    op.drop_table("scripts")
    op.drop_table("agents")
