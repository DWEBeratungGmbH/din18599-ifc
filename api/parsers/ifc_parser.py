"""
IFC Parser für DIN18599 Sidecar Generator

Extrahiert Geometrie und Bauteil-Informationen aus IFC-Dateien.
"""

import ifcopenshell
import ifcopenshell.geom
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from .ifc_material_extractor import extract_material_layers, layer_structure_to_dict
from dataclasses import dataclass, field
import math


@dataclass
class IFCElement:
    """IFC Bauteil mit Geometrie-Informationen"""
    guid: str
    ifc_type: str  # 'IfcWall', 'IfcRoof', 'IfcSlab', etc.
    name: str
    tag: Optional[str] = None  # Positionsnummer (PosNo)
    area: Optional[float] = None  # m² (berechnet)
    orientation: Optional[float] = None  # Grad (0-360, berechnet)
    inclination: Optional[float] = None  # Grad (0-90, berechnet)
    height: Optional[float] = None  # m
    storey: Optional[str] = None  # Geschoss
    material: Optional[str] = None
    parent_element_guid: Optional[str] = None  # Für Fenster/Türen: GUID der Parent-Wand


@dataclass
class IFCGeometry:
    """Vollständige IFC-Geometrie"""
    project_name: str
    site_name: Optional[str] = None
    building_name: Optional[str] = None
    building_guid: Optional[str] = None
    walls: List[IFCElement] = field(default_factory=list)
    roofs: List[IFCElement] = field(default_factory=list)
    slabs: List[IFCElement] = field(default_factory=list)
    windows: List[IFCElement] = field(default_factory=list)
    doors: List[IFCElement] = field(default_factory=list)
    all_elements: List[IFCElement] = field(default_factory=list)
    material_layers: List[Dict[str, Any]] = field(default_factory=list)  # ← NEU!


def parse_ifc(ifc_file_path: str) -> IFCGeometry:
    """
    Parst IFC-Datei und extrahiert Geometrie
    
    Args:
        ifc_file_path: Pfad zur IFC-Datei
        
    Returns:
        IFCGeometry mit allen extrahierten Elementen
    """
    # IFC-Datei öffnen
    ifc_file = ifcopenshell.open(ifc_file_path)
    
    # Projekt-Info
    project = ifc_file.by_type('IfcProject')[0] if ifc_file.by_type('IfcProject') else None
    project_name = project.Name if project else 'Unbekanntes Projekt'
    
    # Site-Info
    site = ifc_file.by_type('IfcSite')[0] if ifc_file.by_type('IfcSite') else None
    site_name = site.Name if site else None
    
    # Building-Info
    building = ifc_file.by_type('IfcBuilding')[0] if ifc_file.by_type('IfcBuilding') else None
    building_name = building.Name if building else None
    
    # Geometrie-Settings für ifcopenshell
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    
    # Elemente extrahieren
    geometry = IFCGeometry(
        project_name=project_name,
        site_name=site_name,
        building_name=building_name
    )
    
    # Wände
    for wall in ifc_file.by_type('IfcWall'):
        element = _extract_element(wall, ifc_file, settings)
        if element:
            geometry.walls.append(element)
            geometry.all_elements.append(element)
    
    # Dächer (mit Slab-Flächen)
    for roof in ifc_file.by_type('IfcRoof'):
        element = _extract_element(roof, ifc_file, settings)
        if element:
            # Aggregiere Flächen von zugehörigen Slabs
            if element.area is None or element.area == 0:
                slab_area = _calculate_roof_area_from_slabs(roof, ifc_file, settings)
                if slab_area > 0:
                    element = IFCElement(
                        guid=element.guid,
                        ifc_type=element.ifc_type,
                        name=element.name,
                        tag=element.tag,
                        area=slab_area,  # Fläche aus Slabs
                        orientation=element.orientation,
                        inclination=element.inclination,
                        height=element.height,
                        storey=element.storey,
                        parent_element_guid=element.parent_element_guid
                    )
                    print(f"  ✅ {element.name}: Fläche aus Slabs = {slab_area:.2f} m²")
            
            geometry.roofs.append(element)
            geometry.all_elements.append(element)
    
    # Decken/Böden
    for slab in ifc_file.by_type('IfcSlab'):
        element = _extract_element(slab, ifc_file, settings)
        if element:
            geometry.slabs.append(element)
            geometry.all_elements.append(element)
    
    # Fenster
    for window in ifc_file.by_type('IfcWindow'):
        element = _extract_element(window, ifc_file, settings)
        if element:
            geometry.windows.append(element)
            geometry.all_elements.append(element)
    
    # Türen
    for door in ifc_file.by_type('IfcDoor'):
        element = _extract_element(door, ifc_file, settings)
        if element:
            geometry.doors.append(element)
            geometry.all_elements.append(element)
    
    # Parent-Child-Beziehungen extrahieren (Fenster/Türen → Wände)
    print(f"\n🔍 Extrahiere Parent-Child-Beziehungen...")
    _extract_parent_child_relationships(ifc_file, geometry)
    
    # Material-Layers extrahieren (NEU!)
    print(f"\n🔍 Extrahiere Material-Schichtaufbauten...")
    layer_structures_map = {}  # GUID → LayerStructure
    
    for ifc_element in geometry.all_elements:
        # Finde IFC-Element anhand GUID
        ifc_elem = None
        for elem_type in ['IfcWall', 'IfcRoof', 'IfcSlab', 'IfcWindow', 'IfcDoor']:
            for elem in ifc_file.by_type(elem_type):
                if elem.GlobalId == ifc_element.guid:
                    ifc_elem = elem
                    break
            if ifc_elem:
                break
        
        if not ifc_elem:
            continue
        
        # Material-Layers extrahieren
        layer_structure = extract_material_layers(ifc_elem, ifc_file)
        if layer_structure:
            layer_structures_map[ifc_element.guid] = layer_structure
            geometry.material_layers.append(layer_structure_to_dict(layer_structure))
    
    print(f"   ✅ {len(geometry.material_layers)} Schichtaufbauten extrahiert")
    
    # Building GUID
    if building:
        geometry.building_guid = building.GlobalId
    
    return geometry


def _extract_element(ifc_element, ifc_file, settings) -> Optional[IFCElement]:
    """
    Extrahiert Informationen aus einem IFC-Element
    
    3-Schritt-Ansatz:
    1. Basis-Infos (GUID, Name, Typ) - IMMER
    2. Geometrie (area, orientation, inclination) - OPTIONAL
    3. EVEBI ergänzt später fehlende Daten
    """
    try:
        # ========================================
        # SCHRITT 1: Basis-Informationen (IMMER)
        # ========================================
        guid = ifc_element.GlobalId
        ifc_type = ifc_element.is_a()
        name = ifc_element.Name or f'{ifc_type} {guid[:8]}'
        tag = ifc_element.Tag if hasattr(ifc_element, 'Tag') else None
        
        # PosNo aus Properties extrahieren (falls vorhanden)
        posno = _extract_posno(ifc_element)
        if posno:
            tag = posno  # PosNo überschreibt Tag
        
        # Geschoss ermitteln
        storey = None
        for rel in ifc_element.ContainedInStructure:
            if rel.RelatingStructure.is_a('IfcBuildingStorey'):
                storey = rel.RelatingStructure.Name
                break
        
        # ========================================
        # SCHRITT 2: Geometrie (OPTIONAL)
        # ========================================
        area = None
        orientation = None
        inclination = None
        height = None
        
        try:
            shape = ifcopenshell.geom.create_shape(settings, ifc_element)
            
            # Fläche berechnen (vereinfacht)
            area = _calculate_area(shape, ifc_type)
            
            # Orientierung und Neigung berechnen
            orientation, inclination = _calculate_orientation_and_inclination(shape, ifc_type)
            
            # Höhe
            height = _calculate_height(shape)
            
            # Debug: Zeige berechnete Werte
            if orientation is not None or inclination is not None:
                print(f"  ✅ {name}: orientation={orientation}°, inclination={inclination}°, area={area}")
            
        except Exception as e:
            # Geometrie fehlgeschlagen - Element wird trotzdem erstellt
            # EVEBI kann später Geometrie-Daten ergänzen
            print(f"  ⚠️  {name}: Keine Geometrie (wird aus EVEBI ergänzt)")
        
        return IFCElement(
            guid=guid,
            ifc_type=ifc_type,
            name=name,
            tag=tag,
            area=area,
            orientation=orientation,
            inclination=inclination,
            height=height,
            storey=storey
        )
        
    except Exception as e:
        print(f"Fehler beim Extrahieren von Element {ifc_element.GlobalId}: {e}")
        return None


def _calculate_area(shape, ifc_type: str) -> Optional[float]:
    """Berechnet die Fläche eines Elements (vereinfacht)"""
    try:
        # Für Wände: Höhe * Länge
        # Für Dächer/Decken: Grundfläche
        # Vereinfachte Berechnung basierend auf Bounding Box
        
        verts = shape.geometry.verts
        if not verts or len(verts) < 9:
            return None
        
        # Bounding Box berechnen
        xs = [verts[i] for i in range(0, len(verts), 3)]
        ys = [verts[i] for i in range(1, len(verts), 3)]
        zs = [verts[i] for i in range(2, len(verts), 3)]
        
        width = max(xs) - min(xs)
        depth = max(ys) - min(ys)
        height = max(zs) - min(zs)
        
        # Flächen-Schätzung basierend auf Typ
        if 'Wall' in ifc_type:
            # Wand: max(width, depth) * height
            area = max(width, depth) * height
        elif 'Roof' in ifc_type or 'Slab' in ifc_type:
            # Dach/Decke: width * depth
            area = width * depth
        elif 'Window' in ifc_type or 'Door' in ifc_type:
            # Fenster/Tür: width * height oder depth * height
            area = max(width * height, depth * height)
        else:
            area = width * depth
        
        return round(area, 2) if area > 0 else None
        
    except Exception as e:
        return None


def _calculate_orientation_and_inclination(shape, ifc_type: str) -> Tuple[Optional[float], Optional[float]]:
    """Berechnet Orientierung (Azimut) und Neigung"""
    try:
        verts = shape.geometry.verts
        if not verts or len(verts) < 9:
            return None, None
        
        # Ersten 3 Punkte nehmen, um Normale zu berechnen
        p1 = (verts[0], verts[1], verts[2])
        p2 = (verts[3], verts[4], verts[5])
        p3 = (verts[6], verts[7], verts[8])
        
        # Vektoren
        v1 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
        v2 = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2])
        
        # Kreuzprodukt (Normale)
        nx = v1[1] * v2[2] - v1[2] * v2[1]
        ny = v1[2] * v2[0] - v1[0] * v2[2]
        nz = v1[0] * v2[1] - v1[1] * v2[0]
        
        # Normalisieren
        length = math.sqrt(nx**2 + ny**2 + nz**2)
        if length == 0:
            return None, None
        
        nx, ny, nz = nx/length, ny/length, nz/length
        
        # Orientierung (Azimut): Winkel der Projektion auf XY-Ebene
        # 0° = Nord (Y+), 90° = Ost (X+), 180° = Süd (Y-), 270° = West (X-)
        orientation = math.degrees(math.atan2(nx, ny))
        if orientation < 0:
            orientation += 360
        
        # Neigung: Winkel zur Vertikalen
        # 0° = horizontal (Dach/Boden), 90° = vertikal (Wand)
        # nz ist die Z-Komponente der Normale
        # Wenn nz=1 (zeigt nach oben) → horizontal (0°)
        # Wenn nz=0 (horizontal) → vertikal (90°)
        inclination = math.degrees(math.acos(abs(nz)))
        
        return round(orientation, 1), round(inclination, 1)
        
    except Exception as e:
        return None, None


def _calculate_roof_area_from_slabs(roof, ifc_file, settings) -> float:
    """
    Berechnet Dachfläche aus zugehörigen Slabs
    Dächer haben oft keine eigene Geometrie, aber Slabs als Teilflächen
    """
    try:
        total_area = 0.0
        processed_guids = set()  # Verhindere Duplikate
        
        # Finde zugehörige Slabs über IsDecomposedBy
        if hasattr(roof, 'IsDecomposedBy'):
            for rel in roof.IsDecomposedBy:
                for elem in rel.RelatedObjects:
                    if elem.is_a('IfcSlab') and elem.GlobalId not in processed_guids:
                        processed_guids.add(elem.GlobalId)
                        
                        # Berechne Slab-Fläche
                        try:
                            shape = ifcopenshell.geom.create_shape(settings, elem)
                            area = _calculate_area(shape, elem.is_a())
                            if area:
                                total_area += area
                        except:
                            pass
        
        return total_area
        
    except Exception as e:
        return 0.0


def _calculate_height(shape) -> Optional[float]:
    """Berechnet die Höhe eines Elements"""
    try:
        verts = shape.geometry.verts
        if not verts or len(verts) < 3:
            return None
        
        zs = [verts[i] for i in range(2, len(verts), 3)]
        height = max(zs) - min(zs)
        
        return round(height, 2) if height > 0 else None
        
    except Exception as e:
        return None


def _extract_parent_child_relationships(ifc_file, geometry: IFCGeometry):
    """
    Extrahiert Parent-Child-Beziehungen zwischen Fenstern/Türen und Wänden
    
    IFC-Struktur:
    - IfcWindow/IfcDoor → IfcRelFillsElement → IfcOpeningElement
    - IfcOpeningElement → IfcRelVoidsElement → IfcWall
    """
    # Mapping: Opening GUID → Wall GUID
    opening_to_wall = {}
    
    # 1. IfcRelVoidsElement: Wand → Öffnung
    for rel in ifc_file.by_type('IfcRelVoidsElement'):
        if rel.RelatingBuildingElement and rel.RelatedOpeningElement:
            wall_guid = rel.RelatingBuildingElement.GlobalId
            opening_guid = rel.RelatedOpeningElement.GlobalId
            opening_to_wall[opening_guid] = wall_guid
    
    # 2. IfcRelFillsElement: Öffnung → Fenster/Tür
    window_to_opening = {}
    for rel in ifc_file.by_type('IfcRelFillsElement'):
        if rel.RelatingOpeningElement and rel.RelatedBuildingElement:
            opening_guid = rel.RelatingOpeningElement.GlobalId
            element_guid = rel.RelatedBuildingElement.GlobalId
            window_to_opening[element_guid] = opening_guid
    
    # 3. Verknüpfe Fenster/Türen mit Wänden
    for element in geometry.all_elements:
        if element.ifc_type in ['IfcWindow', 'IfcDoor']:
            # Finde Öffnung
            opening_guid = window_to_opening.get(element.guid)
            if opening_guid:
                # Finde Wand
                wall_guid = opening_to_wall.get(opening_guid)
                if wall_guid:
                    element.parent_element_guid = wall_guid
                    print(f"  ✅ {element.name} → Parent: {wall_guid[:8]}")


def _extract_posno(ifc_element) -> Optional[str]:
    """
    Extrahiert PosNo aus IFC PropertySets
    
    Sucht nach:
    - Property "PosNo"
    - Property "Positionsnummer"
    - Property "Position"
    - Aus Name extrahiert (z.B. "Wand Pos 001")
    """
    try:
        # 1. Aus PropertySets
        if hasattr(ifc_element, 'IsDefinedBy'):
            for definition in ifc_element.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_set = definition.RelatingPropertyDefinition
                    if property_set.is_a('IfcPropertySet'):
                        for prop in property_set.HasProperties:
                            if prop.is_a('IfcPropertySingleValue'):
                                # PosNo, Positionsnummer, Position
                                if prop.Name in ['PosNo', 'Positionsnummer', 'Position', 'Tag']:
                                    if prop.NominalValue:
                                        return str(prop.NominalValue.wrappedValue)
        
        # 2. Aus Name extrahiert (z.B. "Außenwand Pos 001")
        if hasattr(ifc_element, 'Name') and ifc_element.Name:
            name = ifc_element.Name
            # Suche nach "Pos XXX" Pattern
            import re
            match = re.search(r'Pos\s*(\d+)', name, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # 3. Aus Tag (falls vorhanden)
        if hasattr(ifc_element, 'Tag') and ifc_element.Tag:
            return ifc_element.Tag
        
        return None
        
    except Exception as e:
        return None


def ifc_geometry_to_dict(ifc_geometry: IFCGeometry) -> dict:
    """
    Konvertiert IFCGeometry in Dictionary-Format für Sidecar Generator
    Inkludiert vollständige Material-Schichtaufbauten (NEU!)
    """
    
    # Konvertiere IFCElement Objekte zu Dicts
    def element_to_dict(elem: IFCElement) -> dict:
        return {
            "guid": elem.guid,
            "ifc_type": elem.ifc_type,
            "name": elem.name,
            "tag": elem.tag,
            "area": elem.area,
            "orientation": elem.orientation,
            "inclination": elem.inclination,
            "height": elem.height,
            "storey": elem.storey,
            "material": elem.material,
            "parent_element_guid": elem.parent_element_guid
        }
    
    return {
        "project_name": ifc_geometry.project_name,
        "building_guid": ifc_geometry.building_guid or "UNKNOWN",
        "material_layers": ifc_geometry.material_layers,  # ← NEU!
        "all_elements": [element_to_dict(elem) for elem in ifc_geometry.all_elements],  # ← NEU!
        "walls": [
            {
                "guid": elem.guid,
                "name": elem.name,
                "area": elem.area or 0.0,
                "properties": {
                    "PosNo": elem.tag,
                    "Storey": elem.storey,
                    "Orientation": elem.orientation,
                    "Inclination": elem.inclination
                }
            }
            for elem in ifc_geometry.walls
        ],
        "roofs": [
            {
                "guid": elem.guid,
                "name": elem.name,
                "area": elem.area or 0.0,
                "properties": {
                    "PosNo": elem.tag,
                    "Storey": elem.storey,
                    "Orientation": elem.orientation,
                    "Inclination": elem.inclination
                }
            }
            for elem in ifc_geometry.roofs
        ],
        "floors": [
            {
                "guid": elem.guid,
                "name": elem.name,
                "area": elem.area or 0.0,
                "properties": {
                    "PosNo": elem.tag,
                    "Storey": elem.storey
                }
            }
            for elem in ifc_geometry.slabs
        ],
        "windows": [
            {
                "guid": elem.guid,
                "name": elem.name,
                "area": elem.area or 0.0,
                "properties": {
                    "PosNo": elem.tag,
                    "Storey": elem.storey
                }
            }
            for elem in ifc_geometry.windows
        ],
        "doors": [
            {
                "guid": elem.guid,
                "name": elem.name,
                "area": elem.area or 0.0,
                "properties": {
                    "PosNo": elem.tag,
                    "Storey": elem.storey
                }
            }
            for elem in ifc_geometry.doors
        ]
    }
