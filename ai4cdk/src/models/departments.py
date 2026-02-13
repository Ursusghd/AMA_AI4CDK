"""
Benin Departments Model
Defines all departments with their official names and codes
"""

from typing import Dict, List, Tuple
from enum import Enum

class BeninDepartment(str, Enum):
    """Enumeration of all Benin departments with official names."""
    
    ALIBORI = "ALIBORI"
    ATACORA = "ATACORA"
    ATLANTIQUE = "ATLANTIQUE"
    BORGOU = "BORGOU"
    COLLINES = "COLLINES"
    COUFFO = "COUFFO"
    DONGA = "DONGA"
    LITTORAL = "LITTORAL"
    MONO = "MONO"
    OUEME = "OUEME"
    PLATEAU = "PLATEAU"
    ZOU = "ZOU"

class DepartmentInfo:
    """Department information with metadata."""
    
    def __init__(self, name: str, code: str, capital: str, population: int = 0):
        self.name = name
        self.code = code
        self.capital = capital
        self.population = population

# Official departments data from Benin GeoJSON
DEPARTMENTS_DATA = {
    BeninDepartment.ALIBORI: DepartmentInfo(
        name="Alibori",
        code="BJ-AL",
        capital="Kandi",
        population=1516563
    ),
    BeninDepartment.ATACORA: DepartmentInfo(
        name="Atacora",
        code="BJ-AK", 
        capital="Natitingou",
        population=769337
    ),
    BeninDepartment.ATLANTIQUE: DepartmentInfo(
        name="Atlantique",
        code="BJ-AQ",
        capital="Ouidah",
        population=1570670
    ),
    BeninDepartment.BORGOU: DepartmentInfo(
        name="Borgou",
        code="BJ-BO",
        capital="Parakou",
        population=1307057
    ),
    BeninDepartment.COLLINES: DepartmentInfo(
        name="Collines",
        code="BJ-CO",
        capital="Savalou",
        population=726432
    ),
    BeninDepartment.COUFFO: DepartmentInfo(
        name="Couffo",
        code="BJ-CO",
        capital="Dassa-Zoumè",
        population=745318
    ),
    BeninDepartment.DONGA: DepartmentInfo(
        name="Donga",
        code="BJ-DO",
        capital="Djougou",
        population=543130
    ),
    BeninDepartment.LITTORAL: DepartmentInfo(
        name="Littoral",
        code="BJ-LI",
        capital="Cotonou",
        population=2800054
    ),
    BeninDepartment.MONO: DepartmentInfo(
        name="Mono",
        code="BJ-MO",
        capital="Lokossa",
        population=497246
    ),
    BeninDepartment.OUEME: DepartmentInfo(
        name="Ouémé",
        code="BJ-OU",
        capital="Porto-Novo",
        population=1102227
    ),
    BeninDepartment.PLATEAU: DepartmentInfo(
        name="Plateau",
        code="BJ-PL",
        capital="Sakété",
        population=445580
    ),
    BeninDepartment.ZOU: DepartmentInfo(
        name="Zou",
        code="BJ-ZO",
        capital="Abomey",
        population=851146
    )
}

# Department name mappings for data consistency
DEPARTMENT_NAME_MAPPINGS = {
    # Standard names
    "ALIBORI": "Alibori",
    "ATACORA": "Atacora", 
    "ATLANTIQUE": "Atlantique",
    "BORGOU": "Borgou",
    "COLLINES": "Collines",
    "COUFFO": "Couffo",
    "DONGA": "Donga",
    "LITTORAL": "Littoral",
    "MONO": "Mono",
    "OUEME": "Ouémé",
    "PLATEAU": "Plateau",
    "ZOU": "Zou",
    
    # Common variations and case-insensitive mappings
    "alibori": "Alibori",
    "atacora": "Atacora",
    "atlantique": "Atlantique",
    "borgou": "Borgou",
    "collines": "Collines",
    "couffo": "Couffo",
    "donga": "Donga",
    "littoral": "Littoral",
    "mono": "Mono",
    "oueme": "Ouémé",
    "ouémé": "Ouémé",
    "plateau": "Plateau",
    "zou": "Zou",
    
    # French variations (from the data)
    "Alibori": "Alibori",
    "Atacora": "Atacora",
    "Atlantique": "Atlantique", 
    "Borgou": "Borgou",
    "Collines": "Collines",
    "Couffo": "Couffo",
    "Donga": "Donga",
    "Littoral": "Littoral",
    "Mono": "Mono",
    "Ouémé": "Ouémé",
    "Plateau": "Plateau",
    "Zou": "Zou"
}

def get_all_departments() -> List[DepartmentInfo]:
    """Get all departments information."""
    return list(DEPARTMENTS_DATA.values())

def get_department_by_name(name: str) -> DepartmentInfo:
    """
    Get department by name (case-insensitive).
    
    Args:
        name: Department name
        
    Returns:
        DepartmentInfo object or None if not found
    """
    normalized_name = DEPARTMENT_NAME_MAPPINGS.get(name.strip())
    
    if not normalized_name:
        return None
    
    for dept_info in DEPARTMENTS_DATA.values():
        if dept_info.name == normalized_name:
            return dept_info
    
    return None

def get_department_by_code(code: str) -> DepartmentInfo:
    """
    Get department by ISO code.
    
    Args:
        code: ISO department code (e.g., "BJ-AL")
        
    Returns:
        DepartmentInfo object or None if not found
    """
    for dept_info in DEPARTMENTS_DATA.values():
        if dept_info.code == code.upper():
            return dept_info
    
    return None

def normalize_department_name(name: str) -> str:
    """
    Normalize department name to standard format.
    
    Args:
        name: Raw department name
        
    Returns:
        Normalized department name
    """
    if not name:
        return None
    
    return DEPARTMENT_NAME_MAPPINGS.get(name.strip().title(), name.strip())

def is_valid_department(name: str) -> bool:
    """
    Check if a department name is valid.
    
    Args:
        name: Department name to validate
        
    Returns:
        True if valid, False otherwise
    """
    normalized = normalize_department_name(name)
    return normalized in [dept.name for dept in DEPARTMENTS_DATA.values()]

def get_department_statistics() -> Dict[str, any]:
    """
    Get statistics about all departments.
    
    Returns:
        Dictionary with department statistics
    """
    departments = get_all_departments()
    total_population = sum(dept.population for dept in departments)
    
    return {
        "total_departments": len(departments),
        "total_population": total_population,
        "average_population": total_population // len(departments),
        "largest_department": max(departments, key=lambda x: x.population),
        "smallest_department": min(departments, key=lambda x: x.population),
        "departments": [
            {
                "name": dept.name,
                "code": dept.code,
                "capital": dept.capital,
                "population": dept.population,
                "percentage": round((dept.population / total_population) * 100, 2)
            }
            for dept in sorted(departments, key=lambda x: x.name)
        ]
    }

# Department coordinates for mapping (from GeoJSON)
DEPARTMENT_COORDINATES = {
    "Alibori": {"center": [10.691, 2.838], "bounds": [[9.8, 1.5], [12.4, 3.7]]},
    "Atacora": {"center": [10.514, 2.291], "bounds": [[9.2, 1.3], [11.9, 3.4]]},
    "Atlantique": {"center": [6.902, 2.078], "bounds": [[6.2, 1.9], [7.5, 2.5]]},
    "Borgou": {"center": [9.692, 2.838], "bounds": [[8.4, 1.9], [11.7, 3.8]]},
    "Collines": {"center": [7.656, 2.189], "bounds": [[6.5, 1.9], [9.0, 2.8]]},
    "Couffo": {"center": [7.524, 1.643], "bounds": [[6.2, 1.2], [8.9, 2.2]]},
    "Donga": {"center": [9.973, 2.118], "bounds": [[8.6, 1.5], [11.3, 2.8]]},
    "Littoral": {"center": [6.302, 2.330], "bounds": [[6.2, 2.2], [6.5, 2.5]]},
    "Mono": {"center": [6.729, 1.610], "bounds": [[6.1, 1.2], [7.9, 2.3]]},
    "Ouémé": {"center": [6.339, 2.547], "bounds": [[6.2, 2.2], [6.7, 3.0]]},
    "Plateau": {"center": [7.453, 2.401], "bounds": [[6.3, 2.0], [8.1, 2.8]]},
    "Zou": {"center": [7.651, 1.633], "bounds": [[6.1, 1.2], [9.2, 2.5]]}
}

def get_department_coordinates(name: str) -> Dict:
    """
    Get coordinates for a department.
    
    Args:
        name: Department name
        
    Returns:
        Dictionary with center and bounds coordinates
    """
    normalized_name = normalize_department_name(name)
    return DEPARTMENT_COORDINATES.get(normalized_name, {})

# Export all departments as constants for easy access
ALIBORI = DEPARTMENTS_DATA[BeninDepartment.ALIBORI]
ATACORA = DEPARTMENTS_DATA[BeninDepartment.ATACORA]
ATLANTIQUE = DEPARTMENTS_DATA[BeninDepartment.ATLANTIQUE]
BORGOU = DEPARTMENTS_DATA[BeninDepartment.BORGOU]
COLLINES = DEPARTMENTS_DATA[BeninDepartment.COLLINES]
COUFFO = DEPARTMENTS_DATA[BeninDepartment.COUFFO]
DONGA = DEPARTMENTS_DATA[BeninDepartment.DONGA]
LITTORAL = DEPARTMENTS_DATA[BeninDepartment.LITTORAL]
MONO = DEPARTMENTS_DATA[BeninDepartment.MONO]
OUEME = DEPARTMENTS_DATA[BeninDepartment.OUEME]
PLATEAU = DEPARTMENTS_DATA[BeninDepartment.PLATEAU]
ZOU = DEPARTMENTS_DATA[BeninDepartment.ZOU]

# List of all department names for validation
ALL_DEPARTMENT_NAMES = [dept.name for dept in DEPARTMENTS_DATA.values()]
ALL_DEPARTMENT_CODES = [dept.code for dept in DEPARTMENTS_DATA.values()]