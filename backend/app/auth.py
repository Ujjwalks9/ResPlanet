from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi_sso.sso.google import GoogleSSO
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User
import os

router = APIRouter()

# Get these from Google Cloud Console
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# For local dev: http://localhost:8000/auth/callback/google
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback/google")

google_sso = GoogleSSO(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    allow_insecure_http=True
)

@router.get("/auth/login/google")
async def google_login():
    """Redirects user to Google Login"""
    return await google_sso.get_login_redirect()

@router.get("/auth/callback/google")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """Handles the return from Google"""
    try:
        user_info = await google_sso.verify_and_process(request)
        
        # Check if user exists in DB
        result = await db.execute(select(User).filter(User.email == user_info.email))
        user = result.scalars().first()

        if not user:
            # Create new user
            user = User(
                id=user_info.id, # Google Sub ID
                email=user_info.email,
                name=user_info.display_name,
                picture=user_info.picture
            )
            db.add(user)
            await db.commit()
        
        # Redirect to Frontend with User info (or JWT in real prod)
        # Assuming frontend is on localhost:3000
        return RedirectResponse(url=f"http://localhost:3000?user_id={user.id}&name={user.name}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))