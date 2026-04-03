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
    sequences: List[dict] = None  # Getrennte Abfolgen für inhomogene Schichten


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
    window_constructions: List[dict] = field(default_factory=list)
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
    window_constructions = _extract_window_constructions(eing) if eing is not None else []
    elements = _extract_elements(eing) if eing is not None else []
    zones = _extract_zones(eing) if eing is not None else []
    storeys = _extract_storeys(eing) if eing is not None else []
    
    heating_systems = _extract_heating(eing) if eing is not None else []
    dhw_systems = _extract_dhw(eing) if eing is not None else []
    ventilation_systems = _extract_ventilation(eing) if eing is not None else []
    pv_systems = _extract_pv(eing) if eing is not None else []
    
    print(f"✅ Konstruktionen: {len(constructions)}")
    print(f"✅ Fenster-Konstruktionen: {len(window_constructions)}")
    print(f"✅ Bauteile: {len(elements)}")
    print(f"✅ Zonen: {len(zones)}")
    print(f"✅ Systeme: {len(heating_systems + dhw_systems + ventilation_systems + pv_systems)}")
    
    return EVEBIData(
        project_guid=project_guid,
        project_name=project_name,
        materials=materials,
        constructions=constructions,
        window_constructions=window_constructions,
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
    """Extrahiert Konstruktionen aus EVEBI mit getrennten Abfolgen (inhomogene Schichten)"""
    constructions = []
    
    konstr_liste = eing.find('konstruktionenListe')
    if konstr_liste is not None:
        for item in konstr_liste.findall('item'):
            guid = item.get('GUID', '')
            name_elem = item.find('name')
            name = name_elem.get('man', name_elem.get('calc', name_elem.text or 'Unbekannt')) if name_elem is not None else 'Unbekannt'
            
            u_standard = item.findtext('UWertStandard')
            u_value = 0.0
            if u_standard:
                try:
                    u_value = float(u_standard)
                except (ValueError, TypeError):
                    pass
            
            # Schichten aus abfolgenListe → schichtenListe
            # WICHTIG: Jede Abfolge getrennt halten für inhomogene Schichten (85% Dämmung + 15% Sparren)
            sequences = []  # Liste von Abfolgen mit anteil
            total_thickness = 0.0
            
            abfolgen_liste = item.find('abfolgenListe')
            if abfolgen_liste is not None:
                for abfolge in abfolgen_liste.findall('item'):
                    # Anteil der Abfolge (z.B. 0.85 für Hauptkonstruktion)
                    anteil_elem = abfolge.find('anteil')
                    anteil = 1.0
                    if anteil_elem is not None and anteil_elem.text:
                        try:
                            anteil = float(anteil_elem.text)
                        except (ValueError, TypeError):
                            anteil = 1.0
                    
                    # Schichten dieser Abfolge
                    layers = []
                    schichten_liste = abfolge.find('schichtenListe')
                    if schichten_liste is not None:
                        for pos, schicht in enumerate(schichten_liste.findall('item')):
                            # Material-Name ist in 'name' Tag, nicht 'material'!
                            mat_name = schicht.findtext('name', 'Unbekannt')
                            
                            # Dicke in cm → m (Wert ist in text!)
                            dicke_elem = schicht.find('dicke')
                            thickness = 0.0
                            if dicke_elem is not None and dicke_elem.text:
                                try:
                                    thickness = float(dicke_elem.text) / 100.0
                                except (ValueError, TypeError):
                                    thickness = 0.0
                            
                            # Lambda (Wert ist in text!)
                            lambda_elem = schicht.find('lambda')
                            lambda_val = 0.0
                            if lambda_elem is not None and lambda_elem.text:
                                try:
                                    lambda_val = float(lambda_elem.text)
                                except (ValueError, TypeError):
                                    lambda_val = 0.0
                            
                            if thickness > 0:
                                layers.append(EVEBILayer(
                                    material_name=mat_name,
                                    thickness=thickness,
                                    lambda_value=lambda_val,
                                    position=pos
                                ))
                    
                    if layers:
                        sequences.append({
                            'share': anteil,
                            'layers': layers
                        })
                        # Total thickness nur von erster Abfolge (alle haben gleiche Dicke)
                        if not total_thickness:
                            total_thickness = sum(layer.thickness for layer in layers)
            
            # Für Rückwärtskompatibilität: layers = erste Abfolge
            layers = sequences[0]['layers'] if sequences else []
            
            constructions.append(EVEBIConstruction(
                guid=guid,
                name=name,
                u_value=u_value,
                layers=layers,
                total_thickness=total_thickness,
                sequences=sequences  # Neue Eigenschaft für getrennte Abfolgen
            ))
    
    return constructions


def _extract_elements(eing) -> List[EVEBIElement]:
    """Extrahiert Bauteile aus tflListe (Teilflächen)"""
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


def _extract_btl_elements(eing) -> List[dict]:
    """Extrahiert Bauteile aus btlListe (hat Konstruktion-Referenz!)"""
    btl_elements = []
    
    # Erstelle Konstruktions-GUID → U-Wert Mapping
    konstr_map = {}
    konstr_liste = eing.find('konstruktionenListe')
    if konstr_liste is not None:
        for k in konstr_liste.findall('item'):
            guid = k.get('GUID', '')
            name_elem = k.find('name')
            name = name_elem.get('man', name_elem.get('calc', name_elem.text or 'Unbekannt')) if name_elem is not None else 'Unbekannt'
            
            u_standard = k.findtext('UWertStandard')
            u_value = 0.0
            if u_standard:
                try:
                    u_value = float(u_standard)
                except (ValueError, TypeError):
                    pass
            
            konstr_map[guid] = {'name': name, 'u_value': u_value}
    
    # Extrahiere btlListe mit Konstruktion-Referenz
    btl_liste = eing.find('btlListe')
    if btl_liste is not None:
        for item in btl_liste.findall('item'):
            guid = item.get('GUID', '')
            name = item.findtext('name', 'Unbekannt')
            
            # Konstruktion-Referenz
            konstr_guid = None
            u_value = None
            konstr_name = None
            
            konstr_elem = item.find('konstruktion')
            if konstr_elem is not None:
                konstr_guid = konstr_elem.get('GUID', '')
                if konstr_guid in konstr_map:
                    konstr_data = konstr_map[konstr_guid]
                    u_value = konstr_data['u_value']
                    konstr_name = konstr_data['name']
            
            btl_elements.append({
                'guid': guid,
                'name': name,
                'konstruktion_guid': konstr_guid,
                'konstruktion_name': konstr_name,
                'u_value': u_value
            })
    
    return btl_elements


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
    """Extrahiert Heizungssysteme aus EVEBI mit Detailfeldern"""
    systems = []
    
    hz_liste = eing.find('hzListe')
    if hz_liste is not None:
        for item in hz_liste.findall('item'):
            guid = item.get('GUID', '')
            name_elem = item.find('name')
            name = name_elem.text if name_elem is not None and name_elem.text else 'Unbekannt'
            
            # Netztyp
            netz_typ = item.findtext('netzTyp', None)
            
            # Deckung
            deckung = None
            deckung_elem = item.find('deckung')
            if deckung_elem is not None and deckung_elem.text:
                try:
                    deckung = float(deckung_elem.text)
                except (ValueError, TypeError):
                    pass
            
            # Baujahr
            baujahr = None
            bj_elem = item.find('baujahr')
            if bj_elem is not None and bj_elem.text:
                try:
                    baujahr = int(bj_elem.text)
                except (ValueError, TypeError):
                    pass
            
            systems.append({
                'guid': guid,
                'name': name,
                'netz_typ': netz_typ,
                'deckung': deckung,
                'baujahr': baujahr
            })
    
    return systems


def _extract_dhw(eing) -> List[dict]:
    """Extrahiert Warmwassersysteme aus EVEBI mit Detailfeldern"""
    systems = []
    
    tw_liste = eing.find('twListe')
    if tw_liste is not None:
        for item in tw_liste.findall('item'):
            guid = item.get('GUID', '')
            name_elem = item.find('name')
            name = name_elem.text if name_elem is not None and name_elem.text else 'Unbekannt'
            
            # Netztyp
            netz_typ = item.findtext('netzTyp', None)
            
            # Deckung
            deckung = None
            deckung_elem = item.find('deckung')
            if deckung_elem is not None and deckung_elem.text:
                try:
                    deckung = float(deckung_elem.text)
                except (ValueError, TypeError):
                    pass
            
            # Temperatur
            temperatur = None
            temp_elem = item.find('temperatur')
            if temp_elem is not None and temp_elem.text:
                try:
                    temperatur = float(temp_elem.text)
                except (ValueError, TypeError):
                    pass
            
            # Zapfstellen
            zapfstellen = None
            zapf_elem = item.find('zapfstellen')
            if zapf_elem is not None and zapf_elem.text:
                try:
                    zapfstellen = int(float(zapf_elem.text))
                except (ValueError, TypeError):
                    pass
            
            systems.append({
                'guid': guid,
                'name': name,
                'netz_typ': netz_typ,
                'deckung': deckung,
                'temperatur': temperatur,
                'zapfstellen': zapfstellen
            })
    
    return systems


def _extract_ventilation(eing) -> List[dict]:
    """Extrahiert Lüftungssysteme aus EVEBI mit wrg_grad als float"""
    systems = []
    
    luft_liste = eing.find('luftListe')
    if luft_liste is not None:
        for item in luft_liste.findall('item'):
            guid = item.get('GUID', '')
            name_elem = item.find('name')
            name = name_elem.text if name_elem is not None and name_elem.text else 'Unbekannt'
            
            # Art (LA_FREI = Fensterlüftung, LA_ZENTRAL = zentrale RLT, etc.)
            art_elem = item.find('art')
            art = art_elem.text if art_elem is not None and art_elem.text else None
            
            # WRG (Wärmerückgewinnung) - als float (0.0 = keine WRG)
            wrg_grad = None
            wrg_elem = item.find('wrg')
            if wrg_elem is not None and wrg_elem.text:
                try:
                    wrg_grad = float(wrg_elem.text)
                except (ValueError, TypeError):
                    wrg_grad = None
            
            # Anzahl
            anzahl = None
            anzahl_elem = item.find('anzahl')
            if anzahl_elem is not None and anzahl_elem.text:
                try:
                    anzahl = int(float(anzahl_elem.text))
                except (ValueError, TypeError):
                    pass
            
            systems.append({
                'guid': guid,
                'name': name,
                'art': art,
                'wrg_grad': wrg_grad,
                'anzahl': anzahl
            })
    
    return systems


def _extract_window_constructions(eing) -> List[dict]:
    """Extrahiert Fenster-Konstruktionen aus EVEBI"""
    window_constructions = []
    
    konstr_fenster_liste = eing.find('konstrFensterListe')
    if konstr_fenster_liste is not None:
        for item in konstr_fenster_liste.findall('item'):
            guid = item.get('GUID', '')
            name = item.findtext('name', 'Unbekannt')
            
            # g-Wert (Gesamtenergiedurchlassgrad)
            g_wert = None
            g_elem = item.find('gWert')
            if g_elem is not None and g_elem.text:
                try:
                    g_wert = float(g_elem.text)
                except (ValueError, TypeError):
                    pass
            
            # Ug (U-Wert Verglasung)
            ug = None
            ug_elem = item.find('glas_Ug')
            if ug_elem is not None and ug_elem.text:
                try:
                    ug = float(ug_elem.text)
                except (ValueError, TypeError):
                    pass
            
            # Uf (U-Wert Rahmen)
            uf = None
            uf_elem = item.find('rahmen_Uf')
            if uf_elem is not None and uf_elem.text:
                try:
                    uf = float(uf_elem.text)
                except (ValueError, TypeError):
                    pass
            
            # Rahmenanteil
            frame_area_fraction = None
            rahmen_elem = item.find('rahmenAnteilWin')
            if rahmen_elem is not None and rahmen_elem.text:
                try:
                    frame_area_fraction = float(rahmen_elem.text)
                except (ValueError, TypeError):
                    pass
            
            # U-Wert gesamt
            u_value = None
            u_standard_elem = item.find('UWertStandard')
            if u_standard_elem is not None and u_standard_elem.text:
                try:
                    u_value = float(u_standard_elem.text)
                except (ValueError, TypeError):
                    pass
            
            window_constructions.append({
                'guid': guid,
                'name': name,
                'g_value': g_wert,
                'ug': ug,
                'uf': uf,
                'frame_area_fraction': frame_area_fraction,
                'u_value': u_value
            })
    
    return window_constructions


def _extract_pv(eing) -> List[dict]:
    """Extrahiert PV-Systeme aus EVEBI"""
    systems = []
    
    pv_liste = eing.find('pvListe')
    if pv_liste is not None:
        for item in pv_liste.findall('item'):
            guid = item.get('GUID', '')
            name_elem = item.find('name')
            name = name_elem.text if name_elem is not None and name_elem.text else 'Unbekannt'
            
            # Nennleistung (lstPeak in kWp) - Wert ist direkt im text!
            peak_power = None
            lst_peak_elem = item.find('lstPeak')
            if lst_peak_elem is not None and lst_peak_elem.text:
                try:
                    peak_power = float(lst_peak_elem.text)
                except (ValueError, TypeError):
                    peak_power = None
            
            # Orientierung (orientierung_genau) - Wert ist direkt im text!
            orientation = None
            orient_elem = item.find('orientierung_genau')
            if orient_elem is not None and orient_elem.text:
                try:
                    orientation = float(orient_elem.text)
                except (ValueError, TypeError):
                    orientation = None
            
            # Neigung - Wert ist direkt im text!
            inclination = None
            neig_elem = item.find('neigung')
            if neig_elem is not None and neig_elem.text:
                try:
                    inclination = float(neig_elem.text)
                except (ValueError, TypeError):
                    inclination = None
            
            # Fläche - Wert ist direkt im text!
            area = None
            flaeche_elem = item.find('flaeche')
            if flaeche_elem is not None and flaeche_elem.text:
                try:
                    area = float(flaeche_elem.text)
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
    
    # Extrahiere btlListe separat (für U-Wert-Merge)
    import zipfile
    import xml.etree.ElementTree as ET
    from pathlib import Path
    
    extract_dir = Path('/tmp/evea_extract')
    with zipfile.ZipFile(evea_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    xml_path = extract_dir / 'projekt.xml'
    tree = ET.parse(xml_path)
    root = tree.getroot()
    eing = root.find('eing')
    
    btl_elements = _extract_btl_elements(eing) if eing is not None else []
    print()
    
    # 3. Merge
    print('STEP 3: MERGE')
    print('-' * 70)
    
    # Konstruktionen mit Schichten
    # WICHTIG: Haupt-/Nebenkonstruktion getrennt halten für DIN 18599 U-Wert-Berechnung
    constructions = []
    for konstr in evebi_data.constructions:
        # Schichten in sequences[] Format konvertieren
        # Jede Abfolge (85% Dämmung + 15% Sparren) wird als separate Sequenz abgebildet
        sequences = []
        
        if konstr.sequences:
            # Nutze getrennte Abfolgen aus EVEBI (inhomogene Schichten)
            for i, seq in enumerate(konstr.sequences):
                seq_name = 'Hauptkonstruktion' if i == 0 else f'Nebenkonstruktion {i}'
                sequences.append({
                    'share': seq['share'],
                    'name': seq_name,
                    'layers': [
                        {
                            'material': layer.material_name,
                            'thickness': layer.thickness,
                            'lambda': layer.lambda_value,
                            'position': layer.position
                        }
                        for layer in seq['layers']
                    ]
                })
        elif konstr.layers:
            # Fallback: Alle Schichten in einer Sequenz (alte Logik)
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
    
    # Fenster-Konstruktionen
    # Fenster-Konstruktionen im Schema-Format (nested objects)
    window_constructions = []
    for wc in evebi_data.window_constructions:
        window_constructions.append({
            'id': wc['guid'],
            'name': wc['name'],
            'source': 'EVEBI',
            'u_value': round(wc['u_value'], 3) if wc['u_value'] else None,
            'g_value': round(wc['g_value'], 3) if wc['g_value'] else None,
            'glass': {
                'u_value': round(wc['ug'], 3) if wc['ug'] else None,
                'g_value': round(wc['g_value'], 3) if wc['g_value'] else None
            },
            'frame': {
                'u_value': round(wc['uf'], 3) if wc['uf'] else None,
                'area_fraction': round(wc['frame_area_fraction'], 3) if wc['frame_area_fraction'] else None
            }
        })
    
    sidecar['input']['window_constructions'] = window_constructions
    print(f'✅ {len(window_constructions)} Fenster-Konstruktionen')
    
    # U-Wert-Merge: EVEBI → IFC Bauteile
    # Problem: btlListe hat keine Flächen/Orientierungen, Name-Matching funktioniert nicht
    # Lösung: DIN-Code-Mapping (WA→Außenwand, DA→Dach, etc.)
    
    # Erstelle DIN-Code → Konstruktion Mapping
    din_to_konstr = {}
    for konstr in evebi_data.constructions:
        if not konstr.u_value or konstr.u_value <= 0:
            continue
        name_lower = konstr.name.lower()
        
        # Wände
        if 'außenwand' in name_lower or 'aussenwand' in name_lower:
            din_to_konstr['WA'] = konstr
        elif 'zwischenwand' in name_lower:
            din_to_konstr['WZ'] = konstr
        
        # Dächer (priorisiere "Dach" ohne "Decke")
        if 'dach' in name_lower:
            if 'decke' not in name_lower:
                din_to_konstr['DA'] = konstr  # "Dach"
            elif 'DA' not in din_to_konstr:
                din_to_konstr['DA'] = konstr  # Fallback: "Decke zu Dachraum"
        
        # Decken/Böden
        if 'zwischendecke' in name_lower:
            din_to_konstr['BZ'] = konstr  # BZ = Boden/Decke zu unbeheiztem Raum
            din_to_konstr['DE'] = konstr  # DE = Decke
        elif 'boden' in name_lower and 'außen' in name_lower:
            din_to_konstr['BE'] = konstr  # BE = Boden nach außen
            din_to_konstr['BO'] = konstr  # BO = Boden
    
    # Ergänze U-Werte in IFC-Bauteilen via DIN-Code
    u_value_count = 0
    
    for wall in sidecar['input']['envelope']['walls']:
        if wall['u_value'] == 0.0:
            din_code = wall.get('din_code', '')
            if din_code in din_to_konstr:
                konstr = din_to_konstr[din_code]
                wall['u_value'] = round(konstr.u_value, 3)
                wall['construction_ref'] = konstr.guid
                u_value_count += 1
    
    for roof in sidecar['input']['envelope']['roofs']:
        if not roof.get('u_value') or roof['u_value'] == 0.0:
            # Dächer haben meist keinen din_code, nutze DA als Default
            if 'DA' in din_to_konstr:
                konstr = din_to_konstr['DA']
                roof['u_value'] = round(konstr.u_value, 3)
                roof['construction_ref'] = konstr.guid
                u_value_count += 1
    
    for floor in sidecar['input']['envelope']['floors']:
        if not floor.get('u_value') or floor['u_value'] == 0.0:
            # Nutze din_code falls vorhanden
            din_code = floor.get('din_code', 'DE')
            if din_code in din_to_konstr:
                konstr = din_to_konstr[din_code]
                floor['u_value'] = round(konstr.u_value, 3)
                floor['construction_ref'] = konstr.guid
                u_value_count += 1
    
    if u_value_count > 0:
        print(f'✅ {u_value_count} U-Werte ergänzt (EVEBI → IFC via DIN-Code)')
    
    # Fenster/Türen U-Werte (transparent elements)
    # Nutze erste Fenster-Konstruktion für alle Fenster, erste Tür-Konstruktion für alle Türen
    fenster_konstr = None
    tuer_konstr = None
    
    for wc in evebi_data.window_constructions:
        if 'fenster' in wc['name'].lower() and not fenster_konstr:
            fenster_konstr = wc
        elif 'tür' in wc['name'].lower() or 'tuer' in wc['name'].lower():
            tuer_konstr = wc
    
    window_u_count = 0
    door_u_count = 0
    
    # Fenster
    for window in sidecar['input']['envelope']['windows']:
        if not window.get('u_value') or window['u_value'] == 0.0:
            if fenster_konstr and fenster_konstr['u_value']:
                window['u_value'] = round(fenster_konstr['u_value'], 3)
                window['construction_ref'] = fenster_konstr['guid']
                if fenster_konstr['g_value']:
                    window['g_value'] = round(fenster_konstr['g_value'], 3)
                window_u_count += 1
    
    # Türen
    for door in sidecar['input']['envelope']['doors']:
        if not door.get('u_value') or door['u_value'] == 0.0:
            if tuer_konstr and tuer_konstr['u_value']:
                door['u_value'] = round(tuer_konstr['u_value'], 3)
                door['construction_ref'] = tuer_konstr['guid']
                door_u_count += 1
            elif fenster_konstr and fenster_konstr['u_value']:
                # Fallback: Nutze Fenster-Konstruktion für Türen
                door['u_value'] = round(fenster_konstr['u_value'], 3)
                door['construction_ref'] = fenster_konstr['guid']
                door_u_count += 1
    
    if window_u_count > 0 or door_u_count > 0:
        print(f'✅ {window_u_count} Fenster + {door_u_count} Türen mit U-Werten ergänzt')
    
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
    
    # Zonen (FEHLTE!)
    if evebi_data.zones:
        sidecar['input']['building']['zones'] = [
            {
                'id': z.guid,
                'name': z.name,
                'area': z.area,
                'volume': z.volume,
                'heating_setpoint': z.heating_setpoint
            }
            for z in evebi_data.zones
        ]
        print(f'✅ {len(evebi_data.zones)} Zonen')
    
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
