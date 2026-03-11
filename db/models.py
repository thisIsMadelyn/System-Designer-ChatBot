from sqlalchemy import (
    Column, Integer, String, Text,
    DateTime, ForeignKey, func
)
from sqlalchemy.orm import relationship
from db.database import Base


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String(255), nullable=False)
    username      = Column(String(255), nullable=False)
    email         = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(512), nullable=False)
    created_at    = Column(DateTime, server_default=func.now())

    projects    = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    # Προστέθηκε — χρειάζεται για το InputForm.user relationship
    input_forms = relationship("InputForm", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name        = Column(String(255), nullable=False)
    description = Column(Text)
    created_at  = Column(DateTime, server_default=func.now())

    user        = relationship("User", back_populates="projects")
    input_forms = relationship("InputForm", back_populates="project", cascade="all, delete-orphan")


class InputForm(Base):
    __tablename__ = "input_forms"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    # Προστέθηκε user_id — υπάρχει στη MySQL αλλά έλειπε από το model
    user_id             = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id          = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    project_description = Column(Text, nullable=False)
    team_size           = Column(String(50))
    scale               = Column(String(100))
    deadline            = Column(String(100))
    tech_constraints    = Column(Text)
    capital_constraints = Column(String(100))
    extra_details       = Column(Text)
    result_json         = Column(Text)
    created_at          = Column(DateTime, server_default=func.now())

    project = relationship("Project", back_populates="input_forms")
    user    = relationship("User", back_populates="input_forms")


class ConversationMessage(Base):
        __tablename__ = "conversations"

        id = Column(Integer, primary_key=True, autoincrement=True)
        session_id = Column(String(255), nullable=False, index=True)
        role = Column(String(50), nullable=False)
        content = Column(Text, nullable=False)
        created_at = Column(DateTime, server_default=func.now())