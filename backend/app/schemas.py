from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: str = "patient"


class UserRead(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    role: str


class DoctorBase(BaseModel):
    specialty: str
    bio: Optional[str] = None
    license_number: str


class DoctorCreate(DoctorBase):
    user_id: int


class DoctorRead(DoctorBase):
    id: int
    user: UserRead

    class Config:
        from_attributes = True


class PatientBase(BaseModel):
    date_of_birth: Optional[date] = None
    insurance_id: Optional[str] = None


class PatientCreate(PatientBase):
    user_id: int


class PatientRead(PatientBase):
    id: int
    user: UserRead

    class Config:
        from_attributes = True


class AppointmentBase(BaseModel):
    doctor_id: int
    patient_id: int
    scheduled_for: datetime
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentRead(AppointmentBase):
    id: int
    status: str

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    appointment_id: int
    amount: float


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceRead(InvoiceBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentBase(BaseModel):
    invoice_id: int
    amount: float


class PaymentCreate(PaymentBase):
    pass


class PaymentRead(PaymentBase):
    id: int
    status: str
    provider_reference: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


