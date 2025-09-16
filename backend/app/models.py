from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class Incident(BaseModel):
    incident_id: str
    timestamp: str
    category: str
    severity: str
    description: str
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    affected_components: Optional[List[str]] = None
    impact: Optional[str] = None

class AnalysisRequest(BaseModel):
    query: str
    k: int = 5

class AnalysisResponse(BaseModel):
    success: bool
    result: str
    metadata: Optional[Dict[str, Any]] = None

class StatsResponse(BaseModel):
    total_incidents: int
    total_chunks: int
    by_category: Dict[str, int]
    by_severity: Dict[str, int]