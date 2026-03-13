from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import json
from fastapi.responses import StreamingResponse
import asyncio

from db.database import get_db
from db.models import Project, InputForm, User
from auth.auth_router import get_current_user


router = APIRouter(prefix="/api/projects", tags=["projects"])


# ── Pydantic schemas ──────────────────────────────────────────

class ProjectCreate(BaseModel):
    name:        str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id:          int
    name:        str
    description: Optional[str]
    created_at:  str

class InputFormCreate(BaseModel):
    project_description: str
    team_size:           Optional[str] = None
    scale:               Optional[str] = None
    deadline:            Optional[str] = None
    tech_constraints:    Optional[str] = None
    capital_constraints: Optional[str] = None
    extra_details:       Optional[str] = None

class InputFormResponse(BaseModel):
    id:                  int
    project_id:          int
    project_description: str
    team_size:           Optional[str]
    scale:               Optional[str]
    deadline:            Optional[str]
    tech_constraints:    Optional[str]
    capital_constraints: Optional[str]
    extra_details:       Optional[str]
    result_json:         Optional[str]
    created_at:          str


# ── Project CRUD ──────────────────────────────────────────────

# get method
@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user), # έτσι διαβάζει το JWT token
        #για να επαληθεύσει το χρήστη
        # για να συνδεθεί με την βάση δεδομένων
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            created_at=str(p.created_at),
        )
        for p in projects
    ]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = Project(
        user_id=current_user.id,
        name=body.name,
        description=body.description,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=str(project.created_at),
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=str(project.created_at),
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()


# ── Input Forms ───────────────────────────────────────────────

@router.get("/{project_id}/forms", response_model=list[InputFormResponse])
async def list_forms(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify project ownership
    proj = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    if not proj.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(InputForm)
        .where(InputForm.project_id == project_id)
        .order_by(InputForm.created_at.desc())
    )
    forms = result.scalars().all()
    return [_form_to_response(f) for f in forms]


@router.post("/{project_id}/forms", response_model=InputFormResponse, status_code=status.HTTP_201_CREATED)
async def create_form(
    project_id: int,
    body: InputFormCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    proj = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    if not proj.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    form = InputForm(
        project_id=project_id,
        project_description=body.project_description,
        team_size=body.team_size,
        scale=body.scale,
        deadline=body.deadline,
        tech_constraints=body.tech_constraints,
        capital_constraints=body.capital_constraints,
        extra_details=body.extra_details,
    )
    db.add(form)
    await db.commit()
    await db.refresh(form)
    return _form_to_response(form)


@router.patch("/{project_id}/forms/{form_id}/result")
async def save_form_result(
    project_id: int,
    form_id: int,
    result: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save the agent result JSON back to the input form."""
    proj = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
    )
    if not proj.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    res = await db.execute(
        select(InputForm).where(InputForm.id == form_id, InputForm.project_id == project_id)
    )
    form = res.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    form.result_json = json.dumps(result)
    await db.commit()
    return {"ok": True}


# ── Helper ────────────────────────────────────────────────────

def _form_to_response(f: InputForm) -> InputFormResponse:
    return InputFormResponse(
        id=f.id,
        project_id=f.project_id,
        project_description=f.project_description,
        team_size=f.team_size,
        scale=f.scale,
        deadline=f.deadline,
        tech_constraints=f.tech_constraints,
        capital_constraints=f.capital_constraints,
        extra_details=f.extra_details,
        result_json=f.result_json,
        created_at=str(f.created_at),
    )

from agents.orchestrator import run_orchestrator  # νέο import στην κορυφή


class RunPipelineRequest(BaseModel):
    project_description: str
    team_size:           Optional[str] = None
    scale:               Optional[str] = None
    deadline:            Optional[str] = None
    tech_constraints:    Optional[str] = None
    capital_constraints: Optional[str] = None
    extra_details:       Optional[str] = None
    history:             list[dict]    = []  # chat history για context


class RunPipelineResponse(BaseModel):
    form_id:          int         # το ID της νέας InputForm εγγραφής
    response:         str         # Markdown summary
    structured_output: Optional[dict]  # τα 6 agent outputs


# το run_pipeline κάνει 5 πράγματα
# ownership check
@router.post(
    "/{project_id}/run",
    response_model=RunPipelineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_pipeline(
    project_id: int,
    body: RunPipelineRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession   = Depends(get_db),
):
    """
    All-in-one endpoint:
    1. Επαληθεύει ότι το project ανήκει στον user
    2. Δημιουργεί InputForm εγγραφή
    3. Τρέχει το 6-agent pipeline
    4. Αποθηκεύει το result_json στη MySQL
    5. Επιστρέφει form_id + response + structured_output στο frontend
    """

    # ── 1. Ownership check ────────────────────────────────────
    proj_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if not proj_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    # ── 2. Δημιουργία InputForm (αρχικά χωρίς result) ────────
    form = InputForm(
        project_id          = project_id,
        user_id             =current_user.id,
        project_description = body.project_description,
        team_size           = body.team_size,
        scale               = body.scale,
        deadline            = body.deadline,
        tech_constraints    = body.tech_constraints,
        capital_constraints = body.capital_constraints,
        extra_details       = body.extra_details,
    )
    db.add(form)
    await db.commit()
    await db.refresh(form)

    # ── 3. Τρέχει το pipeline ─────────────────────────────────
    # Φτιάχνουμε το user_message συνδυάζοντας όλα τα fields
    user_message = _build_user_message(body)

    try:
        pipeline_result = await run_orchestrator(
            user_message = user_message,
            history      = body.history,
        )
    except Exception as e:
        # Αν αποτύχει το pipeline, διαγράφουμε τη form και επιστρέφουμε error
        await db.delete(form)
        await db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline error: {str(e)}"
        )

    # ── 4. Αποθήκευση result στη MySQL ────────────────────────
    if pipeline_result["structured_output"]:
        form.result_json = json.dumps(pipeline_result["structured_output"])
        await db.commit()

    # ── 5. Response στο frontend ──────────────────────────────
    return RunPipelineResponse(
        form_id           = form.id,
        response          = pipeline_result["response"],
        structured_output = pipeline_result["structured_output"],
    )


def _build_user_message(body: RunPipelineRequest) -> str:
    """
    Μετατρέπει τα form fields σε ένα καθαρό prompt για τους agents.
    """
    parts = [f"Design a Java microservice: {body.project_description}"]

    if body.team_size:
        parts.append(f"Team size: {body.team_size}")
    if body.scale:
        parts.append(f"Expected scale: {body.scale}")
    if body.deadline:
        parts.append(f"Deadline: {body.deadline}")
    if body.tech_constraints:
        parts.append(f"Tech constraints: {body.tech_constraints}")
    if body.capital_constraints:
        parts.append(f"Budget constraints: {body.capital_constraints}")
    if body.extra_details:
        parts.append(f"Extra details: {body.extra_details}")

    return "\n".join(parts)


@router.post(
    "/{project_id}/run/stream",
    status_code=status.HTTP_200_OK,
)
async def run_pipeline_stream(
        project_id: int,
        body: RunPipelineRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """
    SSE endpoint — στέλνει progress events καθώς τελειώνει κάθε agent.

    Events format (text/event-stream):
        data: {"type": "progress", "agent": "System Analyst", "step": 1, "total": 6}
        data: {"type": "progress", "agent": "Architect",      "step": 2, "total": 6}
        ...
        data: {"type": "done", "form_id": 5, "response": "...", "structured_output": {...}}
        data: {"type": "error", "message": "..."}
    """

    # ── Ownership check ───────────────────────────────────────
    proj_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id,
        )
    )
    if not proj_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    # ── Δημιουργία InputForm ──────────────────────────────────
    form = InputForm(
        project_id=project_id,
        user_id=current_user.id,
        project_description=body.project_description,
        team_size=body.team_size,
        scale=body.scale,
        deadline=body.deadline,
        tech_constraints=body.tech_constraints,
        capital_constraints=body.capital_constraints,
        extra_details=body.extra_details,
    )
    db.add(form)
    await db.commit()
    await db.refresh(form)
    form_id = form.id

    user_message = _build_user_message(body)
    history = body.history

    async def event_generator():
        """
        Generator που τρέχει τους agents έναν-έναν και στέλνει SSE events.
        Κάθε agent τρέχει ξεχωριστά ώστε να μπορούμε να στείλουμε progress.
        """
        from agents.system_anaylst import run_system_analyst
        from agents.architect import run_architect
        from agents.database import run_database_agent
        from agents.backend_layer import run_backend_layer
        from agents.devops import run_devops
        from agents.testing import run_testing
        from agents.llm_factory import get_llm
        from langchain_core.messages import HumanMessage
        from models.schemas import (
            MicroserviceOutput, SystemAnalystOutput, ArchitectOutput,
            DatabaseAgentOutput, BackendLayerOutput, DevOpsOutput, TestingOutput,
        )

        def sse(payload: dict) -> str:
            """Μετατρέπει dict σε SSE format."""
            return f"data: {json.dumps(payload)}\n\n"

        try:
            # ── Agent 1: System Analyst ───────────────────────
            yield sse({"type": "progress", "agent": "System Analyst", "step": 1, "total": 6, "pct": 0})
            system_analyst = await run_system_analyst(user_message)

            # ── Agent 2: Architect ────────────────────────────
            yield sse({"type": "progress", "agent": "Architect", "step": 2, "total": 6, "pct": 17})
            architect = await run_architect(user_message, system_analyst)

            # ── Agent 3: Database ─────────────────────────────
            yield sse({"type": "progress", "agent": "Database Agent", "step": 3, "total": 6, "pct": 33})
            database = await run_database_agent(user_message, system_analyst, architect)

            # ── Agent 4: Backend Layer ────────────────────────
            yield sse({"type": "progress", "agent": "Backend Layer", "step": 4, "total": 6, "pct": 50})
            backend_layer = await run_backend_layer(user_message, system_analyst, architect, database)

            # ── Agent 5: DevOps ───────────────────────────────
            yield sse({"type": "progress", "agent": "DevOps Engineer", "step": 5, "total": 6, "pct": 67})
            devops = await run_devops(user_message, system_analyst, architect)

            # ── Agent 6: Testing ──────────────────────────────
            yield sse({"type": "progress", "agent": "Testing Manager", "step": 6, "total": 6, "pct": 83})
            testing = await run_testing(user_message, system_analyst, database, backend_layer, backend_layer)

            # ── Summarizer ────────────────────────────────────
            yield sse({"type": "progress", "agent": "Finalizing...", "step": 6, "total": 6, "pct": 95})
            llm = get_llm(temperature=0.3)
            summary_response = await llm.ainvoke([HumanMessage(content=
                                                               f"Summarize this Java microservice design in clear markdown:\n"
                                                               f"System: {system_analyst.summary}\n"
                                                               f"Architecture: {architect.summary}\n"
                                                               f"Database: {database.summary}\n"
                                                               f"Backend: {backend_layer.summary}\n"
                                                               f"DevOps: {devops.summary}\n"
                                                               f"Testing: {testing.summary}\n"
                                                               f"Coverage: {testing.coverage_estimate}"
                                                               )])
            final_response = summary_response.content

            # ── Αποθήκευση στη MySQL ──────────────────────────
            structured = MicroserviceOutput(
                system_analyst=system_analyst,
                architect=architect,
                database=database,
                backend_layer=backend_layer,
                devops=devops,
                testing=testing,
                final_summary=final_response,
            )
            structured_dict = structured.model_dump()

            # Update form με result
            res = await db.execute(
                select(InputForm).where(InputForm.id == form_id)
            )
            saved_form = res.scalar_one_or_none()
            if saved_form:
                saved_form.result_json = json.dumps(structured_dict)
                await db.commit()

            # ── Done event ────────────────────────────────────
            yield sse({
                "type": "done",
                "form_id": form_id,
                "response": final_response,
                "structured_output": structured_dict,
                "pct": 100,
            })

        except Exception as e:
            yield sse({"type": "error", "message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # σημαντικό για nginx
            "Access-Control-Allow-Origin": "http://localhost:3000",
        },
    )