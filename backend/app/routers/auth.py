from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text

from .. import models, schemas
from ..config import settings
from ..database import get_db
from ..security import create_access_token
from ..vulnerable_utils import weak_hash_password, generate_weak_token

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="backend/app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/reset-password")
async def password_reset_request(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    # VULNERABILITY: Host Header Injection
    # The application uses the Host header from the request to build the reset link.
    # An attacker can change the Host header to their own server to steal reset tokens.
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        # User enumeration - don't do this in secure apps, but here we do.
        return templates.TemplateResponse("login.html", {"request": request, "error": "User with this email does not exist."})

    # Generate a dummy token
    reset_token = generate_weak_token()
    
    # Building the link using Host header
    host = request.headers.get("Host")
    reset_link = f"http://{host}/auth/reset-password?token={reset_token}"
    
    # In a real app, this would be emailed. Here we just show it in the response 
    # as a "Log" or "Debug" message to simulate theft if Host is poisoned.
    return templates.TemplateResponse("login.html", {
        "request": request, 
        "success": f"Password reset link sent to {email}! (DEBUG: {reset_link})"
    })

@router.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

@router.post("/auth/register")
async def register_user(
    request: Request,
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    role: str = Form("patient"), # VULNERABILITY: Mass Assignment / Enum bypass
    db: Session = Depends(get_db)
):
    # VULNERABILITY: User Enumeration (Verbose error messages)
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": f"Email {email} is already registered! Try logging in."
        })

    # VULNERABILITY: Weak Password Hashing (MD5)
    hashed_password = weak_hash_password(password)

    # VULNERABILITY: Mass Assignment (trusting 'role' from form directly without validation)
    # Allows creating 'admin' user easily
    user = models.User(
        email=email,
        full_name=full_name,
        role=role,
        hashed_password=hashed_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return templates.TemplateResponse("login.html", {
            "request": request,
            "success": "Registration successful! Please login."
        })

@router.post("/auth/login")
async def login(
    request: Request,
    username: str = Form(...), # email
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # VULNERABILITY: SQL Injection
    # Using string formatting to build query
    hashed_password = weak_hash_password(password)
    
    # Intentionally insecure query construction
    query_str = f"SELECT * FROM users WHERE email = '{username}' AND hashed_password = '{hashed_password}'"
    
    try:
        # executing raw sql
        result = db.execute(text(query_str))
        user = result.fetchone()
        
        if not user:
             return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Invalid credentials"
            })
            
        # If SQLi succeeds (e.g. ' OR '1'='1), we might get the first user (usually admin)
        
        # Create token (Weak Secret logic should be in create_access_token if we modify it, 
        # or we just use the standard one for now but with a known secret in config)
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role}, # user is Row object or dict-like
            expires_delta=access_token_expires,
        )
        
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=False, # VULNERABILITY: JavaScript can read this (XSS -> Cookie Stealing)
            samesite="Lax"
        )
        return response

    except Exception as e:
        # VULNERABILITY: API Error Exposure
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"Database Error: {str(e)}"
        })


