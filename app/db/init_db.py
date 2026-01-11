from app.db.session import engine
from app.db.base import Base

from app.models.user import User
from app.models.project import Project
from app.models.test_case import TestCase
# NEW IMPORT
from app.models.prompt import PromptVersion

def init_db():
    Base.metadata.create_all(bind=engine)