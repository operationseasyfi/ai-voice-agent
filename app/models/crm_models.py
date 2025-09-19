from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class CRMLead(BaseModel):
    """CRM lead data model"""
    phone_number: str
    name: Optional[str] = None
    email: Optional[str] = None
    loan_amount: Optional[float] = None
    lead_source: Optional[str] = None
    created_at: Optional[datetime] = None
    status: Optional[str] = None

class CRMIntakeUpdate(BaseModel):
    """Model for updating CRM with intake data"""
    phone_number: str
    intake_data: Dict[str, Any]
    total_unsecured_debt: float
    updated_at: datetime
    call_id: Optional[str] = None