import json
import logging
from typing import List, Optional

from app.api.models.common import NAMASTETerm
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class NAMASTEService:
    def __init__(self, data_file: str = "data/namaste_data.json"):
        import os
        self.data_file = data_file
        logger.info(f"NAMASTE data file path: {os.path.abspath(self.data_file)}")
        logger.info(f"File exists: {os.path.exists(self.data_file)}")

    async def search_namaste(self, query: str, ayush_system: Optional[str] = None) -> List[NAMASTETerm]:
        """Search NAMASTE database for AYUSH terms using local JSON file."""
        logger.info(f"Searching NAMASTE for query='{query}', system='{ayush_system}'")

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Debug logging
            logger.info(f"JSON structure: {type(data)}")
            logger.info(f"Has 'results' key: {'results' in data if isinstance(data, dict) else 'N/A'}")
            logger.info(f"Results count: {len(data.get('results', []))}")

            results: List[NAMASTETerm] = []
            query_lower = query.lower().strip()
            
            for item in data.get("results", []):
                term = item.get("term", "")
                term_id = item.get("id", "")
                system = item.get("ayush_system", "")
                synonyms = item.get("synonyms", [])

                # Check multiple match conditions
                matches = False
                match_reason = ""
                
                # 1. Exact ID match
                if query_lower == term_id.lower():
                    matches = True
                    match_reason = "ID match"
                # 2. Term contains query
                elif query_lower in term.lower():
                    matches = True
                    match_reason = "Term contains query"
                # 3. Query contains term (for single-word terms)
                elif term.lower() in query_lower:
                    matches = True
                    match_reason = "Query contains term"
                # 4. Synonym match - CHECK EACH SYNONYM
                else:
                    for syn in synonyms:
                        if syn:  # Make sure synonym is not empty
                            syn_lower = syn.lower()
                            if query_lower in syn_lower or syn_lower in query_lower:
                                matches = True
                                match_reason = f"Synonym match: '{syn}'"
                                break

                if matches:
                    logger.info(f"  MATCH: {term_id} - {term} ({match_reason})")
                    # Apply AYUSH system filter if specified
                    if not ayush_system or system.lower() == ayush_system.lower():
                        results.append(
                            NAMASTETerm(
                                id=term_id,
                                term=term,
                                term_hindi=item.get("term_hindi"),
                                category=item.get("category", ""),
                                subcategory=item.get("subcategory"),
                                ayush_system=system,
                                description=item.get("description"),
                                synonyms=synonyms,
                            )
                        )

            if not results:
                logger.warning(f"No NAMASTE matches found for '{query}' (system={ayush_system})")
                return []

            logger.info(f"Found {len(results)} NAMASTE matches for query='{query}'")
            return results

        except FileNotFoundError:
            logger.error(f"NAMASTE data file not found: {self.data_file}")
            return []

        except Exception as e:
            logger.error(f"Error searching NAMASTE: {e}", exc_info=True)
            return []