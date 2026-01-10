from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.test_case import TestCase
from app.schemas.test_case import TestCaseCreate, TestCaseResponse

router = APIRouter(prefix="/projects/{project_id}/tests", tags=["Test Cases"],
    dependencies=[Depends(get_current_user)])
@router.post("/", response_model=TestCaseResponse)
def create_test_case(
    project_id: str,
    test: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify project exists and belongs to user
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Create test case
    new_test = TestCase(
        project_id=project_id,
        prompt=test.prompt,
        task_type=test.task_type,
        rules=test.rules,
        expected=test.expected
    )

    db.add(new_test)
    db.commit()
    db.refresh(new_test)

    return new_test
@router.get("/", response_model=list[TestCaseResponse])
def list_test_cases(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tests = db.query(TestCase).filter(
        TestCase.project_id == project_id
    ).all()

    return tests
@router.delete("/{test_id}", status_code=204)
def delete_test_case(
    project_id: str,
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    test = db.query(TestCase).join(Project).filter(
        TestCase.id == test_id,
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not test:
        raise HTTPException(status_code=404, detail="Test case not found")

    db.delete(test)
    db.commit()
