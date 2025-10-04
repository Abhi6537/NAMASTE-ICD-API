from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
import logging
import time

from app.api.models.common import SearchType
from app.api.services.namaste import NAMASTEService
from app.api.services.icd11 import ICD11Service
from app.api.services.mapping import MappingService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
namaste_service = NAMASTEService()
icd11_service = ICD11Service()
mapping_service = MappingService()

def calculate_enhanced_confidence(namaste_dict: dict, icd11_dict: dict) -> float:
    """
    Calculate confidence score using multiple factors:
    1. Term similarity
    2. Synonym matching
    3. Category alignment
    4. Subcategory specificity penalty
    """
    from difflib import SequenceMatcher
    
    # Get field values with fallbacks
    namaste_term = namaste_dict.get('term', '').lower().strip()
    icd11_term = icd11_dict.get('term', icd11_dict.get('title', '')).lower().strip()
    
    if not namaste_term or not icd11_term:
        return 0.0
    
    # 1. Main term similarity using SequenceMatcher
    sequence_similarity = SequenceMatcher(None, namaste_term, icd11_term).ratio()
    
    # 2. Word-level matching
    namaste_words = set(namaste_term.split())
    icd11_words = set(icd11_term.split())
    
    if namaste_words and icd11_words:
        intersection = namaste_words.intersection(icd11_words)
        union = namaste_words.union(icd11_words)
        word_overlap = len(intersection) / len(union)
    else:
        word_overlap = 0.0
    
    # 3. Check for exact word match in term
    exact_word_match = 0.0
    if namaste_term in icd11_term.split() or any(word == namaste_term for word in icd11_words):
        exact_word_match = 0.2
    
    # 4. Synonym matching
    synonym_score = 0.0
    namaste_synonyms = namaste_dict.get('synonyms', [])
    icd11_synonyms = icd11_dict.get('synonyms', [])
    
    for ns in namaste_synonyms[:3]:
        if ns:
            ns_lower = ns.lower().strip()
            # Check against ICD-11 term
            if ns_lower == icd11_term or ns_lower in icd11_term:
                synonym_score = max(synonym_score, 0.85)
            # Check against ICD-11 synonyms
            for is_ in icd11_synonyms:
                if is_:
                    is_lower = is_.lower().strip()
                    sim = SequenceMatcher(None, ns_lower, is_lower).ratio()
                    synonym_score = max(synonym_score, sim * 0.7)
    
    # 5. Category similarity
    category_bonus = 0.0
    namaste_category = namaste_dict.get('category', '').lower()
    icd11_category = icd11_dict.get('category', '').lower()
    
    if namaste_category and icd11_category:
        if namaste_category in icd11_category or icd11_category in namaste_category:
            category_bonus = 0.1
    
    # 6. Subcategory specificity penalty
    # More specific terms (with subcategories) get lower scores for generic queries
    specificity_penalty = 0.0
    icd11_subcategory = icd11_dict.get('subcategory', '').strip()
    
    if icd11_subcategory and icd11_subcategory.lower() not in ['', 'general', 'unspecified']:
        # Specific subcategories get a penalty for generic queries
        specificity_penalty = 0.15
    
    # 7. Length ratio penalty (penalize very different lengths)
    len_ratio = min(len(namaste_term), len(icd11_term)) / max(len(namaste_term), len(icd11_term))
    length_penalty = 1.0 - (0.2 * (1.0 - len_ratio))
    
    # Weighted combination
    base_score = (
        sequence_similarity * 0.3 +
        word_overlap * 0.3 +
        exact_word_match +
        synonym_score * 0.2 +
        category_bonus
    ) * length_penalty
    
    # Apply specificity penalty
    final_score = max(0.0, base_score - specificity_penalty)
    
    return min(final_score, 1.0)

@router.get("/api/v1/search")
async def search_terms(
    q: str = Query(..., description="Search query"),
    source: SearchType = Query(SearchType.BOTH, description="Search source (namaste, icd11, or both)"),
    ayush_system: Optional[str] = Query(None, description="Filter by AYUSH system (e.g., Ayurveda, Yoga)")
):
    """Search for terms in NAMASTE and/or ICD-11 with accurate confidence scores"""
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
                namaste_results = await namaste_service.search_namaste(q, ayush_system)
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
                icd11_results = await icd11_service.search_icd11(q)
                
                # Calculate individual confidence scores when both sources are searched
                if source == SearchType.BOTH and results["namaste_results"]:
                    logger.info(f"🎯 Calculating individual confidence scores for {len(icd11_results)} ICD-11 results...")
                    icd11_results_with_confidence = []
                    
                    # Use the first (most relevant) NAMASTE result
                    primary_namaste_term = results["namaste_results"][0]
                    
                    # Convert to dict if needed
                    namaste_dict = primary_namaste_term if isinstance(primary_namaste_term, dict) else primary_namaste_term.dict()
                    
                    for icd11_term in icd11_results:
                        # Convert to dict if needed
                        icd11_dict = icd11_term if isinstance(icd11_term, dict) else (icd11_term.dict() if hasattr(icd11_term, 'dict') else icd11_term)
                        
                        # Calculate enhanced confidence score
                        confidence = calculate_enhanced_confidence(namaste_dict, icd11_dict)
                        
                        # Add confidence score (rounded to 2 decimals)
                        icd11_dict["confidence_score"] = round(confidence, 2)
                        
                        # Add mapping quality indicator
                        if confidence >= 0.85:
                            icd11_dict["mapping_quality"] = "excellent"
                        elif confidence >= 0.65:
                            icd11_dict["mapping_quality"] = "high"
                        elif confidence >= 0.45:
                            icd11_dict["mapping_quality"] = "medium"
                        elif confidence >= 0.25:
                            icd11_dict["mapping_quality"] = "low"
                        else:
                            icd11_dict["mapping_quality"] = "poor"
                        
                        # Log details for debugging
                        logger.debug(
                            f"  {icd11_dict.get('code', 'N/A')}: {icd11_dict.get('term', '')[:40]}... "
                            f"= {confidence:.2f} ({icd11_dict['mapping_quality']})"
                        )
                        
                        icd11_results_with_confidence.append(icd11_dict)
                    
                    # Sort by confidence score (highest first)
                    icd11_results_with_confidence.sort(
                        key=lambda x: x.get("confidence_score", 0), 
                        reverse=True
                    )
                    
                    results["icd11_results"] = icd11_results_with_confidence
                    
                    # Log score distribution
                    scores = [r.get("confidence_score", 0) for r in icd11_results_with_confidence]
                    if scores:
                        logger.info(
                            f"✅ Confidence scores: "
                            f"Best={scores[0]:.2f}, "
                            f"Worst={scores[-1]:.2f}, "
                            f"Avg={sum(scores)/len(scores):.2f}"
                        )
                else:
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