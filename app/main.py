from app.db.base import Base
from app.db.session import engine
from fastapi.security import OAuth2PasswordBearer
from fastapi import FastAPI, Depends
from app.api.auth import router as auth_router
from app.api.projects import router as project_router
from app.api.tests import router as test_router
from app.api.runs import router as run_router
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
app = FastAPI(title="TrustLLM Backend")
Base.metadata.create_all(bind=engine)
app.include_router(auth_router)
app.include_router(project_router)
app.include_router(test_router)
app.include_router(run_router)



@app.get("/")
def root():
    return {"status": "TrustLLM backend running"}
