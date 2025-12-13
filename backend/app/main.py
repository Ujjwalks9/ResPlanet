import shutil
import uuid
import os
from typing import List

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from sqlalchemy.orm import selectinload


from app.models import ProjectFile

from app.database import init_db, get_db
from app.models import Project, User, CollabRequest, ChatMessage, Embedding
from app.schemas import ProjectOut, CollabRequestOut
from app.auth import router as auth_router
from app.tasks import process_paper_task  # <--- OLD FEATURE: Import Celery Task
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from app.config import settings

app = FastAPI(title="ResPlanet API (Gemini Edition)")

# Mount Static for PDF viewing (OLD FEATURE)
app.mount("/static", StaticFiles(directory="."), name="static")

app.include_router(auth_router)

@app.on_event("startup")
async def startup_event():
    await init_db()

# class ConnectionManager:
#     def __init__(self):
#         # Store connections as {project_id: [websocket1, websocket2]}
#         self.active_connections: dict[str, list[WebSocket]] = {}

#     async def connect(self, websocket: WebSocket, project_id: str):
#         await websocket.accept()
#         if project_id not in self.active_connections:
#             self.active_connections[project_id] = []
#         self.active_connections[project_id].append(websocket)

#     def disconnect(self, websocket: WebSocket, project_id: str):
#         self.active_connections[project_id].remove(websocket)

#     async def broadcast(self, message: str, project_id: str):
#         if project_id in self.active_connections:
#             for connection in self.active_connections[project_id]:
#                 await connection.send_text(message)

# manager = ConnectionManager()

# @app.on_event("startup")
# async def startup():
#     # 1. Create Tables
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
    
#     # 2. Create a Dummy User (user_123) if they don't exist
#     async with AsyncSessionLocal() as db:
#         result = await db.execute(select(User).filter(User.id == "user_123"))
#         user = result.scalars().first()
        
#         if not user:
#             new_user = User(id="user_123", email="test@resplanet.com", name="Test Researcher")
#             db.add(new_user)
#             await db.commit()
#             print("Created test user: user_123")

@app.post("/upload")
async def upload_paper(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # 1. Create project
    project = Project(
        title=file.filename,
        user_id="user_123"  # replace later with auth
    )
    db.add(project)
    await db.flush()

    # 2. Store PDF bytes in DB
    pdf_bytes = await file.read()

    project_file = ProjectFile(
        project_id=project.id,
        filename=file.filename,
        content_type=file.content_type,
        data=pdf_bytes
    )
    db.add(project_file)
    await db.commit()

    # 3. Trigger Celery (ONLY project_id)
    process_paper_task.delay(str(project.id))

    return {"id": project.id, "status": "processing_started"}

@app.get("/projects/{project_id}/file")
async def get_project_file(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProjectFile).where(ProjectFile.project_id == project_id)
    )
    project_file = result.scalars().first()

    if not project_file:
        raise HTTPException(status_code=404, detail="Project file not found")

    return StreamingResponse(
        BytesIO(project_file.data),
        media_type=project_file.content_type or "application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{project_file.filename}"'
        },
    )


@app.post("/chat")
async def chat(query: str, project_id: str, db: AsyncSession = Depends(get_db)):
    """
    OLD FEATURE: Standard HTTP RAG Chat
    """
    # 1. Embed Query
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004", 
        google_api_key=settings.GOOGLE_API_KEY
    )
    query_vector = embeddings_model.embed_query(query)
    
    # 2. Semantic Search
    stmt = select(Embedding).filter(Embedding.project_id == project_id)\
        .order_by(Embedding.vector.cosine_distance(query_vector))\
        .limit(10)
    
    result = await db.execute(stmt)
    relevant_chunks = result.scalars().all()
    
    if not relevant_chunks:
        return {"answer": "I couldn't find relevant info."}
    
    context = "\n\n".join([c.content for c in relevant_chunks[:5]])
    
    # 3. Generate Answer
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=settings.GOOGLE_API_KEY
    )
    
    prompt = f"""
    You are an expert research assistant.

    Answer the question ONLY using the context below.
    If the answer is not present in the context, say:
    "I could not find this information in the paper."

    Context:
    {context}

    Question:
    {query}
    """

    response = llm.invoke(prompt)
    
    return {
        "answer": response.content,
        "sources": [c.content[:100] + "..." for c in relevant_chunks]
    }

########### Feed Features ###########################

@app.get("/feed", response_model=List[ProjectOut])
async def get_feed(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.user)) 
        .order_by(Project.created_at.desc())
        .limit(20)
    )
    return result.scalars().all()


@app.get("/feed/trending", response_model=List[ProjectOut])
async def get_trending_feed(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.user))  
        .order_by(Project.views_count.desc())
        .limit(10)
    )
    return result.scalars().all()


@app.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.user))  
        .where(Project.id == project_id)
    )
    project = result.scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Increment view count
    project.views_count += 1
    await db.commit()

    return project


@app.post("/projects/{project_id}/review")
async def ai_peer_review(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    # 1. Fetch project
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.user))
        .where(Project.id == project_id)
    )
    project = result.scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Fetch top relevant chunks for review
    result = await db.execute(
        select(Embedding)
        .where(Embedding.project_id == project_id)
        .limit(15)
    )
    chunks = result.scalars().all()

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="Paper is not processed yet. Please try again later."
        )

    context = "\n\n".join(c.content for c in chunks[:10])

    # 3. Ask AI to critique the paper
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GOOGLE_API_KEY
    )

    prompt = f"""
You are an expert academic peer reviewer.

Critically review the following research paper content.
Your review MUST include:

1. Summary of the paper
2. Strengths
3. Weaknesses / Limitations
4. Methodology critique
5. Novelty & originality
6. Suggestions for improvement
7. Final verdict (Accept / Weak Accept / Weak Reject / Reject)

Base your review ONLY on the content below.
If information is missing, explicitly mention it.

Paper Content:
{context}
"""

    review = llm.invoke(prompt).content

    return {
        "project_id": project_id,
        "title": project.title,
        "author": project.user.name if project.user else None,
        "ai_review": review
    }


##################### Collaboration Features #####################################

@app.post("/collab/request")
async def send_collab_request(
    project_id: str, 
    sender_id: str, 
    db: AsyncSession = Depends(get_db)
):
    # Verify Project Exists
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(404, "Project not found")

    new_request = CollabRequest(
        sender_id=sender_id,
        receiver_id=project.user_id, # Owner
        project_id=project_id,
        status="PENDING"
    )
    db.add(new_request)
    await db.commit()
    return {"message": "Request Sent"}

@app.get("/collab/requests/{user_id}", response_model=List[CollabRequestOut])
async def get_my_requests(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CollabRequest)
        .options(
            selectinload(CollabRequest.sender),  
            selectinload(CollabRequest.project),  
            selectinload(CollabRequest.project).selectinload(Project.user),
        )
        .where(CollabRequest.receiver_id == user_id)
    )
    return result.scalars().all()


@app.put("/collab/{request_id}/{status}")
async def update_collab_status(
    request_id: UUID,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Owner accepts or rejects the collaboration request.
    Status must be: ACCEPTED or REJECTED
    """
    # Fetch the request
    result = await db.execute(select(CollabRequest).where(CollabRequest.id == request_id))
    req = result.scalars().first()
    
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if status.upper() not in ["ACCEPTED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Invalid status. Use ACCEPTED or REJECTED")
    
    # Update status
    req.status = status.upper()
    await db.commit()
    
    return {"status": req.status}

########### Chat (Human + AI) ######################################

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)

    def disconnect(self, websocket: WebSocket, project_id: str):
        if project_id in self.active_connections:
            self.active_connections[project_id].remove(websocket)

    async def broadcast(self, message: str, project_id: str):
        if project_id in self.active_connections:
            for connection in self.active_connections[project_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/chat/{project_id}/{sender_id}")
async def websocket_chat(
    websocket: WebSocket, 
    project_id: str, 
    sender_id: str, 
    db: AsyncSession = Depends(get_db)
):
    await manager.connect(websocket, project_id)
    try:
        while True:
            data = await websocket.receive_text()
            
            # 1. Save Human Message to DB
            human_msg = ChatMessage(project_id=project_id, sender_id=sender_id, content=data, is_ai=False)
            db.add(human_msg)
            await db.commit()
            
            # 2. Broadcast to room
            await manager.broadcast(f"User {sender_id}: {data}", project_id)

            # 3. Check for Bot Trigger "@bot"
            if "@bot" in data.lower():
                query = data.lower().replace("@bot", "").strip()
                await manager.broadcast(f"🤖 AI: Thinking about '{query}'...", project_id)
                
                # --- RAG LOGIC INSIDE WEBSOCKET ---
                embeddings_model = GoogleGenerativeAIEmbeddings(
                    model="models/text-embedding-004", 
                    google_api_key=settings.GOOGLE_API_KEY
                )
                query_vector = embeddings_model.embed_query(query)
                
                stmt = select(Embedding).filter(Embedding.project_id == project_id)\
                    .order_by(Embedding.vector.cosine_distance(query_vector)).limit(3)
                
                # Need a new session for async operation inside loop if 'db' is closed (rare in WS but safe to check)
                # Using the injected 'db' session is usually fine for the lifecycle of the connection
                result = await db.execute(stmt)
                chunks = result.scalars().all()
                context = "\n".join([c.content for c in chunks])
                
                if not context:
                    ai_response = "I couldn't find information on that in the paper."
                else:
                    llm = ChatGoogleGenerativeAI(
                        model="gemini-2.5-flash", 
                        google_api_key=settings.GOOGLE_API_KEY
                    )
                    ai_response = llm.invoke(f"Context: {context}\n\nQuestion: {query}").content
                
                # Save AI Message
                ai_msg = ChatMessage(project_id=project_id, sender_id=sender_id, content=ai_response, is_ai=True)
                db.add(ai_msg)
                await db.commit()
                
                await manager.broadcast(f"🤖 AI: {ai_response}", project_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)