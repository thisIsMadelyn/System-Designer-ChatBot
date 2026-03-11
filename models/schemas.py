from pydantic import BaseModel
from typing import Optional


# ── Input ─────────────────────────────────────────────────────

class DesignRequest(BaseModel):
    project_description:  str
    team_size:            Optional[str] = None
    scale:                Optional[str] = None
    deadline:             Optional[str] = None
    tech_constraints:     Optional[str] = None
    capital_constraints:  Optional[str] = None
    extra_details:        Optional[str] = None

    def build_prompt(self) -> str:
        lines = [f"Project Description: {self.project_description}"]
        if self.team_size:           lines.append(f"Team Size: {self.team_size}")
        if self.scale:               lines.append(f"Expected Scale: {self.scale}")
        if self.deadline:            lines.append(f"Deadline: {self.deadline}")
        if self.tech_constraints:    lines.append(f"Tech Constraints: {self.tech_constraints}")
        if self.capital_constraints: lines.append(f"Budget: {self.capital_constraints}")
        if self.extra_details:       lines.append(f"Extra Details: {self.extra_details}")
        return "\n".join(lines)


# ── Agent 1: System Analyst ───────────────────────────────────

class SystemAnalystOutput(BaseModel):
    summary:      str
    requirements: list[str]
    tech_stack:   dict
    agent_plan:   list[str]


# ── Agent 2: Architect ────────────────────────────────────────

class ArchitectOutput(BaseModel):
    summary:           str
    package_structure: str        # ASCII tree
    design_patterns:   list[str]
    uml_class:         str        # PlantUML
    uml_sequence:      str        # PlantUML
    tech_versions:     dict


# ── Agent 3: Database ─────────────────────────────────────────

class EntityField(BaseModel):
    name:        str
    type:        str
    annotations: list[str] = []

class EntityDefinition(BaseModel):
    name:   str
    table:  str
    fields: list[EntityField]

class DatabaseAgentOutput(BaseModel):
    summary:                str
    entities:               list[dict]   # list of EntityDefinition-like dicts
    relationships:          list[str]
    java_code:              str
    application_properties: str


# ── Agent 4: Backend Layer (Service + Controller merged) ──────

class BackendLayerOutput(BaseModel):
    summary:        str
    dto_code:       str   # all DTOs
    service_code:   str   # interfaces + implementations
    exception_code: str   # exceptions + GlobalExceptionHandler
    controller_code: str  # REST controllers
    swagger_config: str   # OpenAPI config


# ── Agent 5: DevOps ───────────────────────────────────────────

class DevOpsOutput(BaseModel):
    summary:        str
    dockerfile:     str
    docker_compose: str
    dockerignore:   str
    readme:         str


# ── Agent 6: Testing ──────────────────────────────────────────

class TestingOutput(BaseModel):
    summary:           str
    unit_tests:        str
    test_report:       str
    errors:            list[dict]   # [{file, line, description, cause}]
    coverage_estimate: str


# ── Final Microservice Output ─────────────────────────────────

class MicroserviceOutput(BaseModel):
    system_analyst:  Optional[SystemAnalystOutput]  = None
    architect:       Optional[ArchitectOutput]       = None
    database:        Optional[DatabaseAgentOutput]   = None
    backend_layer:   Optional[BackendLayerOutput]    = None
    devops:          Optional[DevOpsOutput]          = None
    testing:         Optional[TestingOutput]         = None
    final_summary:   str = ""


# ── Legacy (chat_router compatibility) ───────────────────────

class RequirementsOutput(BaseModel):
    summary:                 str = ""
    functional_requirements: list[str] = []
    non_functional:          list[str] = []
    constraints:             list[str] = []
    scale_estimation:        str = ""

class ArchitectureOutput(BaseModel):
    summary:            str = ""
    architecture_style: str = ""
    services:           list[dict] = {}
    tech_stack:         dict = {}
    tradeoffs:          dict = {}

class DatabaseOutput(BaseModel):
    summary:       str = ""
    entities:      list[dict] = []
    relationships: list[str] = []
    mermaid_erd:   str = ""
    sql_schema:    str = ""

class ApiDesignOutput(BaseModel):
    summary:   str = ""
    endpoints: list[dict] = []
    security:  dict = {}
    docker:    str = ""

class StructuredDesignOutput(BaseModel):
    requirements: Optional[RequirementsOutput] = None
    architecture: Optional[ArchitectureOutput] = None
    database:     Optional[DatabaseOutput]     = None
    api_design:   Optional[ApiDesignOutput]    = None