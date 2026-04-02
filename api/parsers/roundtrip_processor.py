"""
Roundtrip Processor - Unified IFC + EVEBI Parser und Merger

Kombiniert:
- IFC Parser v3.6 (ifc_parser_v3.py)
- EVEBI Parser v2 (evebi_parser.py)
- Roundtrip Merger (roundtrip_merger.py)

Workflow:
1. IFC → Sidecar Input (Geometrie)
2. EVEBI → Extrahierte Daten (Konstruktionen, Systeme)
3. Merge → Vollständiges Sidecar (Input komplett)
"""

import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


# ============================================================
# EVEBI Data Classes
# ============================================================

@dataclass
class EVEBIMaterial:
    """Material mit λ-Wert"""
    guid: str
    name: str
    lambda_value: float
    density: float = 0.0


@dataclass
class EVEBILayer:
    """Schicht in Konstruktion"""
    material_name: str
    thickness: float
    lambda_value: float
    position: int


@dataclass
class EVEBIConstruction:
    """Konstruktion (Schichtaufbau)"""
    guid: str
    name: str
    u_value: float
    layers: List[EVEBILayer] = field(default_factory=list)
    total_thickness: float = 0.0


@dataclass
class EVEBIElement:
    """Bauteil (Wand, Dach, etc.)"""
    guid: str
    name: str
    element_type: str
    area: Optional[float] = None
    orientation: Optional[float] = None
    inclination: Optional[float] = None
    u_value: Optional[float] = None
    construction_ref: Optional[str] = None
    boundary_condition: Optional[str] = None
    posno: Optional[str] = None


@dataclass
class EVEBIZone:
    """Thermische Zone"""
    guid: str
    name: str
    area: float = 0.0
    volume: float = 0.0
    heating_setpoint: Optional[float] = None
    cooling_setpoint: Optional[float] = None


@dataclass
class EVEBIData:
    """Vollständige EVEBI-Daten"""
    project_guid: str
    project_name: str
    materials: List[EVEBIMaterial] = field(default_factory=list)
    constructions: List[EVEBIConstruction] = field(default_factory=list)
    elements: List[EVEBIElement] = field(default_factory=list)
    zones: List[EVEBIZone] = field(default_factory=list)
    storeys: List[dict] = field(default_factory=list)
    heating_systems: List[dict] = field(default_factory=list)
    dhw_systems: List[dict] = field(default_factory=list)
    ventilation_systems: List[dict] = field(default_factory=list)
    pv_systems: List[dict] = field(default_factory=list)


# ============================================================
# EVEBI Parser
# ============================================================

def parse_evebi(evea_path: str) -> EVEBIData:
    """
    Parst EVEBI .evea Archiv (ZIP mit projekt.xml)
    """
    print(f"\n=== EVEBI Parser ===")
    print(f"📂 Datei: {evea_path}")
    
    # 1. ZIP entpacken
    extract_dir = Path('/tmp/evea_extract')
    extract_dir.mkdir(exist_ok=True)
    
    with zipfile.ZipFile(evea_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    # 2. projekt.xml parsen
    xml_path = extract_dir / 'projekt.xml'
    if not xml_path.exists():
        raise FileNotFoundError(f"projekt.xml nicht gefunden in {evea_path}")
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # 3. Projekt-Info
    project_guid = root.get('GUID', '')
    project_name = 'Unbekanntes Projekt'
    
    eing = root.find('eing')
    if eing is not None:
        we_liste = eing.find('weListe')
        if we_liste is not None:
            first_we = we_liste.find('item')
            if first_we is not None:
                name_elem = first_we.find('.//name')
                if name_elem is not None and name_elem.text:
                    project_name = name_elem.text
    
    print(f"📋 Projekt: {project_name}")
    
    # 4. Daten extrahieren
    materials = _extract_materials(eing) if eing is not None else []
    constructions = _extract_constructions(eing) if eing is not None else []
    elements = _extract_elements(eing) if eing is not None else []
    zones = _extract_zones(eing) if eing is not None else []
    storeys = _extract_storeys(eing) if eing is not None else []
    
    heating_systems = _extract_heating(eing) if eing is not None else []
    dhw_systems = _extract_dhw(eing) if eing is not None else []
    ventilation_systems = _extract_ventilation(eing) if eing is not None else []
    pv_systems = _extract_pv(eing) if eing is not None else []
    
    print(f"✅ Konstruktionen: {len(constructions)}")
    print(f"✅ Bauteile: {len(elements)}")
    print(f"✅ Zonen: {len(zones)}")
    print(f"✅ Systeme: {len(heating_systems + dhw_systems + ventilation_systems + pv_systems)}")
    
    return EVEBIData(
        project_guid=project_guid,
        project_name=project_name,
        materials=materials,
        constructions=constructions,
        elements=elements,
        zones=zones,
        storeys=storeys,
        heating_systems=heating_systems,
        dhw_systems=dhw_systems,
        ventilation_systems=ventilation_systems,
        pv_systems=pv_systems
    )


def _extract_materials(eing) -> List[EVEBIMaterial]:
    """Extrahiert Materialien aus EVEBI"""
    return []  # TODO: Implementieren


def _extract_constructions(eing) -> List[EVEBIConstruction]:
    """Extrahiert Konstruktionen aus EVEBI"""
    constructions = []
    
    konstr_liste = eing.find('konstruktionenListe')
    if konstr_liste is not None:
        for item in konstr_liste.findall('item'):
            guid = item.get('GUID', '')
            name_elem = item.find('name')
            name = name_elem.text if name_elem is not None and name_elem.text else 'Unbekannt'
            
            u_wert_elem = item.find('UWert')
            u_value = 0.0
            if u_wert_elem is not None and u_wert_elem.text:
                try:
                    u_value = float(u_wert_elem.text)
                except ValueError:
                    pass
            
            constructions.append(EVEBIConstruction(
                guid=guid,
                name=name,
                u_value=u_value,
                layers=[],
                total_thickness=0.0
            ))
    
    return constructions


def _extract_elements(eing) -> List[EVEBIElement]:
    """Extrahiert Bauteile aus EVEBI"""
    elements = []
    
    tfl_liste = eing.find('tflListe')
    if tfl_liste is not None:
        for item in tfl_liste.findall('item'):
            guid = item.get('GUID', '')
            name_elem = item.find('name')
            name = name_elem.text if name_elem is not None and name_elem.text else 'Unbekannt'
            
            elements.append(EVEBIElement(
                guid=guid,
                name=name,
                element_type='UNKNOWN'
            ))
    
    return elements


def _extract_zones(eing) -> List[EVEBIZone]:
    """Extrahiert Zonen aus EVEBI"""
    zones = []
    
    geschosse_liste = eing.find('geschosseListe')
    if geschosse_liste is not None:
        for item in geschosse_liste.findall('item'):
            guid = item.get('GUID', '')
            name_elem = item.find('name')
            name = name_elem.text if name_elem is not None and name_elem.text else 'Unbekannt'
            
            zones.append(EVEBIZone(
                guid=guid,
                name=name,
                area=0.0,
                volume=0.0
            ))
    
    return zones


def _extract_storeys(eing) -> List[dict]:
    """Extrahiert Geschosse aus EVEBI"""
    storeys = []
    
    geschosse_liste = eing.find('geschosseListe')
    if geschosse_liste is not None:
        for item in geschosse_liste.findall('item'):
            guid = item.get('GUID', '')
            name_elem = item.find('name')
            name = name_elem.text if name_elem is not None and name_elem.text else 'Unbekannt'
            
            storeys.append({
                'id': guid,
                'name': name,
                'elevation': None,
                'height': None
            })
    
    return storeys


def _extract_heating(eing) -> List[dict]:
    """Extrahiert Heizungssysteme aus EVEBI"""
    systems = []
    
    hz_erz_liste = eing.find('hzErzListe')
    if hz_erz_liste is not None:
        for item in hz_erz_liste.findall('item'):
            guid = item.get('GUID', '')
            name_elem = item.find('name')
            name = name_elem.text if name_elem is not None and name_elem.text else 'Unbekannt'
            
            art_elem = item.find('art')
            art = art_elem.text if art_elem is not None and art_elem.text else None
            
            systems.append({
                'guid': guid,
                'name': name,
                'art': art,
                'year_built': None
            })
    
    return systems


def _extract_dhw(eing) -> List[dict]:
    """Extrahiert Warmwassersysteme aus EVEBI"""
    systems = []
    
    tw_erz_liste = eing.find('twErzListe')
    if tw_erz_liste is not None:
        for item in tw_erz_liste.findall('item'):
            guid = item.get('GUID', '')
            name_elem = item.find('name')
            name = name_elem.text if name_elem is not None and name_elem.text else 'Unbekannt'
            
            art_elem = item.find('art')
            art = art_elem.text if art_elem is not None and art_elem.text else None
            
            systems.append({
                'guid': guid,
                'name': name,
                'art': art,
                'storage_volume': None,
                'circulation': None
            })
    
    return systems


def _extract_ventilation(eing) -> List[dict]:
    """Extrahiert Lüftungssysteme aus EVEBI"""
    systems = []
    
    luft_liste = eing.find('luftListe')
    if luft_liste is not None:
        for item in luft_liste.findall('item'):
            guid = item.get('GUID', '')
            name_elem = item.find('name')
            name = name_elem.text if name_elem is not None and name_elem.text else 'Unbekannt'
            
            art_elem = item.find('art')
            art = art_elem.text if art_elem is not None and art_elem.text else None
            
            systems.append({
                'guid': guid,
                'name': name,
                'art': art,
                'wrg': None,
                'wrg_grad': None
            })
    
    return systems


def _extract_pv(eing) -> List[dict]:
    """Extrahiert PV-Systeme aus EVEBI"""
    systems = []
    
    pv_liste = eing.find('pvListe')
    if pv_liste is not None:
        for item in pv_liste.findall('item'):
            guid = item.get('GUID', '')
            name_elem = item.find('name')
            name = name_elem.text if name_elem is not None and name_elem.text else 'Unbekannt'
            
            systems.append({
                'guid': guid,
                'name': name,
                'peak_power': None,
                'orientation': None,
                'inclination': None
            })
    
    return systems


# ============================================================
# Roundtrip Processor
# ============================================================

def process_roundtrip(ifc_path: str, evea_path: str, output_path: str = 'output_roundtrip.json') -> Dict[str, Any]:
    """
    Vollständiger Roundtrip: IFC + EVEBI → Sidecar
    
    Args:
        ifc_path: Pfad zur IFC-Datei
        evea_path: Pfad zur EVEBI-Datei (.evea)
        output_path: Pfad für Output-JSON
    
    Returns:
        Vollständiges Sidecar JSON
    """
    import sys
    sys.path.insert(0, '/opt/din18599-ifc')
    
    print('=' * 70)
    print('ROUNDTRIP PROCESSOR - IFC + EVEBI → SIDECAR')
    print('=' * 70)
    print()
    
    # 1. IFC parsen
    print('STEP 1: IFC PARSEN')
    print('-' * 70)
    from api.parsers.ifc_parser_v3 import parse_ifc_file
    
    sidecar = parse_ifc_file(ifc_path)
    
    print(f'✅ IFC geparst')
    print(f'   Wände: {len(sidecar["input"]["envelope"]["walls"])}')
    print(f'   Dächer: {len(sidecar["input"]["envelope"]["roofs"])}')
    print(f'   Räume: {len(sidecar["input"]["building"]["rooms"])}')
    print()
    
    # 2. EVEBI parsen
    print('STEP 2: EVEBI PARSEN')
    print('-' * 70)
    
    evebi_data = parse_evebi(evea_path)
    print()
    
    # 3. Merge
    print('STEP 3: MERGE')
    print('-' * 70)
    
    # Konstruktionen
    constructions = []
    for konstr in evebi_data.constructions:
        constructions.append({
            'id': konstr.guid,
            'name': konstr.name,
            'source': 'EVEBI',
            'u_value': round(konstr.u_value, 3) if konstr.u_value else None,
            'sequences': [],
            'total_thickness': konstr.total_thickness
        })
    
    sidecar['input']['constructions'] = constructions
    print(f'✅ {len(constructions)} Konstruktionen')
    
    # Systeme
    if 'systems' not in sidecar['input']:
        sidecar['input']['systems'] = {}
    
    sidecar['input']['systems']['heating'] = evebi_data.heating_systems
    sidecar['input']['systems']['dhw'] = evebi_data.dhw_systems
    sidecar['input']['systems']['ventilation'] = evebi_data.ventilation_systems
    sidecar['input']['systems']['pv'] = evebi_data.pv_systems
    
    systems_count = (len(evebi_data.heating_systems) + len(evebi_data.dhw_systems) + 
                     len(evebi_data.ventilation_systems) + len(evebi_data.pv_systems))
    print(f'✅ {systems_count} Systeme')
    
    # Geschosse
    if evebi_data.storeys:
        sidecar['input']['building']['storeys'] = evebi_data.storeys
        print(f'✅ {len(evebi_data.storeys)} Geschosse')
    
    print()
    
    # 4. Speichern
    print('STEP 4: SPEICHERN')
    print('-' * 70)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sidecar, f, indent=2, ensure_ascii=False)
    
    file_size = len(json.dumps(sidecar, indent=2, ensure_ascii=False))
    print(f'✅ Gespeichert: {output_path} ({file_size/1024:.1f} KB)')
    print()
    
    print('=' * 70)
    print('ROUNDTRIP ERFOLGREICH ✅')
    print('=' * 70)
    
    return sidecar


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print('Usage: python roundtrip_processor.py <ifc_file> <evea_file> [output_file]')
        sys.exit(1)
    
    ifc_path = sys.argv[1]
    evea_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else 'output_roundtrip.json'
    
    result = process_roundtrip(ifc_path, evea_path, output_path)
    
    print()
    print('ZUSAMMENFASSUNG:')
    print(f'  IFC: {len(result["input"]["envelope"]["walls"])} Wände, '
          f'{len(result["input"]["building"]["rooms"])} Räume')
    print(f'  EVEBI: {len(result["input"]["constructions"])} Konstruktionen, '
          f'{len(result["input"]["systems"].get("heating", []))} Heizung')
