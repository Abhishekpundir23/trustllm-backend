from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from datetime import datetime
import csv
from fastapi.responses import StreamingResponse
import io

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

router = APIRouter(prefix="/projects/{project_id}/run", tags=["Evaluation"], dependencies=[Depends(get_current_user)])

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
        status="running",
        total_input_tokens=0,
        total_output_tokens=0,
        estimated_cost=0.0
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # 5. Run Evaluation
    try:
        # 👇 NEW: Extract User Keys
        user_keys = {
            "openai": current_user.openai_key,
            "anthropic": current_user.anthropic_key,
            "gemini": current_user.gemini_key
        }

        # 👇 UPDATED: Pass keys to evaluate function
        results, input_tokens, output_tokens = evaluate(
            test_cases=tests, 
            model_name=payload.model_name, 
            api_keys=user_keys, 
            system_template=system_template
        )

        # Cost Calculation
        cost = (input_tokens / 1_000_000 * 0.075) + (output_tokens / 1_000_000 * 0.30)

        run.total_input_tokens = input_tokens
        run.total_output_tokens = output_tokens
        run.estimated_cost = cost
        
        # 6. Save Results
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

        correct = sum(1 for r in results if r["score"] == 2)
        
        return RunSummary(
            run_id=str(run.id),
            model_name=payload.model_name,
            prompt_version_id=getattr(payload, "prompt_version_id", None),
            total_tests=len(tests),
            correct=correct,
            incorrect=len(tests) - correct,
            total_input_tokens=run.total_input_tokens,
            total_output_tokens=run.total_output_tokens,
            estimated_cost=run.estimated_cost
        )

    except Exception as e:
        print(f"Run Failed: {e}")
        run.status = "failed"
        db.commit()
        raise e
    
@router.get("/", response_model=list[RunSummary])
def list_runs(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    runs = db.query(ModelRun).filter(
        ModelRun.project_id == project_id
    ).order_by(ModelRun.started_at.desc()).all()

    summaries = []
    for run in runs:
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
            incorrect=total - correct,
            total_input_tokens=run.total_input_tokens,
            total_output_tokens=run.total_output_tokens,
            estimated_cost=run.estimated_cost
        ))

    return summaries

@router.get("/{run_id}/details")
def get_run_details(
    run_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = db.query(EvaluationResult, TestCase).join(
        TestCase, EvaluationResult.test_case_id == TestCase.id
    ).filter(
        EvaluationResult.model_run_id == run_id 
    ).all()

    details = []
    for res, test in results:
        details.append({
            "test_id": test.id,
            "prompt": test.prompt,
            "expected": test.expected,
            "output": res.model_output,
            "score": res.score,
            "category": res.category
        })
    return details

@router.get("/compare", response_model=ComparisonResponse)
def compare_runs(
    project_id: int,
    run_id_1: int,
    run_id_2: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    run1 = db.query(ModelRun).filter(ModelRun.id == run_id_1, ModelRun.project_id == project_id).first()
    run2 = db.query(ModelRun).filter(ModelRun.id == run_id_2, ModelRun.project_id == project_id).first()

    if not run1 or not run2:
        raise HTTPException(status_code=404, detail="One or both runs not found")

    results1 = db.query(EvaluationResult).filter(EvaluationResult.model_run_id == run_id_1).all()
    results2 = db.query(EvaluationResult).filter(EvaluationResult.model_run_id == run_id_2).all()

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

@router.put("/{run_id}/results/{test_id}")
def update_result_score(
    project_id: int,
    run_id: int,
    test_id: int,
    score: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = db.query(EvaluationResult).filter(
        EvaluationResult.model_run_id == run_id,
        EvaluationResult.test_case_id == test_id
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    result.score = score
    result.category = "manual_override" 
    
    db.commit()
    
    return {"status": "success", "new_score": score}

@router.get("/{run_id}/export/csv")
def export_run_csv(
    project_id: int,
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    run = db.query(ModelRun).filter(ModelRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    results = db.query(EvaluationResult, TestCase).join(
        TestCase, EvaluationResult.test_case_id == TestCase.id
    ).filter(
        EvaluationResult.model_run_id == run_id
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Test ID", "Task Type", "Prompt", "Context (RAG)", "Expected", "Model Output", "Score", "Pass/Fail", "Category"])
    
    for res, test in results:
        status = "PASS" if res.score == 2 else "FAIL"
        writer.writerow([
            test.id,
            test.task_type,
            test.prompt,
            test.context or "N/A",
            test.expected,
            res.model_output,
            res.score,
            status,
            res.category
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=run_{run_id}_report.csv"}
    )