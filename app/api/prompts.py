from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.deps import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.prompt import PromptVersion
from app.schemas.prompt import PromptCreate, PromptResponse

router = APIRouter(prefix="/projects/{project_id}/prompts", tags=["Prompts"],
    dependencies=[Depends(get_current_user)])

@router.post("/", response_model=PromptResponse)
def create_prompt_version(
    project_id: int,
    payload: PromptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Calculate next version number
    last_prompt = db.query(PromptVersion).filter(
        PromptVersion.project_id == project_id
    ).order_by(desc(PromptVersion.version)).first()

    new_version = 1
    if last_prompt:
        new_version = last_prompt.version + 1

    # 3. Create new prompt version
    prompt = PromptVersion(
        project_id=project_id,
        version=new_version,
        template=payload.template
    )

    db.add(prompt)
    db.commit()
    db.refresh(prompt)

    return prompt

@router.get("/", response_model=list[PromptResponse])
def list_prompts(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify project
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    prompts = db.query(PromptVersion).filter(
        PromptVersion.project_id == project_id
    ).order_by(desc(PromptVersion.version)).all()

    return prompts