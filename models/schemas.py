from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ─────────────────────────────────────────
# REQUEST / RESPONSE
# ─────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., description="User message")


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    structured_output: Optional["StructuredDesignOutput"] = None


# ─────────────────────────────────────────
# AGENT OUTPUTS
# ─────────────────────────────────────────

class RequirementsOutput(BaseModel):
    functional_requirements: list[str]
    non_functional_requirements: list[str]
    constraints: list[str]
    scale_estimation: str
    summary: str


class ArchitectureOutput(BaseModel):
    architecture_style: str
    services: list[dict]
    tradeoffs: list[str]
    tech_stack: dict
    summary: str


class DatabaseOutput(BaseModel):
    entities: list[dict]
    relationships: list[str]
    mysql_schema_sql: str
    erd_mermaid: str
    summary: str


class ApiDesignOutput(BaseModel):
    endpoints: list[dict]
    spring_security_config: str
    api_mermaid_diagram: str
    docker_compose_snippet: str
    summary: str


# ─────────────────────────────────────────
# FINAL STRUCTURED OUTPUT
# ─────────────────────────────────────────

class StructuredDesignOutput(BaseModel):
    requirements: Optional[RequirementsOutput] = None
    architecture: Optional[ArchitectureOutput] = None
    database: Optional[DatabaseOutput] = None
    api_design: Optional[ApiDesignOutput] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────
# DB RECORD
# ─────────────────────────────────────────

class MessageRecord(BaseModel):
    id: Optional[int] = None
    session_id: str
    role: str
    content: str
    created_at: Optional[datetime] = None


ChatResponse.model_rebuild()