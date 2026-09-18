from typing import Any, Dict
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class RealtimeEvent(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    type: str = Field(..., description="The type of the event, e.g., notification.created")
    version: int = Field(default=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = Field(..., description="The event payload data")
