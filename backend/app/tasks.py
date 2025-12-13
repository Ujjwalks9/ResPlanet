from celery import Celery
from app.config import settings
from app.rag import process_pdf_for_rag
from app.database import AsyncSessionLocal 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Project, Embedding
from pgvector.sqlalchemy import Vector

# Setup Celery
celery_app = Celery("worker", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

# Sync DB connection for Celery (Simpler for background tasks)
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

@celery_app.task
def process_paper_task(project_id: str, file_path: str):
    session = SessionLocal()
    try:
        # 1. Run AI Processing
        print(f"Processing PDF for project: {project_id}")
        summary, topics, vectors = process_pdf_for_rag(file_path)
        
        # 2. Update Project Metadata
        project = session.query(Project).filter(Project.id == project_id).first()
        if project:
            project.abstract = summary
            project.topics = topics
            project.is_processed = True
        
        # 3. Save Embeddings
        for v in vectors:
            emb = Embedding(project_id=project_id, content=v["content"], vector=v["vector"])
            session.add(emb)
            
        session.commit()
        print(f"Finished processing {project_id}")
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        session.rollback()
    finally:
        session.close()
