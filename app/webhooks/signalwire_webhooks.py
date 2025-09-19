from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any
import json

from app.services.crm_service import crm_service
from app.services.call_router import call_router
from app.models.call_data import CallSession, LeadInfo, IntakeData

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory store for active calls (use Redis in production)
active_calls: Dict[str, CallSession] = {}

@router.post("/call-started")
async def handle_call_started(request: Request):
    """Handle incoming call and perform CRM lookup"""
    try:
        payload = await request.json()
        call_id = payload.get("call_id")
        caller_number = payload.get("from", "").replace("+1", "")
        
        logger.info(f"Call started: {call_id} from {caller_number}")
        
        # Look up lead in CRM
        lead_info = await crm_service.lookup_lead_by_phone(caller_number)
        
        if not lead_info:
            lead_info = LeadInfo(phone_number=caller_number, found_in_crm=False)
        
        # Store call session
        call_session = CallSession(call_id=call_id, lead_info=lead_info)
        active_calls[call_id] = call_session
        
        # Generate AI greeting based on CRM lookup
        if lead_info.found_in_crm and lead_info.lead_name:
            greeting = {
                "type": "personalized_greeting",
                "message": f"Hi, this is James with Easy Finance on a recorded line. Am I speaking with {lead_info.lead_name}? Are you calling regarding the loan offer for ${lead_info.loan_amount:,.0f} you received?"
            }
        else:
            greeting = {
                "type": "generic_greeting", 
                "message": "Hi, this is James with Easy Finance on a recorded line. How can I help you today?"
            }
        
        return JSONResponse(content=greeting)
        
    except Exception as e:
        logger.error(f"Error handling call start: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/intake-data")
async def handle_intake_data(request: Request):
    """Process intake data collected by AI agent"""
    try:
        payload = await request.json()
        call_id = payload.get("call_id")
        
        if call_id not in active_calls:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        call_session = active_calls[call_id]
        
        # Parse intake data from AI agent
        intake_data = IntakeData(
            loan_amount_requested=payload.get("loan_amount_requested"),
            funds_purpose=payload.get("funds_purpose"),
            employment_status=payload.get("employment_status"),
            credit_card_debt=payload.get("credit_card_debt"),
            personal_loan_debt=payload.get("personal_loan_debt"),
            other_debt=payload.get("other_debt"),
            monthly_income=payload.get("monthly_income"),
            ssn_last_four=payload.get("ssn_last_four")
        )
        
        # Update call session
        call_session.intake_data = intake_data
        
        # Update CRM with intake data
        await crm_service.update_lead_intake_data(
            call_session.lead_info.phone_number,
            intake_data
        )
        
        # Determine routing queue
        queue_did = call_router.determine_queue(intake_data)
        call_session.queue_assigned = queue_did
        
        logger.info(f"Intake completed for call {call_id}, routing to {queue_did}")
        
        return JSONResponse(content={"status": "intake_complete", "queue": queue_did})
        
    except Exception as e:
        logger.error(f"Error processing intake data: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/transfer-request")
async def handle_transfer_request(request: Request):
    """Handle call transfer to 3CX queue"""
    try:
        payload = await request.json()
        call_id = payload.get("call_id")
        
        if call_id not in active_calls:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        call_session = active_calls[call_id]
        
        if not call_session.queue_assigned:
            raise HTTPException(status_code=400, detail="No queue assigned for transfer")
        
        # Generate transfer parameters
        transfer_params = call_router.generate_transfer_params(call_session.queue_assigned)
        
        # Update call status
        call_session.call_status = "transferred"
        
        logger.info(f"Transferring call {call_id} to {call_session.queue_assigned}")
        
        return JSONResponse(content={
            "action": "transfer",
            "message": "Please hold while I connect you with a senior underwriter.",
            "transfer_params": transfer_params
        })
        
    except Exception as e:
        logger.error(f"Error handling transfer request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/call-ended")
async def handle_call_ended(request: Request):
    """Clean up call session"""
    try:
        payload = await request.json()
        call_id = payload.get("call_id")
        
        if call_id in active_calls:
            del active_calls[call_id]
            logger.info(f"Call {call_id} ended and cleaned up")
        
        return JSONResponse(content={"status": "call_ended"})
        
    except Exception as e:
        logger.error(f"Error handling call end: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")