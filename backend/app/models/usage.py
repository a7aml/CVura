import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Usage(Base):
    __tablename__ = "usage"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    resumes_generated_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    plan_limit: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    reset_at: Mapped[datetime | None] = mapped_column(nullable=True)
