from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.test_case import TestCase
from app.models.model_run import ModelRun
from app.models.evaluation_result import EvaluationResult
from app.schemas.run import RunRequest, RunSummary
from app.services.evaluation_engine import mock_llm, score_response

router = APIRouter(prefix="/projects/{project_id}/run", tags=["Evaluation"],
    dependencies=[Depends(get_current_user)])
@router.post("/", response_model=RunSummary)
def run_evaluation(
    project_id: str,
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

    # 2. Load test cases
    tests = db.query(TestCase).filter(
        TestCase.project_id == project_id
    ).all()

    if not tests:
        raise HTTPException(status_code=400, detail="No test cases found")

    # 3. Create model run
    run = ModelRun(
        project_id=project_id,
        model_name=payload.model_name
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    correct = 0
    incorrect = 0

    # 4. Evaluate each test
    for test in tests:
        output = mock_llm(test.prompt, payload.model_name)
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

    db.commit()

    # 5. Return summary
    return RunSummary(
        run_id=run.id,
        model_name=payload.model_name,
        total_tests=len(tests),
        correct=correct,
        incorrect=incorrect
    )
