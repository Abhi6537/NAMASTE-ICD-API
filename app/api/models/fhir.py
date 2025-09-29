from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class FHIRCodeableConcept(BaseModel):
    """FHIR R4 CodeableConcept"""
    coding: List[Dict[str, Any]]
    text: Optional[str] = None

class FHIRCondition(BaseModel):
    """FHIR R4 Condition Resource"""
    resourceType: str = "Condition"
    id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    code: FHIRCodeableConcept
    subject: Optional[Dict[str, Any]] = None
    recordedDate: Optional[str] = None
    note: Optional[List[Dict[str, Any]]] = None