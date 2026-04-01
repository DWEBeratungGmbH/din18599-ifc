"""
Sidecar Generator
Generiert DIN18599 Sidecar JSON aus IFC + EVEBI Daten
"""

from typing import Dict, List, Optional
from datetime import datetime
import uuid
from .ifc_parser import IFCGeometry
from .evebi_parser import EVEBIData, EVEBIConstruction
from .mapper import MappingResult


def generate_sidecar(
    ifc_geometry: IFCGeometry,
    evebi_data: EVEBIData,
    mapping_result: MappingResult,
    ifc_filename: str,
    evebi_filename: str
) -> Dict:
    """
    Generiert DIN18599 Sidecar JSON
    
    Args:
        ifc_geometry: Geparste IFC-Geometrie
        evebi_data: Geparste EVEBI-Daten
        mapping_result: Mapping-Ergebnis
        ifc_filename: Name der IFC-Datei
        evebi_filename: Name der EVEBI-Datei
        
    Returns:
        Sidecar JSON (dict)
    """
    
    # Konstruktions-Lookup erstellen
    constructions_by_guid = {c.guid: c for c in evebi_data.constructions}
    
    # Sidecar-Struktur
    sidecar = {
        "$schema": "https://din18599-ifc.de/schema/v2.1/complete",
        "meta": {
            "project_name": ifc_geometry.project_name,
            "project_id": str(uuid.uuid4()),
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "version": "1.0.0",
            "ifc_file_ref": ifc_filename,
            "energy_data_source": {
                "type": "EVEBI",
                "file": evebi_filename,
                "imported_at": datetime.now().isoformat()
            },
            "mapping_stats": mapping_result.stats
        },
        "input": {
            "building": {
                "name": ifc_geometry.building_name or "Unbekanntes Gebäude",
                "address": {
                    "street": "",
                    "city": "",
                    "postal_code": "",
                    "country": "DE"
                },
                "construction_year": None,
                "bgf": None,
                "nrf": None
            },
            "zones": _generate_zones(evebi_data),
            "envelope": _generate_envelope(mapping_result, constructions_by_guid),
            "systems": {
                "heating": [],
                "cooling": [],
                "ventilation": [],
                "dhw": [],
                "lighting": [],
                "renewables": []
            }
        }
    }
    
    return sidecar


def _generate_zones(evebi_data: EVEBIData) -> List[Dict]:
    """Generiert Zonen aus EVEBI-Daten"""
    zones = []
    
    for zone in evebi_data.zones:
        zones.append({
            "id": f"zone_{len(zones) + 1}",
            "name": zone.name,
            "usage_type": "residential",  # TODO: aus EVEBI ableiten
            "area": zone.area,
            "volume": zone.volume,
            "heating_setpoint": zone.heating_setpoint or 20.0,
            "cooling_setpoint": zone.cooling_setpoint,
            "ventilation_rate": None,
            "occupancy": None
        })
    
    return zones


def _generate_envelope(
    mapping_result: MappingResult,
    constructions_by_guid: Dict[str, EVEBIConstruction]
) -> Dict:
    """Generiert Envelope aus Mapping-Ergebnis"""
    
    envelope = {
        "walls_external": [],
        "walls_internal": [],
        "roofs": [],
        "floors": [],
        "windows": [],
        "doors": []
    }
    
    for match in mapping_result.matches:
        ifc_elem = match.ifc_element
        evebi_elem = match.evebi_element
        
        # Konstruktion ermitteln
        construction = None
        if evebi_elem.construction_ref:
            construction = constructions_by_guid.get(evebi_elem.construction_ref)
        
        # Element-Daten
        element = {
            "id": f"{evebi_elem.element_type.lower()}_{ifc_elem.guid[:8]}",
            "name": ifc_elem.name,
            "ifc_guid": ifc_elem.guid,
            "evebi_guid": evebi_elem.guid,
            "posno": ifc_elem.tag,
            "area": evebi_elem.area or ifc_elem.area,
            "orientation": evebi_elem.orientation or ifc_elem.orientation,
            "inclination": evebi_elem.inclination or ifc_elem.inclination,
            "u_value_undisturbed": evebi_elem.u_value,
            "boundary_condition": _map_boundary_condition(evebi_elem.boundary_condition),
            "mapping_confidence": match.confidence,
            "mapping_method": match.match_method
        }
        
        # Konstruktion hinzufügen (falls vorhanden)
        if construction:
            element["construction"] = {
                "name": construction.name,
                "u_value": construction.u_value,
                "total_thickness": construction.total_thickness,
                "layers": [
                    {
                        "material": layer.material_name,
                        "thickness": layer.thickness,
                        "lambda": layer.lambda_value,
                        "position": layer.position
                    }
                    for layer in construction.layers
                ]
            }
        
        # Kategorisierung
        if evebi_elem.element_type == 'Wall':
            if evebi_elem.boundary_condition in ['Aussenluft', 'außen']:
                envelope["walls_external"].append(element)
            else:
                envelope["walls_internal"].append(element)
        elif evebi_elem.element_type == 'Roof':
            envelope["roofs"].append(element)
        elif evebi_elem.element_type == 'Floor':
            envelope["floors"].append(element)
        elif evebi_elem.element_type == 'Window':
            envelope["windows"].append(element)
        elif evebi_elem.element_type == 'Door':
            envelope["doors"].append(element)
    
    return envelope


def _map_boundary_condition(evebi_condition: Optional[str]) -> str:
    """Mappt EVEBI Randbedingung zu DIN18599 Standard"""
    if not evebi_condition:
        return "EXTERNAL"
    
    condition_lower = evebi_condition.lower()
    
    if 'aussen' in condition_lower or 'außen' in condition_lower or 'luft' in condition_lower:
        return "EXTERNAL"
    elif 'erdreich' in condition_lower or 'boden' in condition_lower:
        return "GROUND"
    elif 'unbeheizt' in condition_lower:
        return "UNHEATED"
    else:
        return "INTERNAL"
