from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any

from app.api.models.common import MappingResult
from app.api.services.mapping import MappingService

router = APIRouter()
mapping_service = MappingService()

@router.post("/api/v1/map")
async def map_terminology(
    namaste_id: str = Query(..., description="NAMASTE term ID to map"),
    include_fhir: bool = Query(False, description="Include FHIR representation in the response")
):
    """Map NAMASTE term to ICD-11 classifications with confidence scores"""
    
    # Search for NAMASTE term
    namaste_results = await mapping_service.namaste_service.search_namaste(namaste_id)

    if not namaste_results:
        raise HTTPException(status_code=404, detail=f"NAMASTE term with ID '{namaste_id}' not found.")

    namaste_term = namaste_results[0]

    # Perform mapping (this already includes confidence score calculation)
    mapping_result = await mapping_service.map_namaste_to_icd11(namaste_term)

    # ✨ Extract the best match with confidence score
    best_match = None
    if mapping_result.icd11_matches:
        best_match = mapping_result.icd11_matches[0]
        best_match_dict = best_match.dict() if hasattr(best_match, 'dict') else best_match
        
        # Add confidence score and mapping quality to the best match
        best_match_dict["confidence_score"] = mapping_result.confidence_score
        best_match_dict["mapping_method"] = mapping_result.mapping_method
        
        # Add mapping quality indicator
        if mapping_result.confidence_score > 0.8:
            best_match_dict["mapping_quality"] = "high"
        elif mapping_result.confidence_score > 0.6:
            best_match_dict["mapping_quality"] = "medium"
        elif mapping_result.confidence_score > 0.3:
            best_match_dict["mapping_quality"] = "low"
        else:
            best_match_dict["mapping_quality"] = "poor"
    else:
        best_match_dict = {
            "message": "No suitable ICD-11 match found",
            "confidence_score": 0.0,
            "mapping_quality": "none"
        }

    # Prepare response
    response_data: Dict[str, Any] = {
        "namaste_term": {
            "id": namaste_term.id if hasattr(namaste_term, 'id') else namaste_term.get('id'),
            "term": namaste_term.term if hasattr(namaste_term, 'term') else namaste_term.get('term'),
            "ayush_system": namaste_term.ayush_system if hasattr(namaste_term, 'ayush_system') else namaste_term.get('ayush_system'),
        },
        "best_icd11_match": best_match_dict,
        "all_matches": [
            {
                **(match.dict() if hasattr(match, 'dict') else match),
                "confidence_score": mapping_result.confidence_score
            }
            for match in mapping_result.icd11_matches
        ],
        "mapping": {
            "confidence_score": mapping_result.confidence_score,
            "mapping_method": mapping_result.mapping_method,
            "total_matches": len(mapping_result.icd11_matches),
            "created_at": mapping_result.created_at.isoformat()
        },
        "metadata": {
            "confidence_threshold": 0.3,
            "max_results": 5,
            "mapping_version": "1.0"
        }
    }

    # Add FHIR resource if requested
    if include_fhir:
        fhir_condition = mapping_service.fhir_service.create_condition_resource(mapping_result)
        response_data["fhir_condition"] = fhir_condition.dict()

    return response_data