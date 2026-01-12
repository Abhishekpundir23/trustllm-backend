from app.db.base import Base
from app.db.session import engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <--- NEW IMPORT
from app.api.auth import router as auth_router
from app.api.projects import router as project_router
from app.api.tests import router as test_router
from app.api.runs import router as run_router
# Handle Prompt router import gracefully if it fails
try:
    from app.api.prompts import router as prompt_router
except ImportError:
    prompt_router = None

app = FastAPI(title="TrustLLM Backend")

# --- CORS CONFIGURATION (NEW) ---
origins = [
    "http://localhost:3000",  # Allow your Frontend
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -------------------------------

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(project_router)
app.include_router(test_router)
app.include_router(run_router)

if prompt_router:
    app.include_router(prompt_router)

@app.get("/")
def root():
    return {"status": "TrustLLM backend running"}