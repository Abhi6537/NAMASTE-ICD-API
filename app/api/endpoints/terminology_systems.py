from fastapi import APIRouter

router = APIRouter()

@router.get("/api/v1/terminology-systems")
async def get_terminology_systems():
    """Get information about supported terminology systems"""
    return {
        "systems": [
            {
                "name": "NAMASTE",
                "full_name": "National AYUSH Morbidity and Standardized Terminologies Electronic Portal",
                "url": "http://namstp.ayush.gov.in",
                "version": "2024", # Assuming a version, adjust if known
                "description": "Indian traditional medicine terminology system covering Ayurveda, Yoga, Unani, Siddha, and Homeopathy."
            },
            {
                "name": "ICD-11",
                "full_name": "International Classification of Diseases, 11th Revision",
                "url": "http://id.who.int/icd11/mms",
                "version": "2024-01",
                "description": "WHO's global standard for diagnostic health information"
            },
            {
                "name": "FHIR",
                "full_name": "Fast Healthcare Interoperability Resources",
                "url": "http://hl7.org/fhir",
                "version": "R4",
                "description": "Healthcare data exchange standard for EMR integration"
            }
        ]
    }