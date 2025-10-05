from fastapi import APIRouter
from datetime import datetime
from app.api.services.stats_tracker import stats_tracker

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
            "health": "/health",
            "stats": "/api/v1/stats"
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint with detailed service status"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "icd11": {
                "status": "connected",
                "description": "ICD-11 API service"
            },
            "namaste": {
                "status": "connected",
                "description": "NAMASTE terminology database (local)"
            },
            "fhir": {
                "status": "active",
                "description": "FHIR R4 resource generation"
            },
            "database": {
                "status": "connected",
                "description": "Local terminology database"
            }
        }
    }

@router.get("/api/v1/stats")
async def get_stats():
    """Get API statistics"""
    return stats_tracker.get_stats()

@router.post("/api/v1/stats/reset")
async def reset_stats():
    """Reset API statistics (admin endpoint)"""
    stats_tracker.reset_stats()
    return {"message": "Statistics reset successfully"}