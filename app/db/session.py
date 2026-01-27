from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "psql 'postgresql://neondb_owner:npg_ZOSU4ACW3xNT@ep-summer-dream-ah9akyph-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
