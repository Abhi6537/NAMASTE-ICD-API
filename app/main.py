from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import routers - import the router directly, not the module
from app.api.endpoints.general import router as general_router
from app.api.endpoints.search import router as search_router
from app.api.endpoints.mapping import router as mapping_router
from app.api.endpoints.fhir import router as fhir_router
from app.api.endpoints.bulk_mapping import router as bulk_mapping_router
from app.api.endpoints.terminology_systems import router as terminology_systems_router

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