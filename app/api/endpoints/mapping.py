"""
app/api/routes/mapping.py
Complete API endpoint for NAMASTE to ICD-11 mapping
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any

from app.api.models.common import MappingResult, ICD11Term
from app.api.services.mapping import MappingService

router = APIRouter()
mapping_service = MappingService()


@router.post("/api/v1/map")
async def map_terminology(
    namaste_id: str = Query(..., description="NAMASTE term ID to map"),
    include_fhir: bool = Query(False, description="Include FHIR representation in the response")
):
    """
    Map NAMASTE term to ICD-11 classifications with confidence scores
    
    Args:
        namaste_id: NAMASTE term identifier (e.g., 'AYU001')
        include_fhir: Whether to include FHIR Condition resource in response
        
    Returns:
        Comprehensive mapping result with confidence scores and recommendations
    """
    
    # Search for NAMASTE term
    namaste_results = await mapping_service.namaste_service.search_namaste(namaste_id)

    if not namaste_results:
        raise HTTPException(
            status_code=404, 
            detail=f"NAMASTE term with ID '{namaste_id}' not found."
        )

    namaste_term = namaste_results[0]

    # Perform mapping
    mapping_result = await mapping_service.map_namaste_to_icd11(namaste_term)

    # Extract best match with detailed information
    best_match_dict = _format_best_match(mapping_result)
    
    # Format all matches with individual confidence scores
    all_matches = _format_all_matches(mapping_result)

    # Prepare response
    response_data: Dict[str, Any] = {
        "namaste_term": {
            "id": _get_attr(namaste_term, 'id'),
            "term": _get_attr(namaste_term, 'term'),
            "ayush_system": _get_attr(namaste_term, 'ayush_system'),
            "synonyms": _get_attr(namaste_term, 'synonyms', []),
            "description": _get_attr(namaste_term, 'description'),
            "category": _get_attr(namaste_term, 'category')
        },
        "best_icd11_match": best_match_dict,
        "all_matches": all_matches,
        "mapping": {
            "confidence_score": round(mapping_result.confidence_score, 3),
            "mapping_method": mapping_result.mapping_method,
            "total_matches": len(mapping_result.icd11_matches),
            "created_at": mapping_result.created_at.isoformat(),
            "status": _get_mapping_status(mapping_result)
        },
        "metadata": {
            "confidence_threshold": 0.3,
            "max_results": 5,
            "mapping_version": "1.0",
            "quality_levels": {
                "high": ">= 0.8 (exact or very close match)",
                "medium": "0.6 - 0.8 (good match with minor differences)",
                "low": "0.3 - 0.6 (partial match, review recommended)",
                "none": "< 0.3 (no suitable match found)"
            }
        }
    }

    # Add FHIR resource if requested
    if include_fhir:
        try:
            fhir_condition = mapping_service.fhir_service.create_condition_resource(mapping_result)
            response_data["fhir_condition"] = fhir_condition.dict() if hasattr(fhir_condition, 'dict') else fhir_condition
        except Exception as e:
            response_data["fhir_condition"] = {"error": f"Failed to create FHIR resource: {str(e)}"}

    return response_data


def _get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """Safely get attribute from object or dict"""
    if hasattr(obj, attr):
        return getattr(obj, attr)
    elif isinstance(obj, dict):
        return obj.get(attr, default)
    return default


def _format_best_match(mapping_result: MappingResult) -> Dict[str, Any]:
    """Format the best ICD-11 match with confidence and quality indicators"""
    if not mapping_result.icd11_matches:
        return {
            "found": False,
            "message": _get_no_match_message(mapping_result.mapping_method),
            "confidence_score": 0.0,
            "mapping_quality": "none",
            "mapping_method": mapping_result.mapping_method,
            "recommendation": _get_recommendation(mapping_result.mapping_method)
        }
    
    best_match = mapping_result.icd11_matches[0]
    
    # Convert to dict properly
    if hasattr(best_match, 'dict'):
        best_match_dict = best_match.dict()
    elif hasattr(best_match, 'model_dump'):
        best_match_dict = best_match.model_dump()
    else:
        best_match_dict = dict(best_match) if isinstance(best_match, dict) else {}
    
    # Add confidence and quality metrics
    quality = _get_quality_level(mapping_result.confidence_score)
    best_match_dict.update({
        "found": True,
        "confidence_score": round(mapping_result.confidence_score, 3),
        "mapping_method": mapping_result.mapping_method,
        "mapping_quality": quality,
        "is_reliable": mapping_result.confidence_score >= 0.7,
        "recommendation": _get_recommendation(mapping_result.mapping_method, quality)
    })
    
    return best_match_dict


def _format_all_matches(mapping_result: MappingResult) -> List[Dict[str, Any]]:
    """Format all ICD-11 matches with their information"""
    if not mapping_result.icd11_matches:
        return []
    
    matches = []
    for idx, match in enumerate(mapping_result.icd11_matches, 1):
        # Convert to dict properly
        if hasattr(match, 'dict'):
            match_dict = match.dict()
        elif hasattr(match, 'model_dump'):
            match_dict = match.model_dump()
        else:
            match_dict = dict(match) if isinstance(match, dict) else {}
        
        match_dict.update({
            "rank": idx,
            # Only add detailed metrics to the first match
            "is_best_match": idx == 1
        })
        
        if idx == 1:
            match_dict["confidence_score"] = round(mapping_result.confidence_score, 3)
            match_dict["mapping_quality"] = _get_quality_level(mapping_result.confidence_score)
        
        matches.append(match_dict)
    
    return matches


def _get_quality_level(confidence: float) -> str:
    """Determine mapping quality level based on confidence score"""
    if confidence >= 0.8:
        return "high"
    elif confidence >= 0.6:
        return "medium"
    elif confidence >= 0.3:
        return "low"
    else:
        return "none"


def _get_mapping_status(mapping_result: MappingResult) -> str:
    """Get human-readable mapping status"""
    method = mapping_result.mapping_method
    
    status_map = {
        "exact_match": "success",
        "high_confidence": "success",
        "partial_match": "partial",
        "fuzzy_match": "partial",
        "no_match_above_threshold": "no_match",
        "no_results": "no_results",
        "search_failed": "error",
        "system_error": "error",
        "error": "error"
    }
    
    return status_map.get(method, "unknown")


def _get_no_match_message(method: str) -> str:
    """Get appropriate message for no match scenarios"""
    messages = {
        "no_match_above_threshold": "ICD-11 terms found but confidence too low (< 0.3)",
        "no_results": "No ICD-11 terms found matching the search criteria",
        "search_failed": "Error occurred while searching ICD-11 database",
        "system_error": "System error during mapping process",
        "error": "Mapping failed due to an error"
    }
    
    return messages.get(method, "No suitable ICD-11 match found")


def _get_recommendation(method: str, quality: str = None) -> str:
    """Get recommendation based on mapping method and quality"""
    if method in ["exact_match", "high_confidence"]:
        return "Mapping is reliable and can be used directly"
    elif method == "partial_match":
        return "Good match found, but review recommended for clinical use"
    elif method == "fuzzy_match":
        return "Weak match found, manual review required before use"
    elif method == "no_match_above_threshold":
        return "Manual mapping recommended - no confident matches found"
    elif method == "no_results":
        return "Consider alternative search terms or manual ICD-11 lookup"
    elif method in ["search_failed", "system_error"]:
        return "Please retry or contact system administrator"
    else:
        return "Review and validate mapping before use"