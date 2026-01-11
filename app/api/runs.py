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
from app.services.evaluation_engine import mock_llm, score_response

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

    # 2. Get Prompt Template (if provided and model exists)
    prompt_template = "{{prompt}}"
    # Safe check: ensure payload has the field and PromptVersion model is loaded
    if hasattr(payload, 'prompt_version_id') and payload.prompt_version_id and PromptVersion:
        prompt_version = db.query(PromptVersion).filter(
            PromptVersion.id == payload.prompt_version_id,
            PromptVersion.project_id == project_id
        ).first()
        if not prompt_version:
            raise HTTPException(status_code=404, detail="Prompt version not found")
        prompt_template = prompt_version.template

    # 3. Load test cases
    tests = db.query(TestCase).filter(
        TestCase.project_id == project_id
    ).all()

    if not tests:
        raise HTTPException(status_code=400, detail="No test cases found")

    # 4. Create model run
    run = ModelRun(
        project_id=project_id,
        model_name=payload.model_name,
        # UNCOMMENTED: Save the prompt version ID to the database
        prompt_version_id=getattr(payload, "prompt_version_id", None),
        status="running"
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    correct = 0
    incorrect = 0

    # 5. Evaluate each test
    try:
        for test in tests:
            # Inject test prompt into the template
            final_prompt = prompt_template.replace("{{prompt}}", test.prompt)
            
            output = mock_llm(final_prompt, payload.model_name)
            score, category = score_response(output, test)

            if score == 2:
                correct += 1
            else:
                incorrect += 1

            result = EvaluationResult(
                model_run_id=run.id,
                test_case_id=test.id,
                model_output=output,
                score=score,
                category=category
            )
            db.add(result)
        
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        run.status = "failed"
        db.commit()
        raise e

    # 6. Return summary
    return RunSummary(
        run_id=str(run.id),
        model_name=payload.model_name,
        # UNCOMMENTED: Return the prompt version ID in the response
        prompt_version_id=getattr(payload, "prompt_version_id", None),
        total_tests=len(tests),
        correct=correct,
        incorrect=incorrect
    )

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