from datetime import date,datetime, timezone

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    Integer,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import func

class Base(DeclarativeBase):
    pass


# ============================================================
# MEETING
# ============================================================

class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    audio_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    transcript: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    decisions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    action_items: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    processing_status: Mapped[str] = mapped_column(
    String(50),
    nullable=False,
    default="Analyzed"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # --------------------------------------------------------
    # Relationships
    # --------------------------------------------------------

    participants: Mapped[list["Participant"]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan"
    )

    action_item_records: Mapped[list["ActionItem"]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan"
    )


# ============================================================
# PARTICIPANT
# ============================================================

class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    meeting_id: Mapped[int] = mapped_column(
        ForeignKey(
            "meetings.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    meeting: Mapped["Meeting"] = relationship(
        back_populates="participants"
    )


# ============================================================
# ACTION ITEM
# ============================================================

class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    meeting_id: Mapped[int] = mapped_column(
        ForeignKey(
            "meetings.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    task: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    owner: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    deadline: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    reminder_deadline: Mapped[datetime | None] = mapped_column(
    Date,
    nullable=True
    )

    last_reminded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Pending"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # --------------------------------------------------------
    # Relationship
    # --------------------------------------------------------

    meeting: Mapped["Meeting"] = relationship(
        back_populates="action_item_records"
    )

# ============================================================
# REMINDER RECIPIENT
# ============================================================

class ReminderRecipient(Base):
    __tablename__ = "reminder_recipients"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )


class ReminderLog(Base):
    __tablename__ = "reminder_logs"

    __table_args__ = (
        {
            "comment": "Tracks automatic action-item reminder attempts"
        },
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    action_item_id: Mapped[int] = mapped_column(
        ForeignKey("action_items.id", ondelete="CASCADE"),
        nullable=False
    )

    reminder_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    scheduled_for: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Pending"
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
