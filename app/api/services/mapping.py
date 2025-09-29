import logging
from datetime import datetime
from typing import List, Dict, Any

from app.api.models.common import NAMASTETerm, ICD11Term, MappingResult
from app.core.config import settings
from app.api.services.icd11 import ICD11Service
from app.api.services.namaste import NAMASTEService

logger = logging.getLogger(__name__)

class MappingService:
    def __init__(self):
        self.icd11_service = ICD11Service()
        self.namaste_service = NAMASTEService()
        self.mapping_cache: Dict[str, MappingResult] = {}

    def calculate_similarity_score(self, term1: str, term2: str) -> float:
        """Calculate similarity score between two terms"""
        if not term1 or not term2:
            return 0.0
            
        # Simple implementation can be enhanced with ML models
        term1_lower = term1.lower().strip()
        term2_lower = term2.lower().strip()

        if term1_lower == term2_lower:
            return 1.0
        elif term1_lower in term2_lower or term2_lower in term1_lower:
            return 0.8
        else:
            # Calculate word overlap using Jaccard similarity
            words1 = set(term1_lower.split())
            words2 = set(term2_lower.split())
            if not words1 or not words2:
                return 0.0
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            return len(intersection) / len(union) if union else 0.0

    async def map_namaste_to_icd11(self, namaste_term: NAMASTETerm) -> MappingResult:
        """Map NAMASTE term to ICD-11 classifications"""
        cache_key = f"map_{namaste_term.id}"
        if cache_key in self.mapping_cache:
            logger.info(f"Cache hit for mapping {namaste_term.id}")
            return self.mapping_cache[cache_key]

        logger.info(f"Mapping NAMASTE term '{namaste_term.term}' (ID: {namaste_term.id}) to ICD-11...")

        try:
            # Search ICD-11 for matches using the term
            icd11_results = await self.icd11_service.search_icd11(namaste_term.term)

            # Also search using synonyms (limit to avoid too many API calls)
            for synonym in namaste_term.synonyms[:3]:
                if synonym and synonym.strip():
                    additional_results = await self.icd11_service.search_icd11(synonym)
                    icd11_results.extend(additional_results)

            # Remove duplicates and score matches
            seen_codes = set()
            scored_results: List[tuple[float, ICD11Term]] = []

            for icd_term in icd11_results:
                if icd_term.code not in seen_codes and icd_term.code:
                    seen_codes.add(icd_term.code)
                    score = self.calculate_similarity_score(namaste_term.term, icd_term.title)

                    # Check synonyms for better matches
                    for synonym in namaste_term.synonyms:
                        for icd_synonym in icd_term.synonyms:
                            if synonym and icd_synonym:
                                synonym_score = self.calculate_similarity_score(synonym, icd_synonym)
                                score = max(score, synonym_score * 0.9)  # Slightly lower weight for synonym

                    if score > 0.3:  # Threshold for inclusion
                        scored_results.append((score, icd_term))

            # Sort by score and take top matches
            scored_results.sort(key=lambda x: x[0], reverse=True)
            top_matches = [term for score, term in scored_results[:5]]  # Take top 5

            # Determine confidence and method
            confidence = 0.0
            method = "no match"
            if scored_results:
                confidence = scored_results[0][0]
                if confidence > 0.8:
                    method = "exact match"
                elif confidence > 0.6:
                    method = "partial match"
                else:
                    method = "fuzzy_match"
            else:
                method = "no match"
                confidence = 0.0

            result = MappingResult(
                namaste_term=namaste_term,
                icd11_matches=top_matches,
                confidence_score=confidence,
                mapping_method=method,
                created_at=datetime.utcnow()
            )

            # Cache result
            self.mapping_cache[cache_key] = result
            logger.info(f"Mapped {namaste_term.id} to {len(top_matches)} ICD-11 terms. Method: {method}, Confidence: {confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error mapping {namaste_term.id}: {e}")
            # Return empty result instead of raising exception
            result = MappingResult(
                namaste_term=namaste_term,
                icd11_matches=[],
                confidence_score=0.0,
                mapping_method="error",
                created_at=datetime.utcnow()
            )
            return result