import os
import shutil
import requests
from fastapi import APIRouter, Depends, Form, Request, HTTPException, status, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..security import get_current_user_from_token

router = APIRouter(tags=["profile"])
templates = Jinja2Templates(directory="backend/app/templates")

AVATAR_DIR = "backend/app/static/avatars"
os.makedirs(AVATAR_DIR, exist_ok=True)

@router.get("/profile", response_class=HTMLResponse)
async def my_profile(
    request: Request,
    current_user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    # Just redirect to ID-based profile to encourage IDOR
    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "user": current_user, 
        "full_access": True
    })

@router.get("/profile/{user_id}", response_class=HTMLResponse)
async def view_profile(
    request: Request,
    user_id: int,
    current_user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    # VULNERABILITY: IDOR (Insecure Direct Object Reference)
    # No check if current_user.id == user_id or if current_user is admin
    target_user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "user": target_user,
        "viewer": current_user,
        "full_access": (current_user.id == target_user.id)
    })

@router.post("/profile/update")
async def update_profile(
    request: Request,
    bio: str = Form(...),
    current_user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    # VULNERABILITY: Stored XSS
    current_user.bio = bio
    db.commit()
    return RedirectResponse(url=f"/profile/{current_user.id}?success=Bio updated", status_code=303)

@router.post("/profile/avatar/upload")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    # VULNERABILITY: Unrestricted File Upload
    file_path = os.path.join(AVATAR_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    current_user.avatar_url = f"/static/avatars/{file.filename}"
    db.commit()
    return RedirectResponse(url=f"/profile/{current_user.id}?success=Avatar uploaded", status_code=303)

@router.post("/profile/avatar/fetch")
async def fetch_remote_avatar(
    request: Request,
    url: str = Form(...),
    current_user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    # VULNERABILITY: SSRF
    try:
        response = requests.get(url, verify=False, timeout=5) 
        filename = f"remote_{current_user.id}.jpg"
        file_path = os.path.join(AVATAR_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(response.content)
        current_user.avatar_url = f"/static/avatars/{filename}"
        db.commit()
        return RedirectResponse(url=f"/profile/{current_user.id}?success=Avatar fetched", status_code=303)
    except Exception as e:
         return RedirectResponse(url=f"/profile/{current_user.id}?error=SSRF Error: {str(e)}", status_code=303)
