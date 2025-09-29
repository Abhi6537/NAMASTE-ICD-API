import json
import logging
from typing import List, Optional

from app.api.models.common import NAMASTETerm
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class NAMASTEService:
    def __init__(self, data_file: str = "data/namaste_data.json"):
        self.data_file = data_file

    async def search_namaste(self, query: str, ayush_system: Optional[str] = None) -> List[NAMASTETerm]:
        """Search NAMASTE database for AYUSH terms using local JSON file."""
        logger.info(f"🔎 Searching NAMASTE for query='{query}', system='{ayush_system}'")

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            results: List[NAMASTETerm] = []
            query_lower = query.lower().strip()
            
            for item in data.get("results", []):
                term = item.get("term", "")
                term_id = item.get("id", "")
                system = item.get("ayush_system", "")

                # Check if query matches ID (exact match, case-insensitive) OR term (contains match)
                matches = False
                if query_lower == term_id.lower():
                    matches = True
                elif query_lower in term.lower():
                    matches = True

                if matches:
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
                                synonyms=item.get("synonyms", []),
                            )
                        )

            if not results:
                logger.warning(f"⚠️ No NAMASTE matches found for '{query}' (system={ayush_system})")
                return []

            logger.info(f"✅ Found {len(results)} NAMASTE matches for query='{query}'")
            return results

        except FileNotFoundError:
            logger.error(f"❌ NAMASTE data file not found: {self.data_file}")
            return []

        except Exception as e:
            logger.error(f"❌ Error searching NAMASTE: {e}")
            return []