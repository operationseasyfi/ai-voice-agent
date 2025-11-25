"""
Recording Service - Fetches call recordings from SignalWire after call ends
"""
import httpx
from typing import Optional, Dict, Any
from app.config import settings
import logging
import base64

logger = logging.getLogger(__name__)


class RecordingService:
    """
    Service to fetch call recordings from SignalWire API.
    """
    
    def __init__(self):
        self.space_url = settings.SIGNALWIRE_SPACE_URL
        self.project_id = settings.SIGNALWIRE_PROJECT_ID
        self.api_token = settings.SIGNALWIRE_API_TOKEN
        
        # Build base URL and auth
        self.base_url = f"https://{self.space_url}/api/laml/2010-04-01/Accounts/{self.project_id}"
        self._auth = base64.b64encode(
            f"{self.project_id}:{self.api_token}".encode()
        ).decode()
    
    async def get_call_recording(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """
        Fetch recording for a specific call.
        
        Args:
            call_sid: The SignalWire call SID
            
        Returns:
            Recording info dict with url, duration, etc. or None if not found
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/Calls/{call_sid}/Recordings.json",
                    headers={
                        "Authorization": f"Basic {self._auth}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch recordings for call {call_sid}: {response.status_code}")
                    return None
                
                data = response.json()
                recordings = data.get("recordings", [])
                
                if not recordings:
                    logger.info(f"No recordings found for call {call_sid}")
                    return None
                
                # Get the first (usually only) recording
                recording = recordings[0]
                recording_sid = recording.get("sid")
                
                # Build recording URL
                recording_url = f"https://{self.space_url}/api/laml/2010-04-01/Accounts/{self.project_id}/Recordings/{recording_sid}.mp3"
                
                return {
                    "recording_sid": recording_sid,
                    "recording_url": recording_url,
                    "duration": recording.get("duration"),
                    "status": recording.get("status"),
                    "date_created": recording.get("date_created")
                }
                
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching recording for call {call_sid}")
            return None
        except Exception as e:
            logger.error(f"Error fetching recording for call {call_sid}: {str(e)}")
            return None
    
    async def get_call_details(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full call details from SignalWire.
        
        Args:
            call_sid: The SignalWire call SID
            
        Returns:
            Call details dict or None if not found
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/Calls/{call_sid}.json",
                    headers={
                        "Authorization": f"Basic {self._auth}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch call details for {call_sid}: {response.status_code}")
                    return None
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Error fetching call details for {call_sid}: {str(e)}")
            return None


# Singleton instance
recording_service = RecordingService()

