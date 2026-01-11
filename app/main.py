from app.db.base import Base
from app.db.session import engine
from fastapi.security import OAuth2PasswordBearer
from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api.projects import router as project_router
from app.api.tests import router as test_router
from app.api.runs import router as run_router
# NEW IMPORT
from app.api.prompts import router as prompt_router

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
app = FastAPI(title="TrustLLM Backend")

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(project_router)
app.include_router(test_router)
app.include_router(run_router)
# NEW ROUTER
app.include_router(prompt_router)

@app.get("/")
def root():
    return {"status": "TrustLLM backend running"}