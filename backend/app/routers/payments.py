from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user_from_token

router = APIRouter(prefix="/payments", tags=["payments"])
templates = Jinja2Templates(directory="backend/app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_payments(
    request: Request,
    current_user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    # View all invoices provided you are logged in (Excessive Data Exposure / IDOR)
    invoices = db.query(models.Invoice).all()
    
    return templates.TemplateResponse("payments.html", {
        "request": request, 
        "user": current_user,
        "invoices": invoices
    })

@router.post("/invoices/create")
async def create_invoice(
    request: Request,
    appointment_id: int = Form(...),
    amount: float = Form(...),
    current_user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    # VULNERABILITY: Logic Error / Broken Access Control
    # Anyone can create an invoice, even if not staff
    # Also allows generating invoices for any appointment
    
    # Check for existing
    existing = (
        db.query(models.Invoice)
        .filter(models.Invoice.appointment_id == appointment_id)
        .first()
    )
    if existing:
        return RedirectResponse(url="/payments?error=Invoice exists", status_code=303)

    if amount < 0:
        # VULNERABILITY: We allow negative invoices? (Credits?)
        # Logic error if handled poorly in stats, but here maybe just weird.
        pass

    invoice = models.Invoice(
        appointment_id=appointment_id,
        amount=amount,
        status="pending"
    )
    db.add(invoice)
    db.commit()
    
    return RedirectResponse(url="/payments?success=Invoice Created", status_code=303)


@router.post("/charge")
async def initiate_payment(
    request: Request,
    invoice_id: int = Form(...),
    amount: float = Form(...), # VULNERABILITY: We trust this amount!
    current_user: models.User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    invoice = db.get(models.Invoice, invoice_id)
    if not invoice:
        return RedirectResponse(url="/payments?error=Invalid Invoice", status_code=303)

    # VULNERABILITY: Price Manipulation / Integrity
    # We trust the 'amount' sentinel by the client form.
    # The client can change the hidden input from 100.00 to 1.00 or -50.00
    
    payment = models.Payment(
        invoice_id=invoice_id,
        amount=amount, # Saving what they PAID, not what was owed
        status="success", # Direct success
        provider_reference="VULNERABLE-PAYMENT-REF"
    )
    
    # We mark invoice as paid regardless of amount paid?
    # Logic Error: If paid < amount, should be partial?
    invoice.status = "paid" 

    db.add(payment)
    db.commit()
    
    return RedirectResponse(url=f"/payments?success=Paid ${amount}", status_code=303)



