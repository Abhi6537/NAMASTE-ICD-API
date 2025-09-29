from datetime import datetime
from typing import List, Dict, Any, Optional

from app.api.models.common import MappingResult
from app.api.models.fhir import FHIRCodeableConcept, FHIRCondition
from app.core.config import settings

class FHIRService:
    def create_codeable_concept(self, mapping: MappingResult) -> FHIRCodeableConcept:
        """Create FHIR CodeableConcept from mapping"""
        codings = []
        # Add NAMASTE coding
        codings.append({
            "system": "http://namstp.ayush.gov.in",
            "code": mapping.namaste_term.id,
            "display": mapping.namaste_term.term,
            "userSelected": True
        })
        # Add ICD-11 codings (limit to top 2 matches)
        for icd_term in mapping.icd11_matches[:2]:
            codings.append({
                "system": "http://id.who.int/icd11/mms",
                "code": icd_term.code,
                "display": icd_term.title
            })
        return FHIRCodeableConcept(
            coding=codings,
            text=mapping.namaste_term.description or mapping.namaste_term.term
        )

    def create_condition_resource(self, mapping: MappingResult, patient_id: Optional[str] = None) -> FHIRCondition:
        """Create FHIR Condition resource from mapping"""
        condition = FHIRCondition(
            id=f"condition-{mapping.namaste_term.id}-{datetime.utcnow().timestamp()}", # Unique ID
            meta={
                "profile": [
                    "http://hl7.org/fhir/StructureDefinition/Condition"
                ],
                "lastUpdated": datetime.utcnow().isoformat()
            },
            code=self.create_codeable_concept(mapping),
            recordedDate=datetime.utcnow().isoformat()
        )
        if patient_id:
            condition.subject = {
                "reference": f"Patient/{patient_id}",
                "type": "Patient"
            }
        # Add mapping confidence as a note
        condition.note = [{
            "text": f"Mapping confidence: {mapping.confidence_score:.2f} ({mapping.mapping_method})"
        }]
        return condition