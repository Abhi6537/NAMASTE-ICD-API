from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.api.services.mapping import MappingService

router = APIRouter()

# Initialize services
mapping_service = MappingService()

@router.get("/api/v1/fhir/condition")
async def get_fhir_condition(
    namaste_id: str = Query(..., description="NAMASTE term ID to get FHIR Condition for"),
    patient_id: Optional[str] = Query(None, description="Patient ID for the FHIR resource")
):
    """Get FHIR Condition resource for a NAMASTE term"""
    # Get NAMASTE term
    namaste_results = await mapping_service.namaste_service.search_namaste(namaste_id)
    if not namaste_results:
        raise HTTPException(status_code=404, detail=f"NAMASTE term with ID '{namaste_id}' not found.")

    namaste_term = namaste_results[0] # Assuming unique ID lookup

    # Map to ICD-11
    mapping_result = await mapping_service.map_namaste_to_icd11(namaste_term)

    # Create FHIR resource
    fhir_condition = mapping_service.fhir_service.create_condition_resource(mapping_result, patient_id)
    return fhir_condition.dict()