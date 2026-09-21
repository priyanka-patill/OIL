import re
from typing import Dict, Any, List

HAZARD_CATEGORIES = [
    {
        "category": "Hazardous Atmosphere / Toxic Gas",
        "keywords": [r"h2s", r"gas leak", r"toxic", r"asphyx", r"vapor", r"steam leak", r"oxygen deficien", r"hydrocarbon leak"]
    },
    {
        "category": "Pressurized System / Energy Release",
        "keywords": [r"pressure", r"pipe burst", r"flange leak", r"valv", r"pneumatic", r"hydraulic", r"psi", r"bar"]
    },
    {
        "category": "Moving / Rotating Machinery",
        "keywords": [r"pump", r"compressor", r"turbine", r"conveyor", r"shaft", r"nip point", r"entangle", r"pinch point"]
    },
    {
        "category": "Electrical / High Voltage",
        "keywords": [r"electric", r"cable", r"breaker", r"short circuit", r"shock", r"arc flash", r"substation", r"transformer"]
    },
    {
        "category": "Thermal / Fire / Explosion",
        "keywords": [r"fire", r"spark", r"explosion", r"combust", r"hot liquid", r"burn", r"thermal", r"flare"]
    },
    {
        "category": "Fall / Height / Drop Hazard",
        "keywords": [r"fall", r"height", r"scaffold", r"ladder", r"drop", r"floor opening", r"hole", r"platform"]
    },
    {
        "category": "Chemical / Corrosive Contact",
        "keywords": [r"acid", r"caustic", r"chemical splash", r"corrosive", r"solvent", r"toxic spill"]
    },
]

def analyze_hazards(report_data: Dict[str, Any]) -> List[str]:
    """
    Evaluates observation text and equipment context to identify potential operational hazards.
    """
    text_content = f"{report_data.get('description', '')} {report_data.get('refinery_unit', '')} {report_data.get('equipment_id', '')} {report_data.get('activity', '')}".lower()
    
    detected_hazards = []
    
    for haz in HAZARD_CATEGORIES:
        if any(re.search(pattern, text_content, re.IGNORECASE) for pattern in haz["keywords"]):
            detected_hazards.append(haz["category"])
            
    return detected_hazards
