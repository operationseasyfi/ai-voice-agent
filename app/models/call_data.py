from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class LeadInfo(BaseModel):
    phone_number: str
    lead_name: Optional[str] = None
    loan_amount: Optional[float] = None
    found_in_crm: bool = False

class IntakeData(BaseModel):
    # Intake questions responses
    loan_amount_requested: Optional[float] = Field(None, description="Q1: Exact amount to borrow")
    funds_purpose: Optional[str] = Field(None, description="Q2: What funds will be used for")
    employment_status: Optional[str] = Field(None, description="Q3: Paycheck/self-employed/fixed income")
    credit_card_debt: Optional[float] = Field(None, description="Q4: Total unsecured credit card debt")
    personal_loan_debt: Optional[float] = Field(None, description="Q5: Unsecured personal loan balances")
    other_debt: Optional[float] = Field(None, description="Q6: Medical bills and other balances")
    monthly_income: Optional[float] = Field(None, description="Q7: Monthly income amount")
    ssn_last_four: Optional[str] = Field(None, description="Q9: Last 4 digits of SSN")
    
    @property
    def total_unsecured_debt(self) -> float:
        """Calculate total unsecured debt for routing decision"""
        return (
            (self.credit_card_debt or 0) + 
            (self.personal_loan_debt or 0) + 
            (self.other_debt or 0)
        )

class CallSession(BaseModel):
    call_id: str
    lead_info: LeadInfo
    intake_data: Optional[IntakeData] = None
    queue_assigned: Optional[str] = None
    call_status: str = "active"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)