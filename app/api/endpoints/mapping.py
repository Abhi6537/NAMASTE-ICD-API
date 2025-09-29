from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional

from app.api.models.common import MappingResult
from app.api.services.mapping import MappingService

router = APIRouter()

# Initialize services
mapping_service = MappingService()

@router.post("/api/v1/map")
async def map_terminology(
    namaste_id: str = Query(..., description="NAMASTE term ID to map"),
    include_fhir: bool = Query(False, description="Include FHIR representation in the response")
):
    """Map NAMASTE term to ICD-11 classifications and optionally return FHIR resource"""
    # First, get the NAMASTE term details by its ID
    # A more efficient approach would be to have a direct lookup by ID in NAMASTEService
    # For now, we'll search for it. Assuming search_namaste can take an ID if query matches it.
    # A better NamasteService would have get_term_by_id(self, term_id: str) -> Optional[NAMASTETerm]
    namaste_results = await mapping_service.namaste_service.search_namaste(namaste_id) # Using ID as query for simplicity

    if not namaste_results:
        raise HTTPException(status_code=404, detail=f"NAMASTE term with ID '{namaste_id}' not found.")

    # Take the first result if multiple match the ID (should ideally be one unique ID)
    namaste_term = namaste_results[0]

    # Perform mapping
    mapping_result = await mapping_service.map_namaste_to_icd11(namaste_term)

    response_data: Dict[str, Any] = {
        "mapping": mapping_result.dict(),
        "metadata": {
            "confidence_threshold": 0.3,
            "max_results": 5,
            "mapping_version": "1.0"
        }
    }

    if include_fhir:
        fhir_condition = mapping_service.fhir_service.create_condition_resource(mapping_result)
        response_data["fhir_condition"] = fhir_condition.dict()

    return response_data