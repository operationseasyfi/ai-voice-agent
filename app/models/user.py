from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from datetime import date, datetime
from typing import List, Optional
import re


class Address(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class Preferences(BaseModel):
    language: Optional[str] = "en"
    theme: Optional[str] = "light"


def to_snake_case(name: str) -> str:
    """Convert camelCase or PascalCase to snake_case."""
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


class User(BaseModel):
    uuid: str
    full_name: str
    email: EmailStr
    username: str
    password: str
    phone_number: Optional[str]
    address: Optional[Address] = Address()
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_subscribed_to_newsletter: Optional[bool] = False
    is_active: Optional[bool] = True
    roles: List[str]  # ["user", "admin", "sub_user"]
    associated_user: Optional[str] = None
    permissions: List[str] = [] 
    preferences: Optional[Preferences] = Preferences()
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    active_numbers: Optional[List[str]] = []
    customer_id: Optional[str] = None
    
    @field_validator("date_of_birth", pre=True)
    def convert_date_to_datetime(cls, value):
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())  # Convert to datetime
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        if value is None:
            return value
        return value
