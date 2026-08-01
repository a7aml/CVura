import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base
from app.models.awards import Award
from app.models.certifications import Certification
from app.models.education import Education
from app.models.experiences import Experience
from app.models.languages import Language
from app.models.projects import Project
from app.models.skills import Skill


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String, nullable=True)
    github_url: Mapped[str | None] = mapped_column(String, nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String, nullable=True)
    desired_title: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    career_objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    education: Mapped[list[Education]] = relationship(lazy="noload")
    experiences: Mapped[list[Experience]] = relationship(lazy="noload")
    projects: Mapped[list[Project]] = relationship(lazy="noload")
    skills: Mapped[list[Skill]] = relationship(lazy="noload")
    certifications: Mapped[list[Certification]] = relationship(lazy="noload")
    languages: Mapped[list[Language]] = relationship(lazy="noload")
    awards: Mapped[list[Award]] = relationship(lazy="noload")
