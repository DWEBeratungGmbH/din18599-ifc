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
    """Extrahiert Materialien aus konstruktionenListe"""
    materials = []
    
    konstr_liste = eing.find('konstruktionenListe')
    if konstr_liste is None:
        return materials
    
    for item in konstr_liste:
        guid = item.get('GUID', '')
        name = item.findtext('.//name', 'Unbekannt')
        
        # Lambda-Wert
        lambda_elem = item.find('.//lambda')
        lambda_value = 0.0
        if lambda_elem is not None:
            try:
                lambda_value = float(lambda_elem.get('man', lambda_elem.get('calc', '0')))
            except (ValueError, TypeError):
                lambda_value = 0.0
        
        # Dichte
        density_elem = item.find('.//rho')
        density = 0.0
        if density_elem is not None:
            try:
                density = float(density_elem.get('man', density_elem.get('calc', '0')))
            except (ValueError, TypeError):
                density = 0.0
        
        if lambda_value > 0:
            materials.append(EVEBIMaterial(
                guid=guid,
                name=name,
                lambda_value=lambda_value,
                density=density
            ))
    
    return materials


def _extract_constructions(eing) -> List[EVEBIConstruction]:
    """Extrahiert Konstruktionen mit Schichten aus EVEBI"""
    constructions = []
    
    konstr_liste = eing.find('konstruktionenListe')
    if konstr_liste is None:
        return constructions
    
    for item in konstr_liste.findall('item'):
        guid = item.get('GUID', '')
        
        # Name aus Attribut 'man'
        name_elem = item.find('name')
        name = 'Unbekannte Konstruktion'
        if name_elem is not None:
            name = name_elem.get('man', name_elem.get('calc', name_elem.text or name))
        
        # U-Wert
        u_value = 0.0
        u_standard = item.findtext('UWertStandard')
        if u_standard:
            try:
                u_value = float(u_standard)
            except (ValueError, TypeError):
                pass
        
        if u_value == 0.0:
            u_elem = item.find('U')
            if u_elem is not None:
                try:
                    u_value = float(u_elem.get('man', u_elem.get('calc', '0')))
                except (ValueError, TypeError):
                    pass
        
        # Schichten aus abfolgenListe → schichtenListe
        layers = []
        total_thickness = 0.0
        
        abfolgen_liste = item.find('abfolgenListe')
        if abfolgen_liste is not None:
            for abfolge in abfolgen_liste.findall('item'):
                schichten_liste = abfolge.find('schichtenListe')
                if schichten_liste is not None:
                    for pos, schicht in enumerate(schichten_liste.findall('item')):
                        mat_name = schicht.findtext('material', 'Unbekannt')
                        
                        # Dicke in cm → m (Wert ist in text, nicht in Attributen!)
                        dicke_elem = schicht.find('dicke')
                        thickness = 0.0
                        if dicke_elem is not None:
                            try:
                                # Versuche zuerst Attribute, dann text
                                val = dicke_elem.get('man') or dicke_elem.get('calc') or dicke_elem.text
                                if val:
                                    thickness = float(val) / 100.0
                            except (ValueError, TypeError):
                                thickness = 0.0
                        
                        # Lambda (Wert ist in text, nicht in Attributen!)
                        lambda_elem = schicht.find('lambda')
                        lambda_val = 0.0
                        if lambda_elem is not None:
                            try:
                                # Versuche zuerst Attribute, dann text
                                val = lambda_elem.get('man') or lambda_elem.get('calc') or lambda_elem.text
                                if val:
                                    lambda_val = float(val)
                            except (ValueError, TypeError):
                                lambda_val = 0.0
                        
                        if thickness > 0:
                            layers.append(EVEBILayer(
                                material_name=mat_name,
                                thickness=thickness,
                                lambda_value=lambda_val,
                                position=pos
                            ))
                            total_thickness += thickness
        
        constructions.append(EVEBIConstruction(
            guid=guid,
            name=name,
            u_value=u_value,
            layers=layers,
            total_thickness=total_thickness
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
    """Extrahiert Zonen aus zDListe (nicht geschosseListe!)"""
    zones = []
    
    # zDListe enthält die echten DIN 18599 Zonen mit flaeche, V, raumHoehe, iTmp
    zd_liste = eing.find('zDListe')
    if zd_liste is not None:
        for item in zd_liste.findall('item'):
            guid = item.get('GUID', '')
            name_elem = item.find('name')
            name = name_elem.text if name_elem is not None and name_elem.text else 'Unbekannte Zone'
            
            # Fläche
            area = 0.0
            flaeche_elem = item.find('flaeche')
            if flaeche_elem is not None:
                try:
                    area = float(flaeche_elem.get('man', flaeche_elem.get('calc', '0')))
                except (ValueError, TypeError):
                    area = 0.0
            
            # Volumen
            volume = 0.0
            v_elem = item.find('V')
            if v_elem is not None:
                try:
                    volume = float(v_elem.get('man', v_elem.get('calc', '0')))
                except (ValueError, TypeError):
                    volume = 0.0
            
            # Solltemperatur
            heating_setpoint = None
            i_tmp_elem = item.find('iTmp')
            if i_tmp_elem is not None:
                try:
                    heating_setpoint = float(i_tmp_elem.get('man', i_tmp_elem.get('calc', '20')))
                except (ValueError, TypeError):
                    heating_setpoint = None
            
            zones.append(EVEBIZone(
                guid=guid,
                name=name,
                area=area,
                volume=volume,
                heating_setpoint=heating_setpoint
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
            
            # Speichervolumen
            storage_volume = None
            v_sp_elem = item.find('V_Sp')
            if v_sp_elem is not None:
                try:
                    storage_volume = float(v_sp_elem.get('man', v_sp_elem.get('calc', '0')))
                except (ValueError, TypeError):
                    storage_volume = None
            
            # Zirkulation
            circulation = None
            zirk_elem = item.find('zirkulation')
            if zirk_elem is not None:
                circulation = zirk_elem.text == 'true' or zirk_elem.get('man') == 'true'
            
            systems.append({
                'guid': guid,
                'name': name,
                'art': art,
                'storage_volume': storage_volume,
                'circulation': circulation
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
            
            # Wärmerückgewinnung
            wrg = None
            wrg_elem = item.find('wrg')
            if wrg_elem is not None:
                wrg = wrg_elem.text == 'true' or wrg_elem.get('man') == 'true'
            
            # WRG-Grad
            wrg_grad = None
            wrg_grad_elem = item.find('wrg_grad')
            if wrg_grad_elem is not None:
                try:
                    wrg_grad = float(wrg_grad_elem.get('man', wrg_grad_elem.get('calc', '0')))
                except (ValueError, TypeError):
                    wrg_grad = None
            
            systems.append({
                'guid': guid,
                'name': name,
                'art': art,
                'wrg': wrg,
                'wrg_grad': wrg_grad
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
            
            # Nennleistung (lstPeak in kWp) - Wert ist in text!
            peak_power = None
            lst_peak_elem = item.find('lstPeak')
            if lst_peak_elem is not None:
                try:
                    val = lst_peak_elem.get('man') or lst_peak_elem.get('calc') or lst_peak_elem.text
                    if val:
                        peak_power = float(val)
                except (ValueError, TypeError):
                    peak_power = None
            
            # Orientierung (orientierung_genau, nicht orientGrad!)
            orientation = None
            orient_elem = item.find('orientierung_genau')
            if orient_elem is not None:
                try:
                    val = orient_elem.get('man') or orient_elem.get('calc') or orient_elem.text
                    if val:
                        orientation = float(val)
                except (ValueError, TypeError):
                    orientation = None
            
            # Neigung - Wert ist in text!
            inclination = None
            neig_elem = item.find('neigung')
            if neig_elem is not None:
                try:
                    val = neig_elem.get('man') or neig_elem.get('calc') or neig_elem.text
                    if val:
                        inclination = float(val)
                except (ValueError, TypeError):
                    inclination = None
            
            # Fläche - Wert ist in text!
            area = None
            flaeche_elem = item.find('flaeche')
            if flaeche_elem is not None:
                try:
                    val = flaeche_elem.get('man') or flaeche_elem.get('calc') or flaeche_elem.text
                    if val:
                        area = float(val)
                except (ValueError, TypeError):
                    area = None
            
            systems.append({
                'guid': guid,
                'name': name,
                'peak_power': peak_power,
                'orientation': orientation,
                'inclination': inclination,
                'area': area
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
    
    # Konstruktionen mit Schichten
    constructions = []
    for konstr in evebi_data.constructions:
        # Schichten in sequences[] Format konvertieren
        sequences = []
        if konstr.layers:
            sequences.append({
                'share': 1.0,
                'name': 'Hauptkonstruktion',
                'layers': [
                    {
                        'material': layer.material_name,
                        'thickness': layer.thickness,
                        'lambda': layer.lambda_value,
                        'position': layer.position
                    }
                    for layer in konstr.layers
                ]
            })
        
        constructions.append({
            'id': konstr.guid,
            'name': konstr.name,
            'source': 'EVEBI',
            'u_value': round(konstr.u_value, 3) if konstr.u_value else None,
            'sequences': sequences,
            'total_thickness': konstr.total_thickness
        })
    
    sidecar['input']['constructions'] = constructions
    print(f'✅ {len(constructions)} Konstruktionen')
    
    # U-Wert-Merge: EVEBI → IFC Bauteile
    # Erstelle GUID → U-Wert Mapping aus EVEBI-Elementen
    evebi_u_values = {}
    for elem in evebi_data.elements:
        if elem.u_value is not None and elem.u_value > 0:
            evebi_u_values[elem.guid] = elem.u_value
    
    # Ergänze U-Werte in IFC-Bauteilen (via sourceID-Brücke)
    u_value_count = 0
    for wall in sidecar['input']['envelope']['walls']:
        if wall['u_value'] == 0.0 and wall['id'] in evebi_u_values:
            wall['u_value'] = round(evebi_u_values[wall['id']], 3)
            u_value_count += 1
    
    for roof in sidecar['input']['envelope']['roofs']:
        if roof['u_value'] == 0.0 and roof['id'] in evebi_u_values:
            roof['u_value'] = round(evebi_u_values[roof['id']], 3)
            u_value_count += 1
    
    for floor in sidecar['input']['envelope']['floors']:
        if floor['u_value'] == 0.0 and floor['id'] in evebi_u_values:
            floor['u_value'] = round(evebi_u_values[floor['id']], 3)
            u_value_count += 1
    
    if u_value_count > 0:
        print(f'✅ {u_value_count} U-Werte ergänzt (EVEBI → IFC)')
    
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
