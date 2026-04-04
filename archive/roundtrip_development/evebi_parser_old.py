"""
EVEBI .evea Parser
Parst EVEBI Archiv-Dateien (ZIP mit projekt.xml)
"""

import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class EVEBIMaterial:
    """Material mit Wärmeleitfähigkeit"""
    guid: str
    name: str
    lambda_value: float  # W/mK
    density: Optional[float] = None  # kg/m³
    specific_heat: Optional[float] = None  # J/(kg·K)


@dataclass
class EVEBILayer:
    """Schicht einer Konstruktion"""
    material_name: str
    thickness: float  # m
    lambda_value: float  # W/mK
    position: int


@dataclass
class EVEBIConstruction:
    """Bauteil-Konstruktion mit Schichten"""
    guid: str
    name: str
    u_value: float  # W/(m²K)
    layers: List[EVEBILayer] = field(default_factory=list)
    total_thickness: float = 0.0  # m


@dataclass
class EVEBIElement:
    """Bauteil (Wand, Dach, Boden)"""
    guid: str
    name: str
    element_type: str  # 'Wall', 'Roof', 'Floor', 'Window', 'Door'
    area: float  # m²
    orientation: Optional[float] = None  # Grad (0-360)
    inclination: Optional[float] = None  # Grad (0-90)
    u_value: Optional[float] = None  # W/(m²K)
    construction_ref: Optional[str] = None
    boundary_condition: Optional[str] = None  # 'Aussenluft', 'Erdreich', etc.
    posno: Optional[str] = None  # Positionsnummer (Link zu IFC)


@dataclass
class EVEBIZone:
    """Thermische Zone"""
    guid: str
    name: str
    area: float  # m²
    volume: float  # m³
    heating_setpoint: Optional[float] = None  # °C
    cooling_setpoint: Optional[float] = None  # °C


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
    
    Args:
        evea_path: Pfad zur .evea Datei
        
    Returns:
        EVEBIData Objekt
    """
    import zipfile
    import xml.etree.ElementTree as ET
    from pathlib import Path
    
    print(f"\n=== EVEBI Parser Debug ===")
    print(f"📂 EVEA-Datei: {evea_path}")
    
    # 1. ZIP entpacken
    extract_dir = Path('/tmp/evea_extract')
    extract_dir.mkdir(exist_ok=True)
    
    print(f"📦 Entpacke ZIP nach: {extract_dir}")
    
    try:
        with zipfile.ZipFile(evea_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f"📋 Dateien im ZIP: {file_list}")
            zip_ref.extractall(extract_dir)
            print(f"✅ ZIP erfolgreich entpackt")
    except Exception as e:
        print(f"❌ Fehler beim Entpacken: {e}")
        raise
    
    # 2. projekt.xml finden
    xml_path = extract_dir / 'projekt.xml'
    print(f"🔍 Suche projekt.xml: {xml_path}")
    
    if not xml_path.exists():
        print(f"❌ projekt.xml nicht gefunden!")
        print(f"📁 Verfügbare Dateien: {list(extract_dir.iterdir())}")
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
    
    # 3. Projekt-Info
    project_guid = root.get('GUID', '')
    project_name = root.findtext('.//projektname', 'Unbekanntes Projekt')
    
    # 4. Daten extrahieren
    print(f"\n🔍 Extrahiere Daten...")
    print(f"📋 Projekt: {project_name} (GUID: {project_guid})")
    
    materials = _extract_materials(root)
    print(f"✅ Materialien: {len(materials)}")
    
    constructions = _extract_constructions(root)
    print(f"✅ Konstruktionen: {len(constructions)}")
    
    elements = _extract_elements(root)
    print(f"✅ Bauteile: {len(elements)}")
    
    zones = _extract_zones(root)
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


def _extract_materials(root: ET.Element) -> List[EVEBIMaterial]:
    """Extrahiert Materialien mit λ-Werten"""
    materials = []
    
    print(f"  🔍 Suche Materialien in XML...")
    
    # Suche nach Material-Definitionen
    material_items = root.findall('.//MaterialListe/item')
    print(f"  📋 Gefunden: {len(material_items)} Material-Items")
    
    for item in material_items:
        guid = item.get('GUID', '')
        name = item.findtext('name', 'Unbekannt')
        
        # Lambda-Wert extrahieren
        lambda_elem = item.find('lambda')
        lambda_value = 0.0
        if lambda_elem is not None:
            try:
                lambda_value = float(lambda_elem.text or 0)
            except ValueError:
                lambda_value = 0.0
        
        # Dichte (optional)
        density_elem = item.find('dichte')
        density = None
        if density_elem is not None:
            try:
                density = float(density_elem.text or 0)
            except ValueError:
                density = None
        
        materials.append(EVEBIMaterial(
            guid=guid,
            name=name,
            lambda_value=lambda_value,
            density=density
        ))
    
    return materials


def _extract_constructions(root: ET.Element) -> List[EVEBIConstruction]:
    """Extrahiert Konstruktionen (Schichtaufbauten)"""
    constructions = []
    
    print(f"  🔍 Suche Konstruktionen in XML...")
    
    # Suche nach Konstruktions-Definitionen
    construction_items = root.findall('.//BauteilListe/item')
    print(f"  📋 Gefunden: {len(construction_items)} Konstruktions-Items")
    
    for item in construction_items:
        guid = item.get('GUID', '')
        name = item.findtext('name', 'Unbekannte Konstruktion')
        
        # U-Wert
        u_value_elem = item.find('u_wert')
        u_value = 0.0
        if u_value_elem is not None:
            try:
                u_value = float(u_value_elem.text or 0)
            except ValueError:
                u_value = 0.0
        
        # Schichten extrahieren
        layers = []
        total_thickness = 0.0
        
        for idx, layer_elem in enumerate(item.findall('.//SchichtListe/item')):
            material_name = layer_elem.findtext('material', 'Unbekannt')
            
            # Dicke
            thickness_elem = layer_elem.find('dicke')
            thickness = 0.0
            if thickness_elem is not None:
                try:
                    thickness = float(thickness_elem.text or 0)
                except ValueError:
                    thickness = 0.0
            
            # Lambda
            lambda_elem = layer_elem.find('lambda')
            lambda_value = 0.0
            if lambda_elem is not None:
                try:
                    lambda_value = float(lambda_elem.text or 0)
                except ValueError:
                    lambda_value = 0.0
            
            layers.append(EVEBILayer(
                material_name=material_name,
                thickness=thickness,
                lambda_value=lambda_value,
                position=idx
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


def _extract_elements(root: ET.Element) -> List[EVEBIElement]:
    """Extrahiert Bauteile (Wände, Dächer, etc.)"""
    elements = []
    
    print(f"  🔍 Suche Bauteile in XML...")
    
    # Suche nach Bauteil-Definitionen in verschiedenen Listen
    element_lists = [
        ('.//WandListe/item', 'Wall'),
        ('.//DachListe/item', 'Roof'),
        ('.//BodenListe/item', 'Floor'),
        ('.//FensterListe/item', 'Window'),
        ('.//TuerListe/item', 'Door')
    ]
    
    for xpath, element_type in element_lists:
        items = root.findall(xpath)
        print(f"    📋 {element_type}: {len(items)} Items gefunden")
        
        for item in items:
            guid = item.get('GUID', '')
            name = item.findtext('name', 'Unbekanntes Bauteil')
            
            # Element-Typ bereits aus Liste
            if 'Wand' in xpath:
                element_type = 'Wall'
            elif 'Dach' in xpath:
                element_type = 'Roof'
            elif 'Boden' in xpath:
                element_type = 'Floor'
            elif 'Fenster' in xpath:
                element_type = 'Window'
            elif 'Tuer' in xpath:
                element_type = 'Door'
            
            # Fläche
            area_elem = item.find('flaeche')
            area = 0.0
            if area_elem is not None:
                try:
                    area = float(area_elem.text or 0)
                except ValueError:
                    area = 0.0
            
            # Orientierung
            orientation_elem = item.find('orientierung')
            orientation = None
            if orientation_elem is not None:
                try:
                    orientation = float(orientation_elem.text or 0)
                except ValueError:
                    orientation = None
            
            # Neigung
            inclination_elem = item.find('neigung')
            inclination = None
            if inclination_elem is not None:
                try:
                    inclination = float(inclination_elem.text or 0)
                except ValueError:
                    inclination = None
            
            # U-Wert
            u_value_elem = item.find('u_wert')
            u_value = None
            if u_value_elem is not None:
                try:
                    u_value = float(u_value_elem.text or 0)
                except ValueError:
                    u_value = None
            
            # Konstruktions-Referenz
            construction_ref = item.findtext('konstruktion_ref')
            
            # Randbedingung
            boundary_condition = item.findtext('randbedingung')
            
            # PosNo (falls vorhanden)
            posno = item.findtext('posno')
            
            elements.append(EVEBIElement(
                guid=guid,
                name=name,
                element_type=element_type,
                area=area,
                orientation=orientation,
                inclination=inclination,
                u_value=u_value,
                construction_ref=construction_ref,
                boundary_condition=boundary_condition,
                posno=posno
            ))
    
    return elements


def _extract_zones(root: ET.Element) -> List[EVEBIZone]:
    """Extrahiert thermische Zonen"""
    zones = []
    
    print(f"  🔍 Suche Zonen in XML...")
    
    zone_items = root.findall('.//ZoneListe/item')
    print(f"  📋 Gefunden: {len(zone_items)} Zonen-Items")
    
    for item in zone_items:
        guid = item.get('GUID', '')
        name = item.findtext('name', 'Unbekannte Zone')
        
        # Fläche
        area_elem = item.find('flaeche')
        area = 0.0
        if area_elem is not None:
            try:
                area = float(area_elem.text or 0)
            except ValueError:
                area = 0.0
        
        # Volumen
        volume_elem = item.find('volumen')
        volume = 0.0
        if volume_elem is not None:
            try:
                volume = float(volume_elem.text or 0)
            except ValueError:
                volume = 0.0
        
        # Solltemperaturen
        heating_setpoint_elem = item.find('solltemperatur_heizen')
        heating_setpoint = None
        if heating_setpoint_elem is not None:
            try:
                heating_setpoint = float(heating_setpoint_elem.text or 0)
            except ValueError:
                heating_setpoint = None
        
        cooling_setpoint_elem = item.find('solltemperatur_kuehlen')
        cooling_setpoint = None
        if cooling_setpoint_elem is not None:
            try:
                cooling_setpoint = float(cooling_setpoint_elem.text or 0)
            except ValueError:
                cooling_setpoint = None
        
        zones.append(EVEBIZone(
            guid=guid,
            name=name,
            area=area,
            volume=volume,
            heating_setpoint=heating_setpoint,
            cooling_setpoint=cooling_setpoint
        ))
    
    return zones
