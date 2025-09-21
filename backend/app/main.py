from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from typing import List, Dict, Any, Optional
import uvicorn
import os
import logging
import gc
import psutil
import torch
from time import time
from functools import wraps
from .models import Incident, AnalysisRequest, AnalysisResponse
from .incident_service import IncidentService

# Green coding: Environment configuration
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
numeric_level = getattr(logging, log_level, logging.INFO)
MAX_REQUEST_SIZE = os.getenv("MAX_REQUEST_SIZE", "10MB")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # seconds

# Green coding: Optimized logging configuration
logging.basicConfig(
    level=numeric_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Green coding: Resource monitoring decorator
def resource_monitor(func):
    """Decorator to monitor system resources before/after requests"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check system resources before processing
        process = psutil.Process()
        memory_info = process.memory_info()
        cpu_usage = psutil.cpu_percent(interval=None)

        if memory_info.rss > psutil.virtual_memory().available * 0.8:
            logger.warning(f"High memory usage before {func.__name__}: {memory_info.rss} bytes")
            gc.collect()

        if cpu_usage > 80:
            logger.warning(f"High CPU usage before {func.__name__}: {cpu_usage}%")

        start_time = time()
        result = await func(*args, **kwargs)
        duration = time() - start_time

        if duration > 5.0:  # Warn on slow requests
            logger.warning(f"Slow request: {func.__name__} took {duration:.2f}s")

        return result
    return wrapper

app = FastAPI(
    title="AI Incident Analyzer API",
    version="1.0.0",
    docs_url="/api/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url="/api/redoc" if os.getenv("ENABLE_REDOC", "true").lower() == "true" else None
)

# Green coding: Optimized CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600  # Cache preflight requests
)

# Initialize services with lazy loading
incident_service = None

def get_incident_service():
    global incident_service
    if incident_service is None:
        logger.info("Initializing IncidentService")
        incident_service = IncidentService()
    return incident_service

# Initialize service at startup
incident_service = get_incident_service()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Optimized request logging with size tracking"""
    content_length = int(request.headers.get("content-length", 0))
    if content_length > 10 * 1024 * 1024:  # 10MB
        logger.warning(f"Large request: {request.method} {request.url} - {content_length} bytes")

    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Green coding: Resource cleanup middleware
@app.middleware("http")
async def cleanup_resources(request: Request, call_next):
    """Cleanup resources after request processing"""
    try:
        response = await call_next(request)
        return response
    finally:
        # Force cleanup after each request
        gc.collect()
        try:
            if hasattr(torch, 'cuda') and torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass  # torch not available


@app.get("/")
async def root():
    return {"message": "AI Incident Analyzer API"}

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    try:
        # Check if vector store is accessible
        stats = incident_service.get_stats()
        return {
            "status": "healthy", 
            "service": "ai-incident-analyzer",
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
        return {"success": True, "results": [Incident(**data) for data in results]}
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
