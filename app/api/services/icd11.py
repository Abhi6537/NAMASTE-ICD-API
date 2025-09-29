import httpx
import logging
import re
from typing import List, Optional, Set
from fastapi import HTTPException

from app.api.models.common import ICD11Term
from app.core.config import settings

logger = logging.getLogger(__name__)


class ICD11Service:
    def __init__(self):
        self.base_url = settings.ICD11_BASE_URL
        self.client_id = settings.ICD11_CLIENT_ID
        self.client_secret = settings.ICD11_CLIENT_SECRET
        self.token_url = "https://icdaccessmanagement.who.int/connect/token"
        self._token_cache = None

    def clean_html_tags(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not text:
            return ""
        cleaned = re.sub(r"<em class='found'>|</em>", "", text)
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        return cleaned.strip()

    def categorize_icd11_code(self, code: str) -> dict:
        """Categorize ICD-11 codes based on their prefix"""
        if not code:
            return {"category": "Unknown", "system": "ICD11_BIO"}
        
        category_map = {
            "1A": {"category": "Bacterial Infections", "system": "ICD11_BIO"},
            "1B": {"category": "Bacterial Infections", "system": "ICD11_BIO"},
            "1C": {"category": "Rickettsial/Chlamydial Infections", "system": "ICD11_BIO"},
            "1D": {"category": "Viral Infections", "system": "ICD11_BIO"},
            "1E": {"category": "Fungal Infections", "system": "ICD11_BIO"},
            "1F": {"category": "Parasitic Infections", "system": "ICD11_BIO"},
            "1G": {"category": "Mycobacterial Infections", "system": "ICD11_BIO"},
            "2A": {"category": "Neoplasms - Malignant", "system": "ICD11_BIO"},
            "2B": {"category": "Neoplasms - Benign", "system": "ICD11_BIO"},
            "2C": {"category": "Neoplasms - In Situ", "system": "ICD11_BIO"},
            "3A": {"category": "Blood Disorders", "system": "ICD11_BIO"},
            "4A": {"category": "Immune System Disorders", "system": "ICD11_BIO"},
            "4B": {"category": "Autoimmune Disorders", "system": "ICD11_BIO"},
            "5A": {"category": "Endocrine Disorders", "system": "ICD11_BIO"},
            "5C": {"category": "Endocrine Disorders", "system": "ICD11_BIO"},
            "6A": {"category": "Mental Disorders", "system": "ICD11_BIO"},
            "8A": {"category": "Nervous System Disorders", "system": "ICD11_BIO"},
            "8B": {"category": "Nervous System Disorders", "system": "ICD11_BIO"},
            "8C": {"category": "Nervous System Disorders", "system": "ICD11_BIO"},
            "8D": {"category": "Nervous System Disorders", "system": "ICD11_BIO"},
            "9A": {"category": "Visual System Disorders", "system": "ICD11_BIO"},
            "9B": {"category": "Visual System Disorders", "system": "ICD11_BIO"},
            "9C": {"category": "Visual System Disorders", "system": "ICD11_BIO"},
            "AA": {"category": "Ear Disorders", "system": "ICD11_BIO"},
            "BA": {"category": "Circulatory System", "system": "ICD11_BIO"},
            "BB": {"category": "Circulatory System", "system": "ICD11_BIO"},
            "BC": {"category": "Circulatory System", "system": "ICD11_BIO"},
            "BD": {"category": "Circulatory System", "system": "ICD11_BIO"},
            "CA": {"category": "Respiratory System", "system": "ICD11_BIO"},
            "CB": {"category": "Respiratory System", "system": "ICD11_BIO"},
            "DA": {"category": "Digestive System", "system": "ICD11_BIO"},
            "DB": {"category": "Digestive System", "system": "ICD11_BIO"},
            "DC": {"category": "Digestive System", "system": "ICD11_BIO"},
            "EA": {"category": "Skin Disorders", "system": "ICD11_BIO"},
            "EB": {"category": "Skin Disorders", "system": "ICD11_BIO"},
            "EC": {"category": "Skin Disorders", "system": "ICD11_BIO"},
            "EE": {"category": "Skin Disorders", "system": "ICD11_BIO"},
            "EL": {"category": "Skin Disorders", "system": "ICD11_BIO"},
            "FA": {"category": "Musculoskeletal System", "system": "ICD11_BIO"},
            "FB": {"category": "Musculoskeletal System", "system": "ICD11_BIO"},
            "GA": {"category": "Genitourinary System", "system": "ICD11_BIO"},
            "GB": {"category": "Genitourinary System", "system": "ICD11_BIO"},
            "HA": {"category": "Sexual Health", "system": "ICD11_BIO"},
            "JA": {"category": "Pregnancy/Childbirth", "system": "ICD11_BIO"},
            "JB": {"category": "Pregnancy/Childbirth", "system": "ICD11_BIO"},
            "KA": {"category": "Perinatal Conditions", "system": "ICD11_BIO"},
            "KB": {"category": "Perinatal Conditions", "system": "ICD11_BIO"},
            "LA": {"category": "Developmental Anomalies", "system": "ICD11_BIO"},
            "LD": {"category": "Developmental Anomalies", "system": "ICD11_BIO"},
            "MA": {"category": "Symptoms/Signs", "system": "ICD11_BIO"},
            "MB": {"category": "Symptoms/Signs", "system": "ICD11_BIO"},
            "MC": {"category": "Symptoms/Signs", "system": "ICD11_BIO"},
            "MD": {"category": "Symptoms/Signs", "system": "ICD11_BIO"},
            "ME": {"category": "Symptoms/Signs", "system": "ICD11_BIO"},
            "MF": {"category": "Symptoms/Signs", "system": "ICD11_BIO"},
            "MG": {"category": "Symptoms/Signs", "system": "ICD11_BIO"},
            "NA": {"category": "Injury/Poisoning", "system": "ICD11_BIO"},
            "NB": {"category": "Injury/Poisoning", "system": "ICD11_BIO"},
            "NC": {"category": "Injury/Poisoning", "system": "ICD11_BIO"},
            "ND": {"category": "Injury/Poisoning", "system": "ICD11_BIO"},
            "NE": {"category": "Injury/Poisoning", "system": "ICD11_BIO"},
            "PA": {"category": "External Causes", "system": "ICD11_BIO"},
            "PB": {"category": "External Causes", "system": "ICD11_BIO"},
            "PC": {"category": "External Causes", "system": "ICD11_BIO"},
            "QA": {"category": "Health Status Factors", "system": "ICD11_BIO"},
            "QB": {"category": "Health Status Factors", "system": "ICD11_BIO"},
            "QC": {"category": "Health Status Factors", "system": "ICD11_BIO"},
            "TM": {"category": "Traditional Medicine", "system": "ICD11_TM2"},
        }
        
        prefix = code[:2].upper()
        return category_map.get(prefix, {"category": "Other", "system": "ICD11_BIO"})

    def extract_subcategory(self, title: str, code: str) -> str:
        """Extract subcategory from title or code patterns"""
        title_lower = title.lower()
        
        # Code-based patterns
        if '.Z' in code or code.endswith('Z'):
            return "Unspecified"
        if '.Y' in code or code.endswith('Y'):
            return "Other Specified"
        
        # Type classifications
        if 'type 1' in title_lower:
            return "Type 1"
        if 'type 2' in title_lower:
            return "Type 2"
        if 'type unspecified' in title_lower:
            return "Type Unspecified"
        
        # Temporal
        if 'acute' in title_lower:
            return "Acute"
        if 'chronic' in title_lower:
            return "Chronic"
        
        # Severity
        if 'severe' in title_lower:
            return "Severe"
        if 'mild' in title_lower:
            return "Mild"
        if 'moderate' in title_lower:
            return "Moderate"
        
        # Origin/Cause
        if 'congenital' in title_lower:
            return "Congenital"
        if 'acquired' in title_lower:
            return "Acquired"
        if 'hereditary' in title_lower or 'genetic' in title_lower:
            return "Hereditary"
        if 'drug' in title_lower or 'chemical' in title_lower:
            return "Drug/Chemical-Induced"
        
        # Pregnancy-related
        if 'pregnancy' in title_lower or 'gestational' in title_lower:
            return "Pregnancy-Related"
        if 'neonatal' in title_lower:
            return "Neonatal"
        
        # Anatomical/Location
        if 'primary' in title_lower:
            return "Primary"
        if 'secondary' in title_lower:
            return "Secondary"
        
        return ""

    def generate_synonyms(self, title: str, code: str) -> List[str]:
        """Generate medical synonyms from title"""
        synonyms_set: Set[str] = set()
        title_lower = title.lower()
        
        # Common medical term mappings
        synonym_patterns = {
            'diabetes mellitus': ['DM', 'diabetes', 'diabetic condition'],
            'type 1 diabetes': ['T1DM', 'insulin-dependent diabetes', 'IDDM'],
            'type 2 diabetes': ['T2DM', 'non-insulin-dependent diabetes', 'NIDDM'],
            'hypertension': ['high blood pressure', 'HTN', 'elevated BP'],
            'myocardial infarction': ['heart attack', 'MI', 'coronary thrombosis'],
            'cerebrovascular accident': ['stroke', 'CVA', 'brain attack'],
            'pneumonia': ['lung infection', 'pulmonary infection'],
            'gastritis': ['stomach inflammation'],
            'nephropathy': ['kidney disease', 'renal disease'],
            'retinopathy': ['eye disease', 'retinal disease'],
            'neuropathy': ['nerve damage', 'nerve disease'],
            'arthropathy': ['joint disease'],
            'coma': ['unconsciousness', 'loss of consciousness'],
            'acidosis': ['metabolic acidosis', 'acid buildup'],
            'insipidus': ['DI', 'water diabetes'],
        }
        
        # Check patterns
        for key, syns in synonym_patterns.items():
            if key in title_lower:
                synonyms_set.update(syns[:3])
        
        # Extract abbreviations
        words = title.split()
        if len(words) >= 2:
            abbrev = ''.join([w[0].upper() for w in words if len(w) > 2])
            if 2 <= len(abbrev) <= 5:
                synonyms_set.add(abbrev)
        
        # Remove duplicates and original title
        synonyms_set.discard(title)
        synonyms_set.discard(title.lower())
        
        return sorted(list(synonyms_set))[:5]

    def generate_rich_description(self, title: str, code: str, category: str) -> str:
        """Generate detailed medical description"""
        title_lower = title.lower()
        
        # Specific condition descriptions
        if 'type 1 diabetes' in title_lower:
            return "An autoimmune metabolic disorder characterized by absolute insulin deficiency due to pancreatic beta-cell destruction, requiring lifelong insulin therapy."
        if 'type 2 diabetes' in title_lower:
            return "A metabolic disorder characterized by insulin resistance and relative insulin deficiency, typically associated with obesity and lifestyle factors."
        if 'gestational diabetes' in title_lower or ('diabetes' in title_lower and 'pregnancy' in title_lower):
            return "A form of diabetes mellitus that develops during pregnancy, characterized by glucose intolerance with onset or first recognition during gestation."
        if 'diabetic neuropathy' in title_lower:
            return "Nerve damage resulting from chronic hyperglycemia in diabetes, affecting peripheral, autonomic, or cranial nerves."
        if 'diabetic retinopathy' in title_lower:
            return "Microvascular retinal damage caused by chronic hyperglycemia, potentially leading to vision impairment or blindness."
        if 'diabetic nephropathy' in title_lower:
            return "Progressive kidney disease caused by damage to kidney capillaries due to chronic diabetes, potentially leading to end-stage renal disease."
        if 'diabetic foot' in title_lower:
            return "A complex complication of diabetes involving neuropathy, peripheral vascular disease, and infection risk, potentially leading to ulceration or amputation."
        if 'diabetic coma' in title_lower:
            return "A life-threatening complication of diabetes characterized by severe hyperglycemia or hypoglycemia leading to altered consciousness or coma."
        if 'diabetic acidosis' in title_lower or 'ketoacidosis' in title_lower:
            return "A serious metabolic complication characterized by hyperglycemia, ketone body accumulation, and metabolic acidosis, commonly occurring in Type 1 diabetes."
        if 'diabetes insipidus' in title_lower:
            return "A disorder characterized by excessive thirst and excretion of large amounts of dilute urine, caused by deficiency of antidiuretic hormone or renal resistance to ADH."
        
        # Category-based descriptions
        category_descriptions = {
            'Endocrine Disorders': f"An endocrine system disorder affecting hormonal regulation and metabolic processes, classified as {title}.",
            'Pregnancy/Childbirth': f"A pregnancy-related condition involving {title}, requiring specialized obstetric care and monitoring.",
            'Musculoskeletal System': f"A musculoskeletal condition affecting joints, bones, or connective tissue, presenting as {title}.",
            'Digestive System': f"A gastrointestinal disorder affecting the digestive system, classified as {title}.",
            'Respiratory System': f"A respiratory condition affecting pulmonary function, presenting as {title}.",
            'Circulatory System': f"A cardiovascular disorder affecting blood circulation or heart function, classified as {title}.",
            'Nervous System Disorders': f"A neurological condition affecting the nervous system, presenting as {title}.",
        }
        
        if category in category_descriptions:
            return category_descriptions[category]
        
        # Fallback
        return f"A medical condition classified under ICD-11 as {title}, requiring clinical assessment and appropriate medical management."

    async def fetch_detailed_info(self, uri: str, token: str) -> dict:
        """Fetch detailed information including definition and synonyms from ICD-11"""
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "API-Version": "v2",
                "Accept-Language": "en"
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(uri, headers=headers)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning(f"Could not fetch details from {uri}: {e}")
        return {}

    async def get_token(self) -> str:
        """Fetch OAuth2 token for ICD-11 API with caching"""
        if self._token_cache:
            return self._token_cache
            
        if not self.client_id or not self.client_secret:
            logger.error("Missing ICD-11 credentials in settings")
            raise HTTPException(status_code=500, detail="ICD-11 credentials not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "icdapi_access",
                "grant_type": "client_credentials",
            }

            try:
                response = await client.post(self.token_url, headers=headers, data=data)
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch ICD-11 token: {response.status_code} {response.text}")
                    raise HTTPException(status_code=500, detail="ICD-11 token request failed")

                token_data = response.json()
                token = token_data.get("access_token")
                if not token:
                    logger.error("No access_token found in ICD-11 response")
                    raise HTTPException(status_code=500, detail="ICD-11 token missing in response")

                self._token_cache = token
                logger.info("ICD-11 access token fetched successfully")
                return token
                
            except httpx.RequestError as e:
                logger.error(f"Network error fetching ICD-11 token: {e}")
                raise HTTPException(status_code=500, detail="Network error connecting to ICD-11")

    async def search_icd11(self, query: str, use_flexisearch: bool = True) -> List[dict]:
        """Search ICD-11 database with enriched data"""
        if not query or query.strip() == "":
            return []
            
        try:
            token = await self.get_token()
            
            endpoints_to_try = [
                f"{self.base_url}/mms/search",
                f"{self.base_url}/search", 
                f"{self.base_url}/mms/flexisearch",
                f"{self.base_url}/release/11/2024-01/mms/search"
            ]

            params = {
                "q": query.strip(),
                "subtreeFilterUsesFoundationDescendants": "false",
                "includeKeywordResult": "true",
                "useFlexisearch": str(use_flexisearch).lower()
            }
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "API-Version": "v2",
                "Accept-Language": "en"
            }

            results: List[dict] = []
            seen_codes: Set[str] = set()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for url in endpoints_to_try:
                    try:
                        logger.info(f"Trying ICD-11 endpoint: {url}, query: '{query}'")
                        response = await client.get(url, headers=headers, params=params)
                        
                        if response.status_code == 200:
                            data = response.json()
                            logger.info(f"Success with endpoint: {url}")
                            
                            entities = (
                                data.get("destinationEntities", []) or 
                                data.get("entities", []) or 
                                data.get("searchResults", []) or
                                data.get("results", [])
                            )

                            for item in entities:
                                # Extract title
                                title = ""
                                if isinstance(item.get("title"), dict):
                                    title = item["title"].get("@value", "")
                                else:
                                    title = item.get("title", "") or item.get("name", "")
                                title = self.clean_html_tags(title)
                                
                                # Extract code
                                code = item.get("theCode", "") or item.get("code", "")
                                
                                # Skip duplicates
                                if code in seen_codes or not code:
                                    continue
                                seen_codes.add(code)
                                
                                # Get full URI for detailed fetch
                                uri = item.get("id", "") or item.get("@id", "") or item.get("uri", "")
                                
                                # Fetch detailed information
                                detailed_info = await self.fetch_detailed_info(uri, token)
                                
                                # Extract definition from detailed info
                                definition = ""
                                if detailed_info:
                                    def_data = detailed_info.get("definition", {})
                                    if isinstance(def_data, dict):
                                        definition = def_data.get("@value", "")
                                    elif isinstance(def_data, str):
                                        definition = def_data
                                
                                definition = self.clean_html_tags(definition)
                                
                                # Get category info
                                category_info = self.categorize_icd11_code(code)
                                
                                # Generate rich description
                                if not definition or len(definition) < 20:
                                    description = self.generate_rich_description(title, code, category_info["category"])
                                else:
                                    description = definition
                                
                                # Extract subcategory
                                subcategory = self.extract_subcategory(title, code)
                                
                                # Generate synonyms
                                api_synonyms: List[str] = []
                                if detailed_info:
                                    synonym_data = detailed_info.get("synonym", [])
                                    if isinstance(synonym_data, list):
                                        for syn in synonym_data[:3]:
                                            if isinstance(syn, dict):
                                                syn_text = syn.get("label", {}).get("@value", "")
                                                if syn_text:
                                                    api_synonyms.append(self.clean_html_tags(syn_text))
                                
                                # Combine API synonyms with generated ones
                                generated_syns = self.generate_synonyms(title, code)
                                all_synonyms = list(dict.fromkeys(api_synonyms + generated_syns))[:5]
                                
                                if title:
                                    organized_result = {
                                        "id": uri,
                                        "code": code,
                                        "term": title,
                                        "category": category_info["category"],
                                        "subcategory": subcategory,
                                        "system": category_info["system"],
                                        "system_name": "Traditional Medicine Module 2" if category_info["system"] == "ICD11_TM2" else "Biomedicine",
                                        "description": description,
                                        "synonyms": all_synonyms,
                                        "uri": uri
                                    }
                                    results.append(organized_result)
                            
                            break
                            
                        else:
                            logger.warning(f"Endpoint {url} returned {response.status_code}")
                            
                    except httpx.RequestError as e:
                        logger.warning(f"Network error with endpoint {url}: {e}")
                        continue
                    except Exception as e:
                        logger.warning(f"Error with endpoint {url}: {e}")
                        continue

            if not results:
                logger.warning(f"No ICD-11 results found for query='{query}'")
            else:
                logger.info(f"Found {len(results)} ICD-11 matches for query='{query}'")
            
            return results

        except Exception as e:
            logger.error(f"Unexpected error in ICD-11 search: {e}")
            return []