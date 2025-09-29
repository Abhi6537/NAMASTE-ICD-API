from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Healthcare Terminology Integration API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/api/v1/search",
            "map": "/api/v1/map",
            "fhir_condition": "/api/v1/fhir/condition",
            "bulk_map": "/api/v1/bulk-map",
            "terminology_systems": "/api/v1/terminology-systems",
            "health": "/health"
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    # In a real app, you'd check service statuses (DB, external APIs)
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "icd11": "connected", # Assuming successful connection during init/first call
            "namaste": "connected (local)",
            "fhir": "active"
        }
    }