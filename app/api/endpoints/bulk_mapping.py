from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any
import asyncio

from app.api.services.mapping import MappingService

router = APIRouter()

# Initialize services
mapping_service = MappingService()

@router.post("/api/v1/bulk-map")
async def bulk_map_terms(
    terms: List[str] = Query(..., description="List of NAMASTE term IDs to map (max 10)")
):
    """Bulk map multiple NAMASTE terms to ICD-11"""
    if len(terms) > 10:
        raise HTTPException(status_code=400, detail="Maximum of 10 terms allowed for bulk mapping.")

    tasks = []
    valid_terms_processed = []

    for term_id in terms:
        # Fetch the NAMASTE term first
        namaste_results = await mapping_service.namaste_service.search_namaste(term_id)
        if namaste_results:
            # Add mapping task for the first found NAMASTE term
            tasks.append(mapping_service.map_namaste_to_icd11(namaste_results[0]))
            valid_terms_processed.append(namaste_results[0])
        else:
            # Log or handle terms that were not found
            print(f"Warning: NAMASTE term with ID '{term_id}' not found for bulk mapping.")

    if not tasks:
        return {"message": "No valid NAMASTE terms found to process."}

    mappings = await asyncio.gather(*tasks)

    # Create a mapping of the original term_id to its mapped result for easier correlation
    # This assumes that the order in 'mappings' corresponds to the order of valid_terms_processed
    mapping_results_dict = {}
    for i, mapped_result in enumerate(mappings):
        mapping_results_dict[valid_terms_processed[i].id] = mapped_result.dict()


    summary = {
        "exact_matches": sum(1 for m in mappings if m.mapping_method == "exact match"),
        "partial_matches": sum(1 for m in mappings if m.mapping_method == "partial_match"),
        "fuzzy_matches": sum(1 for m in mappings if m.mapping_method == "fuzzy_match"),
        "no_matches": sum(1 for m in mappings if m.mapping_method == "no_match")
    }

    return {
        "total_processed": len(mappings),
        "mappings": mapping_results_dict,
        "summary": summary
    }