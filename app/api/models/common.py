from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class SearchType(str, Enum):
    NAMASTE = "namaste"
    ICD11 = "icd11"
    BOTH = "both"

class NAMASTETerm(BaseModel):
    id: str
    term: str
    term_hindi: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    ayush_system: str
    description: Optional[str] = None
    synonyms: List[str] = []
    
    @property
    def english_name(self) -> str:
        """Alias for term field"""
        return self.term

class ICD11Term(BaseModel):
    id: str = ""
    uri: str = ""
    code: str
    title: str
    definition: Optional[str] = None
    parent: Optional[str] = None
    children: List[str] = []
    synonyms: List[str] = []

class MappingResult(BaseModel):
    namaste_term: NAMASTETerm
    icd11_matches: List[ICD11Term] = []
    confidence_score: float = 0.0
    mapping_method: str = "no match"
    created_at: datetime = Field(default_factory=datetime.utcnow)