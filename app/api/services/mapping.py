"""
app/api/services/mapping.py
Complete mapping service with fixed type handling
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from app.api.models.common import NAMASTETerm, ICD11Term, MappingResult
from app.core.config import settings
from app.api.services.icd11 import ICD11Service
from app.api.services.namaste import NAMASTEService
from app.api.services.fhir import FHIRService

logger = logging.getLogger(__name__)


class MappingService:
    def __init__(self):
        self.icd11_service = ICD11Service()
        self.namaste_service = NAMASTEService()
        self.fhir_service = FHIRService()
        self.mapping_cache: Dict[str, MappingResult] = {}

    def _convert_to_icd11_term(self, data: Union[dict, ICD11Term]) -> ICD11Term:
        """Convert dictionary to ICD11Term object if needed"""
        if isinstance(data, ICD11Term):
            return data
        
        # Convert dict to ICD11Term
        return ICD11Term(
            id=data.get('id', ''),
            code=data.get('code', ''),
            title=data.get('term', '') or data.get('title', ''),
            category=data.get('category', ''),
            subcategory=data.get('subcategory', ''),
            system=data.get('system', 'ICD11_BIO'),
            system_name=data.get('system_name', 'Biomedicine'),
            description=data.get('description', ''),
            synonyms=data.get('synonyms', []),
            uri=data.get('uri', '')
        )

    def calculate_similarity_score(self, term1: str, term2: str) -> float:
        """Calculate similarity score between two terms"""
        if not term1 or not term2:
            return 0.0
            
        term1_lower = term1.lower().strip()
        term2_lower = term2.lower().strip()

        # Exact match
        if term1_lower == term2_lower:
            return 1.0
        
        # Substring match
        if term1_lower in term2_lower or term2_lower in term1_lower:
            shorter = min(len(term1_lower), len(term2_lower))
            longer = max(len(term1_lower), len(term2_lower))
            return 0.7 + (shorter / longer) * 0.2  # 0.7 to 0.9 range
        
        # Word-based Jaccard similarity
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
            logger.info(f"✅ Cache hit for mapping {namaste_term.id}")
            return self.mapping_cache[cache_key]

        logger.info(f"🔍 Mapping NAMASTE term '{namaste_term.term}' (ID: {namaste_term.id}) to ICD-11...")

        icd11_results: List[ICD11Term] = []
        search_errors: List[str] = []

        try:
            # Search with main term
            logger.info(f"   Searching main term: '{namaste_term.term}'")
            try:
                main_results_raw = await self.icd11_service.search_icd11(namaste_term.term)
                
                # Convert dict results to ICD11Term objects
                main_results = [self._convert_to_icd11_term(r) for r in main_results_raw]
                icd11_results.extend(main_results)
                
                logger.info(f"   ✅ Found {len(main_results)} results for main term")
                if main_results:
                    logger.info(f"      First result: {main_results[0].code} - {main_results[0].title}")
                    
            except Exception as e:
                error_msg = f"Error searching main term: {type(e).__name__}: {str(e)}"
                logger.error(f"   ❌ {error_msg}")
                search_errors.append(error_msg)

            # Search with synonyms (up to 3)
            synonyms = getattr(namaste_term, 'synonyms', []) or []
            if synonyms:
                logger.info(f"   Searching {len(synonyms[:3])} synonyms...")
                for idx, synonym in enumerate(synonyms[:3], 1):
                    if synonym and synonym.strip():
                        try:
                            logger.info(f"      Synonym {idx}: '{synonym}'")
                            additional_results_raw = await self.icd11_service.search_icd11(synonym)
                            additional_results = [self._convert_to_icd11_term(r) for r in additional_results_raw]
                            icd11_results.extend(additional_results)
                            logger.info(f"      ✅ Found {len(additional_results)} results")
                        except Exception as e:
                            error_msg = f"Error searching synonym '{synonym}': {str(e)}"
                            logger.warning(f"      ⚠️ {error_msg}")
                            search_errors.append(error_msg)

            logger.info(f"   📊 Total results collected: {len(icd11_results)}")

            # Check if we got any results
            if not icd11_results:
                logger.warning(f"   ⚠️ No ICD-11 results found")
                if search_errors:
                    logger.error(f"   Errors: {'; '.join(search_errors)}")
                
                return MappingResult(
                    namaste_term=namaste_term,
                    icd11_matches=[],
                    confidence_score=0.0,
                    mapping_method="search_failed" if search_errors else "no_results",
                    created_at=datetime.utcnow()
                )

            # Process and score results
            logger.info(f"   ⚙️ Scoring results...")
            seen_codes = set()
            scored_results: List[tuple[float, ICD11Term]] = []

            for icd_term in icd11_results:
                if not icd_term.code or icd_term.code in seen_codes:
                    continue
                    
                seen_codes.add(icd_term.code)
                
                # Calculate base score
                score = self.calculate_similarity_score(namaste_term.term, icd_term.title)
                
                # Check synonyms for better matches
                if synonyms and icd_term.synonyms:
                    for namaste_syn in synonyms:
                        if not namaste_syn:
                            continue
                        for icd_syn in icd_term.synonyms:
                            if not icd_syn:
                                continue
                            synonym_score = self.calculate_similarity_score(namaste_syn, icd_syn)
                            score = max(score, synonym_score * 0.95)

                # Only include matches above threshold
                if score >= 0.3:
                    scored_results.append((score, icd_term))
                    logger.debug(f"      Match: {icd_term.code} - {icd_term.title} (score: {score:.3f})")

            # Sort by score and take top matches
            scored_results.sort(key=lambda x: x[0], reverse=True)
            top_matches = [term for score, term in scored_results[:5]]

            # Determine confidence and method
            if scored_results:
                confidence = scored_results[0][0]
                if confidence >= 0.9:
                    method = "exact_match"
                elif confidence >= 0.7:
                    method = "high_confidence"
                elif confidence >= 0.5:
                    method = "partial_match"
                else:
                    method = "fuzzy_match"
                    
                logger.info(f"   📊 Best confidence: {confidence:.3f}, method: {method}")
            else:
                confidence = 0.0
                method = "no_match_above_threshold"
                logger.warning(f"   ⚠️ No matches above 0.3 threshold")

            result = MappingResult(
                namaste_term=namaste_term,
                icd11_matches=top_matches,
                confidence_score=confidence,
                mapping_method=method,
                created_at=datetime.utcnow()
            )

            # Cache the result
            self.mapping_cache[cache_key] = result
            
            logger.info(
                f"✅ Mapping complete: {len(top_matches)} matches, "
                f"confidence: {confidence:.2f}, method: {method}"
            )
            
            return result
            
        except Exception as e:
            logger.exception(f"❌ System error mapping {namaste_term.id}: {type(e).__name__}: {str(e)}")
            return MappingResult(
                namaste_term=namaste_term,
                icd11_matches=[],
                confidence_score=0.0,
                mapping_method="system_error",
                created_at=datetime.utcnow()
            )