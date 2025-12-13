from celery import Celery
from app.config import settings
from app.rag import process_pdf_for_rag
from app.database import AsyncSessionLocal 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Project, Embedding
from pgvector.sqlalchemy import Vector
from app.models import ProjectFile


# Setup Celery
celery_app = Celery("worker", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

# Sync DB connection for Celery (Simpler for background tasks)
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

@celery_app.task
@celery_app.task
def process_paper_task(project_id: str):
    session = SessionLocal()
    try:
        project_file = (
            session.query(ProjectFile)
            .filter(ProjectFile.project_id == project_id)
            .first()
        )

        if not project_file:
            raise Exception("Project file not found")

        pdf_bytes = project_file.data

        summary, topics, vectors = process_pdf_for_rag(pdf_bytes)

        project = session.query(Project).get(project_id)
        project.abstract = summary
        project.topics = topics
        project.is_processed = True

        for v in vectors:
            session.add(
                Embedding(
                    project_id=project_id,
                    content=v["content"],
                    vector=v["vector"]
                )
            )

        session.commit()

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
