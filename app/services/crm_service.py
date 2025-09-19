import httpx
import logging
from typing import Optional, Dict, Any
from app.config import settings
from app.models.call_data import LeadInfo, IntakeData

logger = logging.getLogger(__name__)

class OCCCRMService:
    def __init__(self):
        self.base_url = settings.OCC_CRM_API_URL
        self.api_key = settings.OCC_CRM_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def lookup_lead_by_phone(self, phone_number: str) -> Optional[LeadInfo]:
        """Look up lead information by phone number"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/leads/lookup",
                    headers=self.headers,
                    params={"phone": phone_number}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return LeadInfo(
                        phone_number=phone_number,
                        lead_name=data.get("name"),
                        loan_amount=data.get("loan_amount"),
                        found_in_crm=True
                    )
                elif response.status_code == 404:
                    # Lead not found, return basic info
                    return LeadInfo(
                        phone_number=phone_number,
                        found_in_crm=False
                    )
                else:
                    logger.error(f"CRM lookup failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error looking up lead: {str(e)}")
            return None
    
    async def update_lead_intake_data(self, phone_number: str, intake_data: IntakeData) -> bool:
        """Push intake data to CRM"""
        try:
            payload = {
                "phone_number": phone_number,
                "intake_data": intake_data.dict(exclude_none=True),
                "total_unsecured_debt": intake_data.total_unsecured_debt,
                "updated_at": intake_data.dict().get("updated_at")
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/leads/intake-update",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Successfully updated CRM for {phone_number}")
                    return True
                else:
                    logger.error(f"Failed to update CRM: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating CRM: {str(e)}")
            return False

# Singleton instance
crm_service = OCCCRMService()