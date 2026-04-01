"""
IFC Parser Helper - Konvertiert IFC-Daten in Format für Sidecar Generator
"""

from typing import Dict, Any, List


def ifc_data_to_dict(ifc_data: Any) -> Dict[str, Any]:
    """
    Konvertiert IFC-Parser-Output in Dictionary-Format für Sidecar Generator
    
    Args:
        ifc_data: Output von ifc_parser.parse_ifc()
    
    Returns:
        Dictionary mit strukturierten IFC-Daten
    """
    
    result = {
        "project_name": ifc_data.get("project_name", "Unbekanntes Projekt"),
        "building_guid": ifc_data.get("building_guid"),
        "walls": [],
        "roofs": [],
        "floors": [],
        "windows": [],
        "doors": []
    }
    
    # Wände
    if "walls" in ifc_data:
        for wall in ifc_data["walls"]:
            result["walls"].append({
                "guid": wall.get("guid", ""),
                "name": wall.get("name", ""),
                "area": wall.get("area", 0.0),
                "properties": wall.get("properties", {})
            })
    
    # Dächer
    if "roofs" in ifc_data:
        for roof in ifc_data["roofs"]:
            result["roofs"].append({
                "guid": roof.get("guid", ""),
                "name": roof.get("name", ""),
                "area": roof.get("area", 0.0),
                "properties": roof.get("properties", {})
            })
    
    # Böden
    if "floors" in ifc_data:
        for floor in ifc_data["floors"]:
            result["floors"].append({
                "guid": floor.get("guid", ""),
                "name": floor.get("name", ""),
                "area": floor.get("area", 0.0),
                "properties": floor.get("properties", {})
            })
    
    # Fenster
    if "windows" in ifc_data:
        for window in ifc_data["windows"]:
            result["windows"].append({
                "guid": window.get("guid", ""),
                "name": window.get("name", ""),
                "area": window.get("area", 0.0),
                "properties": window.get("properties", {})
            })
    
    # Türen
    if "doors" in ifc_data:
        for door in ifc_data["doors"]:
            result["doors"].append({
                "guid": door.get("guid", ""),
                "name": door.get("name", ""),
                "area": door.get("area", 0.0),
                "properties": door.get("properties", {})
            })
    
    return result
