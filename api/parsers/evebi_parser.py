"""
EVEBI Parser v2 - Basierend auf tatsächlicher XML-Struktur
"""

from typing import List, Optional
from dataclasses import dataclass, field
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


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
    element_type: str  # Wall, Roof, Floor, Window, Door
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


def parse_evea(evea_path: str) -> EVEBIData:
    """
    Parst EVEBI .evea Archiv (ZIP mit projekt.xml)
    """
    print(f"\n=== EVEBI Parser v2 Debug ===")
    print(f"📂 EVEA-Datei: {evea_path}")
    
    # 1. ZIP entpacken
    extract_dir = Path('/tmp/evea_extract')
    extract_dir.mkdir(exist_ok=True)
    
    print(f"📦 Entpacke ZIP...")
    
    try:
        with zipfile.ZipFile(evea_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f"📋 Dateien im ZIP: {len(file_list)}")
            zip_ref.extractall(extract_dir)
            print(f"✅ ZIP erfolgreich entpackt")
    except Exception as e:
        print(f"❌ Fehler beim Entpacken: {e}")
        raise
    
    # 2. projekt.xml finden
    xml_path = extract_dir / 'projekt.xml'
    print(f"🔍 Suche projekt.xml...")
    
    if not xml_path.exists():
        print(f"❌ projekt.xml nicht gefunden!")
        raise FileNotFoundError(f"projekt.xml nicht gefunden in {evea_path}")
    
    print(f"✅ projekt.xml gefunden")
    
    # 3. XML parsen
    print(f"📖 Parse XML...")
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        print(f"✅ XML geparst, Root-Tag: {root.tag}")
    except Exception as e:
        print(f"❌ Fehler beim XML-Parsen: {e}")
        raise
    
    # 4. Projekt-Info
    project_guid = root.get('GUID', '')
    
    # Projektname aus verschiedenen Quellen
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
    
    print(f"📋 Projekt: {project_name} (GUID: {project_guid})")
    
    # 5. Daten extrahieren
    print(f"\n🔍 Extrahiere Daten...")
    
    materials = _extract_materials(eing) if eing is not None else []
    print(f"✅ Materialien: {len(materials)}")
    
    constructions = _extract_constructions(eing) if eing is not None else []
    print(f"✅ Konstruktionen: {len(constructions)}")
    
    elements = _extract_elements(eing) if eing is not None else []
    print(f"✅ Bauteile: {len(elements)}")
    
    zones = _extract_zones(eing) if eing is not None else []
    print(f"✅ Zonen: {len(zones)}")
    
    evebi_data = EVEBIData(
        project_guid=project_guid,
        project_name=project_name,
        materials=materials,
        constructions=constructions,
        elements=elements,
        zones=zones
    )
    
    print(f"\n✅ EVEBI Parser erfolgreich abgeschlossen!")
    print(f"=== Ende Debug ===\n")
    
    return evebi_data


def _extract_materials(eing: ET.Element) -> List[EVEBIMaterial]:
    """Extrahiert Materialien aus konstruktionenListe"""
    materials = []
    
    print(f"  🔍 Suche Materialien...")
    
    konstr_liste = eing.find('konstruktionenListe')
    if konstr_liste is None:
        print(f"  ⚠️  Keine konstruktionenListe gefunden")
        return materials
    
    items = list(konstr_liste)
    print(f"  📋 Gefunden: {len(items)} Konstruktions-Items")
    
    for item in items:
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
        
        if lambda_value > 0:  # Nur wenn Lambda-Wert vorhanden
            materials.append(EVEBIMaterial(
                guid=guid,
                name=name,
                lambda_value=lambda_value,
                density=density
            ))
    
    return materials


def _extract_constructions(eing: ET.Element) -> List[EVEBIConstruction]:
    """Extrahiert Konstruktionen"""
    constructions = []
    
    print(f"  🔍 Suche Konstruktionen...")
    
    konstr_liste = eing.find('konstruktionenListe')
    if konstr_liste is None:
        return constructions
    
    items = list(konstr_liste)
    print(f"  📋 Gefunden: {len(items)} Konstruktions-Items")
    
    for item in items:
        guid = item.get('GUID', '')
        name = item.findtext('.//name', 'Unbekannte Konstruktion')
        
        # U-Wert
        u_elem = item.find('.//U')
        u_value = 0.0
        if u_elem is not None:
            try:
                u_value = float(u_elem.get('man', u_elem.get('calc', '0')))
            except (ValueError, TypeError):
                u_value = 0.0
        
        constructions.append(EVEBIConstruction(
            guid=guid,
            name=name,
            u_value=u_value
        ))
    
    return constructions


def _extract_elements(eing: ET.Element) -> List[EVEBIElement]:
    """Extrahiert Bauteile aus tflListe (Teilflächen)"""
    elements = []
    
    print(f"  🔍 Suche Bauteile in tflListe...")
    
    tfl_liste = eing.find('tflListe')
    if tfl_liste is None:
        print(f"  ⚠️  Keine tflListe gefunden")
        return elements
    
    items = list(tfl_liste)
    print(f"  📋 Gefunden: {len(items)} Teilflächen-Items")
    
    for item in items:
        guid = item.get('GUID', '')
        name = item.findtext('.//name', 'Unbekanntes Bauteil')
        
        # Element-Typ aus Name ableiten
        element_type = 'Unknown'
        if 'Wand' in name or 'wand' in name:
            element_type = 'Wall'
        elif 'Dach' in name or 'dach' in name:
            element_type = 'Roof'
        elif 'Boden' in name or 'Decke' in name:
            element_type = 'Floor'
        elif 'Fenster' in name or 'fenster' in name:
            element_type = 'Window'
        elif 'Tür' in name or 'tür' in name or 'Tuer' in name:
            element_type = 'Door'
        
        # PosNo aus Name extrahieren (z.B. "Zwischenwand Pos 005" -> "005")
        posno = None
        if 'Pos' in name:
            parts = name.split('Pos')
            if len(parts) > 1:
                posno_str = parts[1].strip().split()[0]
                posno = posno_str
        
        # Fläche (nettoA)
        area = None
        netto_a = item.findtext('.//nettoA', None)
        if netto_a:
            try:
                area = float(netto_a)
            except (ValueError, TypeError):
                area = None
        
        # U-Wert
        u_value = None
        u_elem = item.find('.//U')
        if u_elem is not None:
            try:
                u_value = float(u_elem.get('man', u_elem.get('calc', '0')))
            except (ValueError, TypeError):
                u_value = None
        
        # Orientierung
        orientation = None
        orient_text = item.findtext('.//orientierung', None)
        if orient_text:
            try:
                orientation = float(orient_text)
            except (ValueError, TypeError):
                orientation = None
        
        # Neigung
        inclination = None
        neig_text = item.findtext('.//neigGrad', None)
        if neig_text:
            try:
                inclination = float(neig_text)
            except (ValueError, TypeError):
                inclination = None
        
        elements.append(EVEBIElement(
            guid=guid,
            name=name,
            element_type=element_type,
            area=area,
            orientation=orientation,
            inclination=inclination,
            u_value=u_value,
            posno=posno
        ))
    
    return elements


def _extract_zones(eing: ET.Element) -> List[EVEBIZone]:
    """Extrahiert Zonen aus geschosseListe und rmListe"""
    zones = []
    
    print(f"  🔍 Suche Zonen...")
    
    # Geschosse
    geschosse_liste = eing.find('geschosseListe')
    if geschosse_liste is not None:
        items = list(geschosse_liste)
        print(f"  📋 Geschosse: {len(items)}")
        
        for item in items:
            guid = item.get('GUID', '')
            name = item.findtext('.//name', 'Unbekanntes Geschoss')
            
            # Fläche
            area = 0.0
            a_elem = item.find('.//A')
            if a_elem is not None:
                try:
                    area = float(a_elem.get('man', a_elem.get('calc', '0')))
                except (ValueError, TypeError):
                    area = 0.0
            
            # Volumen
            volume = 0.0
            v_elem = item.find('.//V')
            if v_elem is not None:
                try:
                    volume = float(v_elem.get('man', v_elem.get('calc', '0')))
                except (ValueError, TypeError):
                    volume = 0.0
            
            zones.append(EVEBIZone(
                guid=guid,
                name=name,
                area=area,
                volume=volume
            ))
    
    return zones


def evebi_data_to_dict(evebi_data: EVEBIData) -> dict:
    """
    Konvertiert EVEBIData in Dictionary-Format für Sidecar Generator
    """
    return {
        "project_guid": evebi_data.project_guid,
        "project_name": evebi_data.project_name,
        "materials": [
            {
                "guid": mat.guid,
                "name": mat.name,
                "lambda": mat.lambda_value,
                "density": mat.density
            }
            for mat in evebi_data.materials
        ],
        "constructions": [
            {
                "guid": konstr.guid,
                "name": konstr.name,
                "u_value": konstr.u_value
            }
            for konstr in evebi_data.constructions
        ],
        "elements": [
            {
                "guid": elem.guid,
                "name": elem.name,
                "posno": elem.posno,
                "element_type": elem.element_type,
                "area": elem.area or 0.0,
                "u_value": elem.u_value or 0.0,
                "orientation": elem.orientation,
                "inclination": elem.inclination,
                "construction_ref": elem.construction_ref
            }
            for elem in evebi_data.elements
        ],
        "zones": [
            {
                "guid": zone.guid,
                "name": zone.name,
                "area": zone.area,
                "volume": zone.volume
            }
            for zone in evebi_data.zones
        ]
    }
