"""
Department Service
Business logic for department operations and validation
"""

from typing import List, Dict, Optional
from ..models.departments import (
    get_all_departments, get_department_by_name, get_department_by_code,
    normalize_department_name, is_valid_department, get_department_statistics,
    get_department_coordinates, ALL_DEPARTMENT_NAMES, ALL_DEPARTMENT_CODES
)

class DepartmentService:
    """Service for department-related operations."""
    
    def __init__(self):
        self.departments = get_all_departments()
    
    def get_all_departments_info(self) -> List[Dict]:
        """Get all departments with their information."""
        return [
            {
                "name": dept.name,
                "code": dept.code,
                "capital": dept.capital,
                "population": dept.population
            }
            for dept in self.departments
        ]
    
    def get_department_info(self, name_or_code: str) -> Optional[Dict]:
        """
        Get department information by name or code.
        
        Args:
            name_or_code: Department name or ISO code
            
        Returns:
            Department information or None if not found
        """
        # Try by name first
        dept = get_department_by_name(name_or_code)
        
        # Try by code if name lookup failed
        if not dept:
            dept = get_department_by_code(name_or_code)
        
        if not dept:
            return None
        
        return {
            "name": dept.name,
            "code": dept.code,
            "capital": dept.capital,
            "population": dept.population,
            "coordinates": get_department_coordinates(dept.name)
        }
    
    def validate_department(self, name: str) -> Dict[str, any]:
        """
        Validate a department name.
        
        Args:
            name: Department name to validate
            
        Returns:
            Validation result with normalized name
        """
        if not name or not name.strip():
            return {
                "valid": False,
                "error": "Department name cannot be empty",
                "normalized_name": None,
                "suggestions": ALL_DEPARTMENT_NAMES[:5]
            }
        
        normalized = normalize_department_name(name)
        
        if not normalized:
            return {
                "valid": False,
                "error": "Invalid department name",
                "normalized_name": None,
                "suggestions": self._find_similar_departments(name)
            }
        
        return {
            "valid": True,
            "error": None,
            "normalized_name": normalized,
            "suggestions": []
        }
    
    def get_department_list(self) -> List[str]:
        """Get list of all valid department names."""
        return ALL_DEPARTMENT_NAMES.copy()
    
    def get_department_codes(self) -> List[str]:
        """Get list of all department codes."""
        return ALL_DEPARTMENT_CODES.copy()
    
    def get_statistics(self) -> Dict[str, any]:
        """Get comprehensive department statistics."""
        return get_department_statistics()
    
    def get_coordinates(self, name: str) -> Optional[Dict]:
        """
        Get coordinates for a department.
        
        Args:
            name: Department name
            
        Returns:
            Coordinates dictionary or None if not found
        """
        return get_department_coordinates(name)
    
    def search_departments(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search departments by name or code.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching departments
        """
        if not query:
            return []
        
        query_lower = query.lower()
        results = []
        
        for dept in self.departments:
            # Search by name
            if query_lower in dept.name.lower():
                results.append({
                    "name": dept.name,
                    "code": dept.code,
                    "capital": dept.capital,
                    "population": dept.population,
                    "match_type": "name"
                })
                continue
            
            # Search by code
            if query_lower in dept.code.lower():
                results.append({
                    "name": dept.name,
                    "code": dept.code,
                    "capital": dept.capital,
                    "population": dept.population,
                    "match_type": "code"
                })
            
            # Search by capital
            if query_lower in dept.capital.lower():
                results.append({
                    "name": dept.name,
                    "code": dept.code,
                    "capital": dept.capital,
                    "population": dept.population,
                    "match_type": "capital"
                })
        
        # Sort by relevance and limit results
        results.sort(key=lambda x: (
            x["match_type"] == "name",  # Prioritize name matches
            len(x["name"])  # Shorter names first
        ))
        
        return results[:limit]
    
    def get_population_ranking(self) -> List[Dict]:
        """
        Get departments ranked by population.
        
        Returns:
            List of departments sorted by population (descending)
        """
        sorted_depts = sorted(self.departments, key=lambda x: x.population, reverse=True)
        
        return [
            {
                "rank": i + 1,
                "name": dept.name,
                "code": dept.code,
                "capital": dept.capital,
                "population": dept.population,
                "percentage": round((dept.population / sum(d.population for d in self.departments)) * 100, 2)
            }
            for i, dept in enumerate(sorted_depts)
        ]
    
    def get_regions(self) -> Dict[str, List[str]]:
        """
        Group departments by geographical regions.
        
        Returns:
            Dictionary with regions and their departments
        """
        regions = {
            "Nord": ["Alibori", "Atacora", "Borgou", "Donga"],
            "Centre": ["Collines", "Plateau", "Zou"],
            "Sud": ["Atlantique", "Couffo", "Littoral", "Mono", "Ouémé"]
        }
        
        # Filter to only include valid departments
        valid_regions = {}
        for region, dept_list in regions.items():
            valid_depts = []
            for dept_name in dept_list:
                if is_valid_department(dept_name):
                    valid_depts.append(dept_name)
            if valid_depts:
                valid_regions[region] = valid_depts
        
        return valid_regions
    
    def _find_similar_departments(self, name: str) -> List[str]:
        """
        Find department names similar to the input.
        
        Args:
            name: Input name to match
            
        Returns:
            List of similar department names
        """
        name_lower = name.lower()
        similar = []
        
        for dept_name in ALL_DEPARTMENT_NAMES:
            dept_lower = dept_name.lower()
            
            # Check if the input is a substring of the department name
            if name_lower in dept_lower or dept_lower in name_lower:
                similar.append(dept_name)
            
            # Check for partial matches (first 3 characters)
            if len(name_lower) >= 3 and dept_lower.startswith(name_lower[:3]):
                similar.append(dept_name)
        
        # Remove duplicates and limit to 5 suggestions
        return list(set(similar))[:5]
    
    def get_department_summary(self) -> Dict[str, any]:
        """
        Get a comprehensive summary of all departments.
        
        Returns:
            Dictionary with department summary information
        """
        stats = self.get_statistics()
        
        return {
            "total_departments": stats["total_departments"],
            "total_population": stats["total_population"],
            "average_population": stats["average_population"],
            "largest_department": {
                "name": stats["largest_department"].name,
                "population": stats["largest_department"].population,
                "capital": stats["largest_department"].capital
            },
            "smallest_department": {
                "name": stats["smallest_department"].name,
                "population": stats["smallest_department"].population,
                "capital": stats["smallest_department"].capital
            },
            "regions": self.get_regions(),
            "department_count_by_region": {
                region: len(depts) for region, depts in self.get_regions().items()
            }
        }