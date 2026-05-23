"""SQLAlchemy database models."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    generations = relationship("Generation", back_populates="project", cascade="all, delete-orphan")


class Generation(Base):
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    prompt = Column(Text, nullable=False)
    part_type = Column(String(50), nullable=False)
    parameters = Column(Text, default="{}")
    stl_path = Column(String(500), default="")
    step_path = Column(String(500), default="")
    cad_code = Column(Text, default="")
    status = Column(String(20), default="pending")
    error_message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="generations")
