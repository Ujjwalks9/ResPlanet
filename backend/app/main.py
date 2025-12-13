import shutil
import uuid
import os
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db, engine, Base, AsyncSessionLocal
from app.models import Project, Embedding, User
from app.tasks import process_paper_task
from app.config import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

app = FastAPI(title="ResPlanet API (Gemini Edition)")

@app.on_event("startup")
async def startup():
    # 1. Create Tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Create a Dummy User (user_123) if they don't exist
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).filter(User.id == "user_123"))
        user = result.scalars().first()
        
        if not user:
            new_user = User(id="user_123", email="test@resplanet.com", name="Test Researcher")
            db.add(new_user)
            await db.commit()
            print("Created test user: user_123")

@app.post("/upload")
async def upload_paper(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    file_id = str(uuid.uuid4())
    file_path = f"temp_{file_id}.pdf"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    new_project = Project(
        title=file.filename,
        file_url=file_path,
        user_id="user_123" 
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    
    process_paper_task.delay(str(new_project.id), file_path)
    
    return {"id": new_project.id, "status": "processing_started"}

@app.post("/chat")
async def chat(query: str, project_id: str, db: AsyncSession = Depends(get_db)):
    # 1. Embed Query
    embeddings_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=settings.GOOGLE_API_KEY)
    query_vector = embeddings_model.embed_query(query)
    
    # 2. Semantic Search
    stmt = select(Embedding).filter(Embedding.project_id == project_id)\
        .order_by(Embedding.vector.cosine_distance(query_vector))\
        .limit(5)
    
    result = await db.execute(stmt)
    relevant_chunks = result.scalars().all()
    
    if not relevant_chunks:
        return {"answer": "I couldn't find relevant info in this paper."}
    
    context = "\n\n".join([c.content for c in relevant_chunks])
    
    # 3. Generate Answer with Gemini
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=settings.GOOGLE_API_KEY)
    
    prompt = f"""You are a helpful research assistant. Answer the question based ONLY on the context provided below.
    
    Context:
    {context}
    
    Question: {query}
    """
    
    response = llm.invoke(prompt)
    
    return {
        "answer": response.content,
        "sources": [c.content[:100] + "..." for c in relevant_chunks]
    }


@app.get("/feed")
async def get_feed(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    return projects

@app.get("/projects/{project_id}")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project