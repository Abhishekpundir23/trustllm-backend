from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str
    domain: str = "general"

class ProjectResponse(BaseModel):
    id: int  # <--- FIXED: Changed from str to int
    name: str
    domain: str

    class Config:
        from_attributes = True