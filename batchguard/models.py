"""Data model for electronic batch records (eBR).

Records are never deleted or overwritten: a correction creates a new entry that supersedes the old one,
and every change is written to an append-only, hash-chained audit trail.
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    full_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))  # operator | supervisor | qa | admin
    password_hash: Mapped[str] = mapped_column(String(200))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)


class Template(Base):
    """Master batch record: the approved recipe that every batch of a product must follow."""

    __tablename__ = "templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    product: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(20))
    steps: Mapped[list["TemplateStep"]] = relationship(order_by="TemplateStep.seq")


class TemplateStep(Base):
    __tablename__ = "template_steps"
    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id"))
    seq: Mapped[int] = mapped_column(Integer)
    instruction: Mapped[str] = mapped_column(Text)
    parameter: Mapped[str] = mapped_column(String(50))
    unit: Mapped[str] = mapped_column(String(20))
    min_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    critical: Mapped[bool] = mapped_column(Boolean, default=False)  # critical steps need a second-person verification


class Batch(Base):
    __tablename__ = "batches"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_no: Mapped[str] = mapped_column(String(30), unique=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id"))
    status: Mapped[str] = mapped_column(String(20), default="in_progress")  # in_progress | in_review | released | rejected
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    template: Mapped[Template] = relationship()


class StepEntry(Base):
    __tablename__ = "step_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    step_id: Mapped[int] = mapped_column(ForeignKey("template_steps.id"))
    value: Mapped[float] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(DateTime)  # when the operator says it happened
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)  # server time: cannot be edited
    recorded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    superseded_by: Mapped[int | None] = mapped_column(ForeignKey("step_entries.id"), nullable=True)
    correction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    step: Mapped[TemplateStep] = relationship()


class Signature(Base):
    """21 CFR 11.50: every signature shows the printed name, date/time, and meaning."""

    __tablename__ = "signatures"
    id: Mapped[int] = mapped_column(primary_key=True)
    record_type: Mapped[str] = mapped_column(String(30))  # step_entry | deviation | batch
    record_id: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    printed_name: Mapped[str] = mapped_column(String(100))
    meaning: Mapped[str] = mapped_column(String(30))  # performed | verified | reviewed | approved_release | closed
    signed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Deviation(Base):
    __tablename__ = "deviations"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    step_entry_id: Mapped[int | None] = mapped_column(ForeignKey("step_entries.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(10), default="major")  # minor | major | critical
    status: Mapped[str] = mapped_column(String(10), default="open")  # open | closed
    raised_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    closure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuditEvent(Base):
    """Append-only. Each row stores the hash of the previous row, so any edit or deletion breaks the chain."""

    __tablename__ = "audit_trail"
    id: Mapped[int] = mapped_column(primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    username: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(40))
    entity: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    prev_hash: Mapped[str] = mapped_column(String(64))
    hash: Mapped[str] = mapped_column(String(64))


def make_session_factory(url: str = "sqlite:///batchguard.sqlite3"):
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)
