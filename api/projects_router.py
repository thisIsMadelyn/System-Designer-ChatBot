from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import json

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

@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
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

# api/projects_router.py
# ΠΡΟΣΘΕΣΕ αυτό μετά το υπάρχον @router.post("/{project_id}/forms")
# (όλος ο υπόλοιπος κώδικας παραμένει ακριβώς ίδιος)

from agents.orchestrator import run_orchestrator  # νέο import στην κορυφή


class RunPipelineRequest(BaseModel):
    """Body για το /run endpoint — ίδια fields με InputFormCreate"""
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
    response:         str         # markdown summary
    structured_output: Optional[dict]  # τα 6 agent outputs


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