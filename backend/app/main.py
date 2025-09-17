from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse
from typing import List, Dict, Any
import uvicorn
from .models import Incident, AnalysisRequest, AnalysisResponse
from .incident_service import IncidentService
import os
import logging

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
numeric_level = getattr(logging, log_level, logging.INFO)

logging.basicConfig(
    level=numeric_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(title="ING Incident Analyzer API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
incident_service = IncidentService()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


@app.get("/")
async def root():
    return {"message": "ING Incident Analyzer API"}

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    try:
        # Check if vector store is accessible
        stats = incident_service.get_stats()
        return {
            "status": "healthy", 
            "service": "ing-incident-analyzer",
            "incident_count": stats.get("total_documents", 0)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}, 500

@app.get("/api/health")
async def api_health():
    """API health check specifically for frontend"""
    return {"status": "ok", "message": "API is running"}

@app.post("/api/incidents", response_model=Dict[str, Any])
async def add_incident(incident: Incident):
    """Add a new incident to the knowledge base"""
    try:
        result = incident_service.add_incident(incident.dict())
        return {"success": True, "incident_id": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/incidents/batch", response_model=Dict[str, Any])
async def add_incidents_batch(incidents: List[Incident]):
    """Add multiple incidents"""
    try:
        result = incident_service.add_incidents_batch([inc.dict() for inc in incidents])
        return {"success": True, "processed_count": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/root-cause", response_model=AnalysisResponse)
async def analyze_root_cause(request: AnalysisRequest):
    """Perform root cause analysis"""
    try:
        result = incident_service.analyze_root_cause(request.query, request.k)
        return AnalysisResponse(result=result, success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/patterns", response_model=AnalysisResponse)
async def analyze_patterns(request: AnalysisRequest):
    """Analyze patterns across incidents"""
    try:
        result = incident_service.analyze_patterns(request.query, request.k)
        return AnalysisResponse(result=result, success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/incidents/stats", response_model=Dict[str, Any])
async def get_stats():
    """Get collection statistics"""
    try:
        stats = incident_service.get_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search", response_model=Dict[str, Any])
async def search_incidents(query: str, k: int = 5):
    """Search for similar incidents"""
    try:
        results = incident_service.search_incidents(query, k)
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/incidents", response_model=Dict[str, Any])
async def get_incidents():
    """Get all incidents for dashboard"""
    try:
        results = incident_service.get_incidents()
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.options("/{rest_of_path:path}")
async def catch_all_options(rest_of_path: str):
    return PlainTextResponse("")  # status 200 + CORS headers

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Allow external connections
        port=8000, 
        reload=True,
        log_level="info"
    )