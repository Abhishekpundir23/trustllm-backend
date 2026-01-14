from app.models.prompt import PromptVersion # <--- Add this import
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID

from app.db.deps import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.test_case import TestCase
from app.models.model_run import ModelRun
from app.models.evaluation_result import EvaluationResult
from app.schemas.run import RunRequest, RunSummary
from app.schemas.compare import ComparisonResponse, ComparisonRow
from app.services.evaluation_engine import evaluate

# Handle PromptVersion import gracefully
try:
    from app.models.prompt import PromptVersion
except ImportError:
    PromptVersion = None

router = APIRouter(prefix="/projects/{project_id}/run", tags=["Evaluation"],
    dependencies=[Depends(get_current_user)])

@router.post("/", response_model=RunSummary)
def run_evaluation(
    project_id: int,
    payload: RunRequest,
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

    # 2. Get Prompt Template (if provided)
    system_template = None
    # Check if prompt_version_id exists in payload and is not None
    if getattr(payload, 'prompt_version_id', None) and PromptVersion:
        prompt_version = db.query(PromptVersion).filter(
            PromptVersion.id == payload.prompt_version_id,
            PromptVersion.project_id == project_id
        ).first()
        if prompt_version:
            system_template = prompt_version.template

    # 3. Load test cases
    tests = db.query(TestCase).filter(
        TestCase.project_id == project_id
    ).all()

    if not tests:
        raise HTTPException(status_code=400, detail="No test cases found")

    # 4. Create model run record
    run = ModelRun(
        project_id=project_id,
        model_name=payload.model_name,
        prompt_version_id=getattr(payload, "prompt_version_id", None),
        status="running"
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # 5. Run Evaluation (Call the new engine!)
    try:
        # This calls OpenAI with the pirate template (if selected)
        results = evaluate(tests, payload.model_name, system_template)

        # 6. Save Results to Database
        for res in results:
            db_res = EvaluationResult(
                model_run_id=run.id,
                test_case_id=res["test_id"],
                model_output=res["output"],
                score=res["score"],
                category=res["category"]
            )
            db.add(db_res)
        
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        db.commit()

        # 7. Calculate Summary
        correct = sum(1 for r in results if r["score"] == 2)
        
        return RunSummary(
            run_id=str(run.id),
            model_name=payload.model_name,
            prompt_version_id=getattr(payload, "prompt_version_id", None),
            total_tests=len(tests),
            correct=correct,
            incorrect=len(tests) - correct
        )

    except Exception as e:
        run.status = "failed"
        db.commit()
        raise e
    
@router.get("/", response_model=list[RunSummary])
def list_runs(
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

    # 2. Get all runs for this project (newest first)
    runs = db.query(ModelRun).filter(
        ModelRun.project_id == project_id
    ).order_by(ModelRun.started_at.desc()).all()

    # 3. Calculate summary stats for each run
    summaries = []
    for run in runs:
        # Count results
        total = db.query(EvaluationResult).filter(EvaluationResult.model_run_id == run.id).count()
        correct = db.query(EvaluationResult).filter(
            EvaluationResult.model_run_id == run.id, 
            EvaluationResult.score == 2
        ).count()
        
        summaries.append(RunSummary(
            run_id=str(run.id),
            model_name=run.model_name,
            prompt_version_id=run.prompt_version_id,
            total_tests=total,
            correct=correct,
            incorrect=total - correct
        ))

    return summaries
# ... inside app/api/runs.py
@router.get("/{run_id}/details")
def get_run_details(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Convert the String ID to a real UUID object
    try:
        real_run_id = UUID(run_id) 
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # 2. Use the UUID object in the query
    results = db.query(EvaluationResult, TestCase).join(
        TestCase, EvaluationResult.test_case_id == TestCase.id
    ).filter(
        EvaluationResult.model_run_id == real_run_id 
    ).all()

    details = []
    for res, test in results:
        details.append({
            "test_id": test.id,
            "prompt": test.prompt,
            "expected": test.expected,
            "output": res.model_output,  # Ensure this matches your model field name (model_output vs output)
            "score": res.score
        })
    return details
@router.get("/compare", response_model=ComparisonResponse)
def compare_runs(
    project_id: int,
    run_id_1: str,
    run_id_2: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify project
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Convert Strings to UUID objects
    try:
        uuid_1 = UUID(run_id_1)
        uuid_2 = UUID(run_id_2)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # 3. Fetch runs
    run1 = db.query(ModelRun).filter(ModelRun.id == uuid_1, ModelRun.project_id == project_id).first()
    run2 = db.query(ModelRun).filter(ModelRun.id == uuid_2, ModelRun.project_id == project_id).first()

    if not run1 or not run2:
        raise HTTPException(status_code=404, detail="One or both runs not found")

    # 4. Fetch results
    results1 = db.query(EvaluationResult).filter(EvaluationResult.model_run_id == uuid_1).all()
    results2 = db.query(EvaluationResult).filter(EvaluationResult.model_run_id == uuid_2).all()

    r1_map = {r.test_case_id: r for r in results1}
    r2_map = {r.test_case_id: r for r in results2}

    tests = db.query(TestCase).filter(TestCase.project_id == project_id).all()

    comparison_rows = []
    for test in tests:
        res1 = r1_map.get(test.id)
        res2 = r2_map.get(test.id)

        row = ComparisonRow(
            test_id=test.id,
            prompt=test.prompt,
            expected=test.expected,
            run1_output=res1.model_output if res1 else None,
            run1_score=res1.score if res1 else None,
            run2_output=res2.model_output if res2 else None,
            run2_score=res2.score if res2 else None
        )
        comparison_rows.append(row)

    return ComparisonResponse(
        project_id=project_id,
        run1_id=str(run1.id),
        run1_name=run1.model_name,
        run2_id=str(run2.id),
        run2_name=run2.model_name,
        comparisons=comparison_rows
    )