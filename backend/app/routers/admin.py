import os
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user_from_token
from ..vulnerable_utils import unsafe_ping

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="backend/app/templates")

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    # VULNERABILITY: Broken Access Control
    # Ideally should check if current_user.role == 'admin'.
    # We might just check if they are logged in, or check nothing!
    # Let's check logged in but NOT role.
    
    # Also we leak user data here for the dashboard
    users = db.query(models.User).limit(5).all()
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user": current_user, 
        "users": users
    })

@router.post("/diagnostics/ping")
async def diagnostics_ping(
    request: Request,
    ip: str = Form(...),
    current_user: models.User = Depends(get_current_user_from_token)
):
    # VULNERABILITY: Command Injection
    output = unsafe_ping(ip)
    
    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "user": current_user, 
        "ping_output": output,
        "users": [] # Don't need to reload users for ping result ideally
    })

@router.post("/users/search")
async def user_search(
    request: Request,
    query: str = Form(...),
    current_user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    # VULNERABILITY: SQL Injection
    # Searching users
    
    sql = f"SELECT * FROM users WHERE email LIKE '%{query}%' OR full_name LIKE '%{query}%'"
    try:
        result = db.execute(text(sql))
        # Determine columns from model or result keys (if mapped)
        # SQLAlchemy 'text' result returns tuples or Row objects.
        users = result.fetchall()
        
    except Exception as e:
        return templates.TemplateResponse("admin.html", {
            "request": request, 
            "user": current_user, 
            "ping_output": f"SQL Error: {str(e)}"
        })
        
    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "user": current_user, 
        "users": users
    })

@router.get("/logs", response_class=HTMLResponse)
async def view_logs(
    request: Request,
    file: str = "app.log",
    current_user: models.User = Depends(get_current_user_from_token)
):
    # VULNERABILITY: Path Traversal / LFI
    # Arbitrary file read
    
    LOG_DIR = "/var/log" # or just curr dir
    # For demo, we might want to read /etc/passwd or something else relative
    
    # We will try to read from current dir if no path given, or absolute
    # If they pass /etc/passwd it works if permissions allow
    
    log_content = ""
    try:
        # If absolute, verify exist
        if os.path.exists(file):
            with open(file, "r") as f:
                log_content = f.read()
        else:
             log_content = "File not found."
    except Exception as e:
        log_content = f"Error reading file: {str(e)}"

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user": current_user, 
        "log_content": log_content,
        "users": [] 
    })