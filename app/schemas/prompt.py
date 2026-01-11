from pydantic import BaseModel
from datetime import datetime

class PromptCreate(BaseModel):
    template: str

class PromptResponse(BaseModel):
    id: str
    project_id: int
    version: int
    template: str
    created_at: datetime

    class Config:
        from_attributes = True