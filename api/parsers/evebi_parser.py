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


def parse_evea(evea_file_path: str) -> EVEBIData:
    """
    Parst EVEBI .evea Archiv
    
    Args:
        evea_file_path: Pfad zur .evea Datei
        
    Returns:
        EVEBIData mit allen extrahierten Daten
    """
    # 1. ZIP entpacken und projekt.xml lesen
    with zipfile.ZipFile(evea_file_path, 'r') as zip_ref:
        xml_content = zip_ref.read('projekt.xml')
    
    # 2. XML parsen
    root = ET.fromstring(xml_content)
    
    # 3. Projekt-Info
    project_guid = root.get('GUID', '')
    project_name = root.findtext('.//projektname', 'Unbekanntes Projekt')
    
    # 4. Daten extrahieren
    evebi_data = EVEBIData(
        project_guid=project_guid,
        project_name=project_name,
        materials=_extract_materials(root),
        constructions=_extract_constructions(root),
        elements=_extract_elements(root),
        zones=_extract_zones(root)
    )
    
    return evebi_data


def _extract_materials(root: ET.Element) -> List[EVEBIMaterial]:
    """Extrahiert Materialien mit λ-Werten"""
    materials = []
    
    # Suche nach Material-Definitionen
    for item in root.findall('.//MaterialListe/item'):
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
    """Extrahiert Konstruktionen mit Schichten"""
    constructions = []
    
    # Suche nach Konstruktions-Definitionen
    for item in root.findall('.//KonstruktionListe/item'):
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
    
    # Suche nach Bauteil-Definitionen in verschiedenen Listen
    element_lists = [
        './/WandListe/item',
        './/DachListe/item',
        './/BodenListe/item',
        './/FensterListe/item',
        './/TuerListe/item'
    ]
    
    for xpath in element_lists:
        for item in root.findall(xpath):
            guid = item.get('GUID', '')
            name = item.findtext('name', 'Unbekanntes Bauteil')
            
            # Element-Typ aus XPath ableiten
            element_type = 'Unknown'
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
    
    for item in root.findall('.//ZoneListe/item'):
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
