from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
import logging
import time

from app.api.models.common import SearchType, NAMASTETerm, ICD11Term
from app.api.services.mapping import MappingService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services (singleton pattern implicitly via import)
mapping_service = MappingService()

@router.get("/api/v1/search")
async def search_terms(
    q: str = Query(..., description="Search query"),
    source: SearchType = Query(SearchType.BOTH, description="Search source (namaste, icd11, or both)"),
    ayush_system: Optional[str] = Query(None, description="Filter by AYUSH system (e.g., Ayurveda, Yoga)")
):
    """Search for terms in NAMASTE and/or ICD-11"""
    start_time = time.time()
    
    results: Dict[str, Any] = {
        "query": q,
        "source": source.value,
        "namaste_results": [],
        "icd11_results": [],
        "total_results": 0,
        "search_time_ms": 0,
        "status": "success"
    }

    try:
        # Search NAMASTE if requested
        if source in [SearchType.NAMASTE, SearchType.BOTH]:
            try:
                logger.info(f"🔎 Searching NAMASTE for: {q}")
                namaste_results = await mapping_service.namaste_service.search_namaste(q, ayush_system)
                results["namaste_results"] = namaste_results
                logger.info(f"✅ NAMASTE search completed: {len(namaste_results)} results")
            except HTTPException as e:
                if e.status_code == 404:
                    logger.warning(f"⚠️ No NAMASTE results for: {q}")
                    results["namaste_results"] = []
                else:
                    logger.error(f"❌ NAMASTE search error: {e}")
                    results["namaste_results"] = []
            except Exception as e:
                logger.error(f"❌ Unexpected NAMASTE error: {e}")
                results["namaste_results"] = []

        # Search ICD-11 if requested
        if source in [SearchType.ICD11, SearchType.BOTH]:
            try:
                logger.info(f"🔎 Searching ICD-11 for: {q}")
                icd11_results = await mapping_service.icd11_service.search_icd11(q)
                results["icd11_results"] = icd11_results
                logger.info(f"✅ ICD-11 search completed: {len(icd11_results)} results")
            except Exception as e:
                logger.error(f"❌ ICD-11 search error: {e}")
                results["icd11_results"] = []

        # Calculate totals
        results["total_results"] = len(results["namaste_results"]) + len(results["icd11_results"])
        
        # Calculate search time
        end_time = time.time()
        results["search_time_ms"] = int((end_time - start_time) * 1000)
        
        logger.info(f"🎯 Search completed for '{q}': {results['total_results']} total results in {results['search_time_ms']}ms")
        
        # If no results found, return a more informative response
        if results["total_results"] == 0:
            results["status"] = "no_results"
            results["message"] = f"No results found for '{q}' in the selected sources"
            
        return results

    except Exception as e:
        logger.error(f"❌ Search endpoint error: {e}")
        end_time = time.time()
        return {
            "query": q,
            "source": source.value,
            "namaste_results": [],
            "icd11_results": [],
            "total_results": 0,
            "search_time_ms": int((end_time - start_time) * 1000),
            "status": "error",
            "message": f"Search failed: {str(e)}"
        }