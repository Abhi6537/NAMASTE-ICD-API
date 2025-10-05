from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

# Import routers
from app.api.endpoints.general import router as general_router
from app.api.endpoints.search import router as search_router
from app.api.endpoints.mapping import router as mapping_router
from app.api.endpoints.fhir import router as fhir_router
from app.api.endpoints.bulk_mapping import router as bulk_mapping_router
from app.api.endpoints.terminology_systems import router as terminology_systems_router

# Import stats tracker
from app.api.services.stats_tracker import stats_tracker

app = FastAPI(
    title="Healthcare Terminology Integration API",
    description="Integrates ICD-11, NAMASTE, and FHIR for healthcare interoperability",
    version="1.0.0"
)

# CORS configuration for EMR integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stats tracking middleware - EXCLUDE monitoring endpoints
@app.middleware("http")
async def track_requests(request: Request, call_next):
    # List of endpoints to exclude from tracking
    excluded_paths = ['/health', '/api/v1/stats', '/api/v1/stats/reset', '/docs', '/openapi.json', '/redoc']
    
    # Check if the path should be excluded
    should_track = not any(request.url.path == excluded or request.url.path.startswith(excluded) 
                          for excluded in excluded_paths)
    
    start_time = time.time()
    
    # Process the request
    response = await call_next(request)
    
    # Only track if not excluded
    if should_track:
        # Calculate response time in milliseconds
        response_time = (time.time() - start_time) * 1000
        
        # Record the request
        stats_tracker.record_request(
            endpoint=request.url.path,
            response_time=response_time,
            status_code=response.status_code
        )
    
    return response

# Add routers to the application
app.include_router(general_router)
app.include_router(search_router)
app.include_router(mapping_router)
app.include_router(fhir_router)
app.include_router(bulk_mapping_router)
app.include_router(terminology_systems_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)