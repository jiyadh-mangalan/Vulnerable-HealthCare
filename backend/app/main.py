from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .database import Base, engine
from .routers import auth, appointments, payments, profile, records, admin, misc
from .seed import seed_demo_users


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)
    seed_demo_users()

    app = FastAPI(
        title=settings.app_name,
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url="/redoc" if settings.enable_docs else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Adjust for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(appointments.router)
    app.include_router(payments.router)
    app.include_router(profile.router)
    app.include_router(records.router)
    app.include_router(admin.router)
    app.include_router(misc.router)

    app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")
    templates = Jinja2Templates(directory="backend/app/templates")

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "app_name": settings.app_name,
                "user": None # We'll need a way to get user from token in home too ideally
            },
        )

    # Helper dependency to get current user from cookie
    from .security import get_current_user_from_token
    from . import models, schemas
    from sqlalchemy.orm import Session
    from .database import get_db
    from fastapi import Depends

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(
        request: Request, 
        current_user: models.User = Depends(get_current_user_from_token),
        db: Session = Depends(get_db)
    ):
        # Fetch some data for the dashboard
        # This is where we might add more Broken Access Control later (e.g. seeing other's data)
        upcoming_appointments = []
        if current_user.role == "patient" and current_user.patient_profile:
             upcoming_appointments = current_user.patient_profile.appointments
        elif current_user.role == "doctor" and current_user.doctor_profile:
             upcoming_appointments = current_user.doctor_profile.appointments
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": current_user, 
                "appointments_count": len(upcoming_appointments),
                "upcoming_appointments": upcoming_appointments
            },
        )

    return app


app = create_app()


