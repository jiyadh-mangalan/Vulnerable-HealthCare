from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..vulnerable_utils import render_template_string_unsafe
from .. import models

router = APIRouter(tags=["misc"])
templates = Jinja2Templates(directory="backend/app/templates")

@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = Query("")):
    # VULNERABILITY: Reflected XSS
    # The query 'q' is reflected in the template.
    # In search.html, we will render it with | safe.
    
    return templates.TemplateResponse("search.html", {
        "request": request,
        "query": q,
        "results": [] # Mock results
    })

@router.get("/redirect")
async def open_redirect(url: str = Query("/dashboard")):
    # VULNERABILITY: Open Redirect
    # Redirects to any user-supplied URL without validation.
    return RedirectResponse(url=url)

@router.post("/feedback/preview")
async def feedback_preview(request: Request, template_str: str = Form(...)):
    # VULNERABILITY: SSTI (Server Side Template Injection)
    # Uses unsafe template rendering from vulnerable_utils
    
    context = {"user": "HealthApp User", "app_name": "Vulnerable HealthCare"}
    rendered = render_template_string_unsafe(template_str, context)
    
    return templates.TemplateResponse("feedback.html", {
        "request": request,
        "preview": rendered,
        "original": template_str
    })

@router.get("/feedback", response_class=HTMLResponse)
async def feedback_page(request: Request):
    return templates.TemplateResponse("feedback.html", {"request": request})

@router.get("/api/v1/users/{user_id}")
async def get_user_api(user_id: int, db: Session = Depends(get_db)):
    # VULNERABILITY: Excessive Data Exposure / Sensitive Data Exposure
    # Returns the entire user object including hashed_password
    user = db.get(models.User, user_id)
    if not user:
        return {"error": "Not Found"}
    return user
