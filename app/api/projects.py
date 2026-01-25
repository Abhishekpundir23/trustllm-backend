from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.db.deps import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.model_run import ModelRun
from app.models.evaluation_result import EvaluationResult
from app.models.test_case import TestCase
from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.analytics import HealthResponse, FailingTest

router = APIRouter(prefix="/projects", tags=["Projects"],
    dependencies=[Depends(get_current_user)])

@router.post("/", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_project = Project(
        name=project.name,
        domain=project.domain,
        user_id=current_user.id
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.get("/", response_model=list[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    return projects

@router.post("/{project_id}/health", response_model=HealthResponse)
def get_project_health(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify Project
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Get Recent Runs (Completed only)
    runs = db.query(ModelRun).filter(
        ModelRun.project_id == project_id,
        ModelRun.status == "completed"
    ).order_by(desc(ModelRun.completed_at)).limit(2).all()

    # --- Metrics Logic ---

    # A. Models Compared (Unique count)
    unique_models = db.query(ModelRun.model_name).filter(
        ModelRun.project_id == project_id
    ).distinct().count()

    # B. Worst Failing Tests (Top 5 most frequent failures)
    worst_tests_query = db.query(
        TestCase.id,
        TestCase.prompt,
        func.count(EvaluationResult.id).label('fail_count')
    ).join(EvaluationResult, EvaluationResult.test_case_id == TestCase.id)\
     .join(ModelRun, EvaluationResult.model_run_id == ModelRun.id)\
     .filter(
         ModelRun.project_id == project_id,
         EvaluationResult.score == 0  # 0 = Incorrect
     )\
     .group_by(TestCase.id)\
     .order_by(desc('fail_count'))\
     .limit(5).all()

    worst_tests = [
        FailingTest(test_id=t.id, prompt=t.prompt, failure_count=t.fail_count)
        for t in worst_tests_query
    ]

    # C. Pass Rate & Drift
    pass_rate = 0.0
    drift = 0.0
    regression_score = 0.0

    if runs:
        latest_run = runs[0]
        
        # Calculate Stats for Latest Run
        total_latest = db.query(EvaluationResult).filter(EvaluationResult.model_run_id == latest_run.id).count()
        passed_latest = db.query(EvaluationResult).filter(
            EvaluationResult.model_run_id == latest_run.id, 
            EvaluationResult.score == 2
        ).count()
        
        if total_latest > 0:
            pass_rate = (passed_latest / total_latest) * 100

        # If we have a previous run, calculate Drift
        if len(runs) > 1:
            prev_run = runs[1]
            total_prev = db.query(EvaluationResult).filter(EvaluationResult.model_run_id == prev_run.id).count()
            passed_prev = db.query(EvaluationResult).filter(
                EvaluationResult.model_run_id == prev_run.id, 
                EvaluationResult.score == 2
            ).count()
            
            prev_rate = 0.0
            if total_prev > 0:
                prev_rate = (passed_prev / total_prev) * 100
            
            # Drift: Positive means improvement, Negative means regression
            drift = pass_rate - prev_rate
            
            # Regression Score: Inverted Drift (Positive means bad regression)
            if drift < 0:
                regression_score = abs(drift)

    return HealthResponse(
        pass_rate=round(pass_rate, 2),
        drift=round(drift, 2),
        models_compared=unique_models,
        regression_score=round(regression_score, 2),
        worst_failing_tests=worst_tests
    )

# 👇 NEW: Delete Project Endpoint
@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify Project Ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Cascade Delete (Manually deleting children to be safe)
    # Delete Evaluation Results linked to this project's runs
    db.query(EvaluationResult).filter(
        EvaluationResult.model_run_id.in_(
            db.query(ModelRun.id).filter(ModelRun.project_id == project_id)
        )
    ).delete(synchronize_session=False)

    # Delete Model Runs
    db.query(ModelRun).filter(ModelRun.project_id == project_id).delete(synchronize_session=False)

    # Delete Test Cases
    db.query(TestCase).filter(TestCase.project_id == project_id).delete(synchronize_session=False)

    # 3. Delete Project
    db.delete(project)
    db.commit()

    return {"status": "success", "message": f"Project {project_id} deleted"}