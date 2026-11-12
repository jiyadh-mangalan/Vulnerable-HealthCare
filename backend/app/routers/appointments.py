import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user_from_token

router = APIRouter(prefix="/appointments", tags=["appointments"])
templates = Jinja2Templates(directory="backend/app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_appointments_page(
    request: Request,
    current_user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    query = db.query(models.Appointment).order_by(models.Appointment.scheduled_for.desc())
    
    # Simple role check for what to show
    if current_user.role == "patient" and current_user.patient_profile:
        query = query.filter(models.Appointment.patient_id == current_user.patient_profile.id)
    elif current_user.role == "doctor" and current_user.doctor_profile:
        query = query.filter(models.Appointment.doctor_id == current_user.doctor_profile.id)
    # else: show all (admin/staff)
    
    appointments = query.all()
    # Get all doctors for the booking form
    doctors = db.query(models.Doctor).all()
    return templates.TemplateResponse("appointments.html", {
        "request": request, 
        "user": current_user,
        "appointments": appointments,
        "doctors": doctors
    })

@router.post("/book")
async def book_appointment(
    request: Request,
    doctor_id: int = Form(...),
    scheduled_for: str = Form(...), # datetime string
    notes: str = Form(None),
    current_user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    # Retrieve patient profile
    if current_user.role != "patient":
         return templates.TemplateResponse("appointments.html", {
            "request": request, "user": current_user, "appointments": [], 
            "error": "Only patients can book appointments."
        })
    
    patient_id = current_user.patient_profile.id

    # VULNERABILITY: Race Condition
    # Check if slot is taken
    existing = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.scheduled_for == scheduled_for
    ).first()
    
    if existing:
         # Already booked
         return RedirectResponse(url="/appointments?error=Slot taken", status_code=303)

    # VULNERABILITY: Artificial Delay to allow Race Condition exploitation
    time.sleep(2) 
    
    # Double booking possible if another request comes in here during sleep
    
    appt = models.Appointment(
        doctor_id=doctor_id,
        patient_id=patient_id,
        scheduled_for=scheduled_for,
        notes=notes,
        status="scheduled"
    )
    db.add(appt)
    db.commit()
    
    return RedirectResponse(url="/appointments?success=Booked", status_code=303)

@router.post("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: int,
    current_user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    # VULNERABILITY: IDOR / Broken Access Control
    # We allow canceling ANY appointment ID without checking if it belongs to current_user
    
    appt = db.get(models.Appointment, appointment_id)
    if not appt:
        return RedirectResponse(url="/appointments?error=Not Found", status_code=303)
        
    appt.status = "cancelled"
    db.commit()
    
    return RedirectResponse(url="/appointments?success=Cancelled", status_code=303)



