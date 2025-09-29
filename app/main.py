from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import routers
from app.api.endpoints import (
    general,
    search,
    mapping,
    fhir,
    bulk_mapping,
    terminology_systems
)

app = FastAPI(
    title="Healthcare Terminology Integration API",
    description="Integrates ICD-11, NAMASTE, and FHIR for healthcare interoperability",
    version="1.0.0"
)

# CORS configuration for EMR integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files for local Namaste data if you serve it that way
# If you use a local JSON file as shown in NAMASTEService, you might not need this.
# If you need to serve it directly via HTTP, you would configure a server for that.
# For demonstration, if namaste_data.json is in a 'static' folder in the root:
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Add routers to the application
app.include_router(general.router)
app.include_router(search.router)
app.include_router(mapping.router)
app.include_router(fhir.router)
app.include_router(bulk_mapping.router)
app.include_router(terminology_systems.router)

# Add a health check endpoint that isn't part of a router if preferred
# Or ensure it's covered by the general router.

# Optional: Root path for health check if not covered by a router
# @app.get("/health")
# async def health_check():
#     return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # This block is typically for running the app directly during development
    # For production, you would use a WSGI server like Gunicorn with Uvicorn workers.
    uvicorn.run(app, host="0.0.0.0", port=8000)