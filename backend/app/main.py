import shutil
import uuid
import os
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db, engine, Base, AsyncSessionLocal
from app.models import CollabRequest, Project, Embedding, User
from app.tasks import process_paper_task
from app.config import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from fastapi import WebSocket, WebSocketDisconnect

app = FastAPI(title="ResPlanet API (Gemini Edition)")

class ConnectionManager:
    def __init__(self):
        # Store connections as {project_id: [websocket1, websocket2]}
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)

    def disconnect(self, websocket: WebSocket, project_id: str):
        self.active_connections[project_id].remove(websocket)

    async def broadcast(self, message: str, project_id: str):
        if project_id in self.active_connections:
            for connection in self.active_connections[project_id]:
                await connection.send_text(message)

manager = ConnectionManager()

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


@app.post("/collab/request")
async def send_collab_request(project_id: str, sender_id: str, db: AsyncSession = Depends(get_db)):
    # Get project to find the owner
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(404, "Project not found")
        
    new_request = CollabRequest(
        sender_id=sender_id,
        receiver_id=project.user_id,
        project_id=project_id,
        status="PENDING"
    )
    db.add(new_request)
    await db.commit()
    return {"message": "Collaboration request sent!"}

@app.put("/collab/{request_id}/{status}")
async def update_collab_status(request_id: str, status: str, db: AsyncSession = Depends(get_db)):
    # Status should be "ACCEPTED" or "REJECTED"
    result = await db.execute(select(CollabRequest).filter(CollabRequest.id == request_id))
    req = result.scalars().first()
    if not req:
        raise HTTPException(404, "Request not found")
    
    req.status = status
    await db.commit()
    return {"status": status}

@app.websocket("/ws/chat/{project_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    await manager.connect(websocket, project_id)
    try:
        while True:
            data = await websocket.receive_text()
            
            # 1. Broadcast Human Message
            await manager.broadcast(f"User {user_id}: {data}", project_id)
            
            # 2. Check for Bot Trigger "@bot"
            if "@bot" in data.lower():
                # Extract query (remove "@bot")
                query = data.lower().replace("@bot", "").strip()
                await manager.broadcast(f"🤖 AI: Thinking about '{query}'...", project_id)
                
                # --- RUN RAG LOGIC HERE ---
                # (Re-using the logic from your existing /chat endpoint)
                from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
                
                embeddings_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=settings.GOOGLE_API_KEY)
                query_vector = embeddings_model.embed_query(query)
                
                # Search DB
                stmt = select(Embedding).filter(Embedding.project_id == project_id)\
                    .order_by(Embedding.vector.cosine_distance(query_vector)).limit(3)
                result = await db.execute(stmt)
                chunks = result.scalars().all()
                context = "\n".join([c.content for c in chunks])
                
                # Generate Answer
                llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=settings.GOOGLE_API_KEY)
                answer = llm.invoke(f"Context: {context}\n\nQuestion: {query}").content
                
                # 3. Broadcast AI Response
                await manager.broadcast(f"🤖 AI: {answer}", project_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)