"""
app/api/models/common.py
Complete models for NAMASTE-ICD11 mapping system
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


# Enum for search types (needed by search.py)
class SearchType(str, Enum):
    """Search type enumeration"""
    NAMASTE = "namaste"
    ICD11 = "icd11"
    BOTH = "both"


class ICD11Term(BaseModel):
    """ICD-11 terminology model matching the structure from ICD11Service"""
    id: str = Field(..., description="Unique identifier/URI")
    code: str = Field(..., description="ICD-11 code (e.g., '5A10', 'MB21.1')")
    title: str = Field(..., description="Official ICD-11 title/term")
    category: str = Field(default="", description="Category (e.g., 'Endocrine Disorders')")
    subcategory: str = Field(default="", description="Subcategory (e.g., 'Type 1', 'Acute')")
    system: str = Field(default="ICD11_BIO", description="System identifier")
    system_name: str = Field(default="Biomedicine", description="System name")
    description: str = Field(default="", description="Detailed medical description")
    synonyms: List[str] = Field(default_factory=list, description="Alternative terms")
    uri: str = Field(default="", description="Full ICD-11 URI")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "http://id.who.int/icd/entity/1234567890",
                "code": "5A11",
                "title": "Type 1 diabetes mellitus",
                "category": "Endocrine Disorders",
                "subcategory": "Type 1",
                "system": "ICD11_BIO",
                "system_name": "Biomedicine",
                "description": "An autoimmune metabolic disorder...",
                "synonyms": ["T1DM", "IDDM", "insulin-dependent diabetes"],
                "uri": "http://id.who.int/icd/entity/1234567890"
            }
        }


class NAMASTETerm(BaseModel):
    """NAMASTE (AYUSH) terminology model"""
    id: str = Field(..., description="NAMASTE term ID (e.g., 'AYU001')")
    term: str = Field(..., description="AYUSH term name")
    ayush_system: str = Field(..., description="AYUSH system (Ayurveda, Yoga, etc.)")
    synonyms: List[str] = Field(default_factory=list, description="Synonyms/translations")
    description: Optional[str] = Field(None, description="Term description")
    category: Optional[str] = Field(None, description="Category/classification")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "AYU001",
                "term": "Jwara",
                "ayush_system": "Ayurveda",
                "synonyms": ["Fever", "Pyrexia"],
                "description": "Fever conditions in Ayurveda",
                "category": "Symptoms"
            }
        }


class MappingResult(BaseModel):
    """Mapping result between NAMASTE and ICD-11"""
    namaste_term: NAMASTETerm
    icd11_matches: List[ICD11Term] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    mapping_method: str = Field(
        description="Method used: exact_match, high_confidence, partial_match, fuzzy_match, no_match_above_threshold, no_results, search_failed, system_error"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "namaste_term": {
                    "id": "AYU001",
                    "term": "Jwara",
                    "ayush_system": "Ayurveda",
                    "synonyms": ["Fever", "Pyrexia"]
                },
                "icd11_matches": [
                    {
                        "code": "MG26",
                        "title": "Fever",
                        "category": "Symptoms/Signs",
                        "description": "Elevated body temperature..."
                    }
                ],
                "confidence_score": 0.85,
                "mapping_method": "high_confidence",
                "created_at": "2025-10-04T20:00:00"
            }
        }