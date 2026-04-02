"""
IFC Parser v2 - 8-Schritte-Pipeline für DIN18599 Sidecar Generator

Systematische Extraktion nach Best Practices:
1. Header (Schema, Projekt, Software)
2. Räumliche Struktur (Geschosse, Räume)
3. Bauteile inventarisieren
4. Properties extrahieren (IsExternal, U-Werte, Psets)
5. Materialien und Schichten
6. Beziehungen (Parent-Child, Aggregation)
7. Geometrie (Fläche, Orientierung, Neigung)
8. Validierung (DIN 18599 Konsistenz)
"""

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import math

# R3-FIX: Import an Dateianfang statt in Methode
try:
    from .ifc_material_extractor import extract_material_layers, layer_structure_to_dict
    HAS_MATERIAL_EXTRACTOR = True
except ImportError:
    HAS_MATERIAL_EXTRACTOR = False
    print("⚠️  ifc_material_extractor nicht gefunden - Schichtaufbauten werden übersprungen")


@dataclass
class IFCElement:
    """IFC-Element mit allen relevanten Informationen"""
    guid: str
    ifc_type: str
    name: str
    tag: Optional[str] = None
    area: Optional[float] = None
    orientation: Optional[float] = None
    inclination: Optional[float] = None
    height: Optional[float] = None
    storey: Optional[str] = None
    material: Optional[str] = None
    parent_element_guid: Optional[str] = None
    predefined_type: Optional[str] = None
    # Step 4: Properties
    is_external: Optional[bool] = None
    u_value: Optional[float] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IFCGeometry:
    """Vollständige IFC-Geometrie mit Validierung"""
    # Step 1: Header
    schema: str = ""
    project_name: str = ""
    site_name: Optional[str] = None
    building_name: Optional[str] = None
    building_guid: Optional[str] = None
    
    # Step 2: Räumliche Struktur (S1-FIX)
    storeys: List[Dict[str, Any]] = field(default_factory=list)
    spaces: List[Dict[str, Any]] = field(default_factory=list)
    
    # Step 3: Bauteile
    walls: List[IFCElement] = field(default_factory=list)
    roofs: List[IFCElement] = field(default_factory=list)
    slabs: List[IFCElement] = field(default_factory=list)
    windows: List[IFCElement] = field(default_factory=list)
    doors: List[IFCElement] = field(default_factory=list)
    all_elements: List[IFCElement] = field(default_factory=list)
    
    # Step 5: Materialien
    material_layers: List[Dict[str, Any]] = field(default_factory=list)
    
    # Step 8: Validierung
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class IFCParser:
    """8-Schritte IFC Parser für DIN 18599"""
    
    def __init__(self, ifc_file_path: str):
        self.ifc_file = ifcopenshell.open(ifc_file_path)
        self.settings = ifcopenshell.geom.settings()
        self.settings.set(self.settings.USE_WORLD_COORDS, True)
        self.geometry = IFCGeometry()
        self.ifc_cache = {}  # N2-FIX: GUID-Cache für Performance
    
    def parse(self) -> IFCGeometry:
        """Führt alle 8 Schritte aus"""
        print(f"\n{'='*60}")
        print(f"🔬 IFC PARSER v2 - 8-Schritte-Pipeline")
        print(f"{'='*60}\n")
        
        self.step1_header()
        self.step2_spatial_structure()
        self.step3_collect_elements()
        self.step4_extract_properties()
        self.step5_extract_materials()
        self.step6_extract_relationships()
        self.step7_calculate_geometry()
        self.step8_validate()
        
        print(f"\n{'='*60}")
        print(f"✅ PARSING ABGESCHLOSSEN")
        print(f"{'='*60}\n")
        
        return self.geometry
    
    def step1_header(self):
        """Step 1: Header - Schema, Projekt, Software"""
        print("1️⃣  Header...")
        
        project = self.ifc_file.by_type('IfcProject')[0]
        self.geometry.schema = self.ifc_file.schema
        self.geometry.project_name = project.Name
        
        buildings = self.ifc_file.by_type('IfcBuilding')
        if buildings:
            self.geometry.building_name = buildings[0].Name
            self.geometry.building_guid = buildings[0].GlobalId
        
        print(f"   Schema: {self.geometry.schema}")
        print(f"   Projekt: {self.geometry.project_name}")
    
    def step2_spatial_structure(self):
        """Step 2: Räumliche Struktur - Geschosse, Räume"""
        print("2️⃣  Räumliche Struktur...")
        
        # S1-FIX: Speichere Geschoss-Daten für spätere Nutzung
        storeys = self.ifc_file.by_type('IfcBuildingStorey')
        for storey in storeys:
            self.geometry.storeys.append({
                'guid': storey.GlobalId,
                'name': storey.Name,
                'elevation': storey.Elevation if hasattr(storey, 'Elevation') else None
            })
        
        spaces = self.ifc_file.by_type('IfcSpace')
        for space in spaces:
            self.geometry.spaces.append({
                'guid': space.GlobalId,
                'name': space.Name or 'Unnamed'
            })
        
        print(f"   Geschosse: {len(self.geometry.storeys)}")
        print(f"   Räume: {len(self.geometry.spaces)}")
    
    def step3_collect_elements(self):
        """Step 3: Bauteile inventarisieren"""
        print("3️⃣  Bauteile sammeln...")
        
        # N2-FIX: Baue GUID-Cache für alle nachfolgenden Steps
        for wall in self.ifc_file.by_type('IfcWall'):
            elem = self._extract_element_basic(wall)
            if elem:
                self.ifc_cache[elem.guid] = wall  # Cache IFC-Objekt
                self.geometry.walls.append(elem)
                self.geometry.all_elements.append(elem)
        
        for roof in self.ifc_file.by_type('IfcRoof'):
            elem = self._extract_element_basic(roof)
            if elem:
                self.ifc_cache[elem.guid] = roof
                self.geometry.roofs.append(elem)
                self.geometry.all_elements.append(elem)
        
        # K4-FIX: Slabs nach PredefinedType routen
        for slab in self.ifc_file.by_type('IfcSlab'):
            elem = self._extract_element_basic(slab)
            if elem:
                self.ifc_cache[elem.guid] = slab
                if elem.predefined_type == "ROOF":
                    self.geometry.roofs.append(elem)
                else:
                    self.geometry.slabs.append(elem)
                self.geometry.all_elements.append(elem)
        
        for window in self.ifc_file.by_type('IfcWindow'):
            elem = self._extract_element_basic(window)
            if elem:
                self.ifc_cache[elem.guid] = window
                self.geometry.windows.append(elem)
                self.geometry.all_elements.append(elem)
        
        for door in self.ifc_file.by_type('IfcDoor'):
            elem = self._extract_element_basic(door)
            if elem:
                self.ifc_cache[elem.guid] = door
                self.geometry.doors.append(elem)
                self.geometry.all_elements.append(elem)
        
        print(f"   Wände: {len(self.geometry.walls)}")
        print(f"   Dächer: {len(self.geometry.roofs)}")
        print(f"   Böden: {len(self.geometry.slabs)}")
        print(f"   Fenster: {len(self.geometry.windows)}")
        print(f"   Türen: {len(self.geometry.doors)}")
    
    def step4_extract_properties(self):
        """Step 4: Properties - IsExternal, U-Werte, Psets"""
        print("4️⃣  Properties extrahieren...")
        
        props_count = 0
        for elem in self.geometry.all_elements:
            try:
                ifc_elem = self.ifc_cache.get(elem.guid)  # N2-FIX: Nutze Cache
                if not ifc_elem:
                    continue
                psets = ifcopenshell.util.element.get_psets(ifc_elem)
                
                if 'Pset_WallCommon' in psets:
                    elem.is_external = psets['Pset_WallCommon'].get('IsExternal')
                    elem.u_value = psets['Pset_WallCommon'].get('ThermalTransmittance')
                
                elem.properties = psets
                props_count += 1
                
            except Exception as e:
                pass
        
        print(f"   Properties für {props_count} Elemente extrahiert")
    
    def step5_extract_materials(self):
        """Step 5: Materialien und Schichten"""
        print("5️⃣  Materialien...")
        
        # R3-FIX: Import bereits am Anfang der Datei
        
        for elem in self.geometry.all_elements:
            try:
                ifc_elem = self.ifc_cache.get(elem.guid)  # N2-FIX
                if not ifc_elem:
                    continue
                
                # Material-Name
                if hasattr(ifc_elem, 'HasAssociations'):
                    for assoc in ifc_elem.HasAssociations:
                        if assoc.is_a('IfcRelAssociatesMaterial'):
                            mat = assoc.RelatingMaterial
                            if hasattr(mat, 'Name'):
                                elem.material = mat.Name
                
                # N3-FIX: Schichtaufbau (R3-FIX: mit try/except)
                if HAS_MATERIAL_EXTRACTOR:
                    layer_structure = extract_material_layers(ifc_elem, self.ifc_file)
                    if layer_structure:
                        layer_dict = layer_structure_to_dict(layer_structure)
                        layer_dict['element_guid'] = elem.guid
                        self.geometry.material_layers.append(layer_dict)
                    
            except:
                pass
        
        print(f"   Materialien: {len([e for e in self.geometry.all_elements if e.material])}")
        print(f"   Schichtaufbauten: {len(self.geometry.material_layers)}")
    
    def step6_extract_relationships(self):
        """Step 6: Beziehungen - Parent-Child, Aggregation"""
        print("6️⃣  Beziehungen...")
        
        parent_count = 0
        for window in self.geometry.windows + self.geometry.doors:
            try:
                ifc_elem = self.ifc_cache.get(window.guid)  # N2-FIX
                if not ifc_elem:
                    continue
                
                if hasattr(ifc_elem, 'FillsVoids'):
                    for rel in ifc_elem.FillsVoids:
                        if rel.RelatingOpeningElement:
                            opening = rel.RelatingOpeningElement
                            if hasattr(opening, 'VoidsElements'):
                                for void_rel in opening.VoidsElements:
                                    if void_rel.RelatingBuildingElement:
                                        window.parent_element_guid = void_rel.RelatingBuildingElement.GlobalId
                                        parent_count += 1
                                        break
            except:
                pass
        
        print(f"   {parent_count} Parent-Child-Beziehungen")
    
    def step7_calculate_geometry(self):
        """Step 7: Geometrie - Fläche, Orientierung, Neigung"""
        print("7️⃣  Geometrie berechnen...")
        
        geom_count = 0
        
        # R2-FIX: Erst Slabs/Wände berechnen, dann Roofs
        # Sonst haben Slabs noch area=None wenn IfcRoof sie aggregieren will
        non_roofs = [e for e in self.geometry.all_elements if e.ifc_type != 'IfcRoof']
        roofs = [e for e in self.geometry.all_elements if e.ifc_type == 'IfcRoof']
        
        for elem in non_roofs + roofs:
            try:
                ifc_elem = self.ifc_cache.get(elem.guid)  # N2-FIX
                if not ifc_elem:
                    continue
                
                shape = ifcopenshell.geom.create_shape(self.settings, ifc_elem)
                
                # N1-FIX: Unterschiedliche Logik für Wände vs Slabs
                elem.area = self._calculate_area_mesh(shape, elem.ifc_type)
                elem.orientation, elem.inclination = self._calculate_orientation(shape)
                elem.height = self._calculate_height(shape)
                
                geom_count += 1
                
            except:
                # S4-FIX: Für IfcRoof ohne Geometrie, aggregiere Slab-Flächen
                if elem.ifc_type == 'IfcRoof':
                    elem.area = self._calculate_roof_area_from_slabs(elem.guid)
        
        print(f"   Geometrie für {geom_count} Elemente berechnet")
    
    def step8_validate(self):
        """Step 8: Validierung - DIN 18599 Konsistenz"""
        print("8️⃣  Validierung...")
        
        # R4-FIX: Prüfe TypeObject-Namen statt Element-Namen
        for wall in self.geometry.walls:
            if wall.is_external == False:
                # Prüfe TypeObject-Namen (z.B. "AW 36,5 m. Deckenauflager")
                type_name = wall.properties.get('Pset_CompType', {}).get('TypeName', '')
                if not type_name:
                    # Fallback: Prüfe Reference Property
                    type_name = wall.properties.get('Pset_WallCommon', {}).get('Reference', '')
                
                if 'AW' in type_name or 'Außenwand' in type_name:
                    self.geometry.warnings.append(
                        f"Wand '{wall.name}' (Typ: {type_name}) ist als AW typisiert, aber IsExternal=False"
                    )
        
        zero_u_count = sum(1 for w in self.geometry.walls if w.u_value == 0.0)
        if zero_u_count > 0:
            self.geometry.warnings.append(
                f"{zero_u_count} Wände haben U-Wert = 0.0"
            )
        
        no_geom = sum(1 for e in self.geometry.all_elements if e.area is None)
        if no_geom > 0:
            self.geometry.warnings.append(
                f"{no_geom} Elemente ohne Geometrie"
            )
        
        print(f"   Warnungen: {len(self.geometry.warnings)}")
        
        if self.geometry.warnings:
            print(f"\n   ⚠️  Warnungen:")
            for warning in self.geometry.warnings[:3]:
                print(f"      • {warning}")
    
    def _extract_element_basic(self, ifc_elem) -> Optional[IFCElement]:
        """Extrahiert Basis-Informationen"""
        try:
            guid = ifc_elem.GlobalId
            ifc_type = ifc_elem.is_a()
            name = ifc_elem.Name or f'{ifc_type} {guid[:8]}'
            tag = ifc_elem.Tag if hasattr(ifc_elem, 'Tag') else None
            
            predefined_type = None
            if hasattr(ifc_elem, 'PredefinedType'):
                predefined_type = str(ifc_elem.PredefinedType)
            
            # K5-FIX: Geschoss mit try/except
            storey = None
            try:
                if hasattr(ifc_elem, 'ContainedInStructure'):
                    for rel in ifc_elem.ContainedInStructure:
                        if rel.RelatingStructure.is_a('IfcBuildingStorey'):
                            storey = rel.RelatingStructure.Name
                            break
            except:
                pass
            
            return IFCElement(
                guid=guid,
                ifc_type=ifc_type,
                name=name,
                tag=tag,
                storey=storey,
                predefined_type=predefined_type
            )
            
        except Exception as e:
            return None
    
    def _calculate_area_mesh(self, shape, ifc_type: str) -> Optional[float]:
        """R1-FIX: Korrekte Flächenberechnung - Wände nach Normalenrichtung gruppiert"""
        try:
            verts = shape.geometry.verts
            faces = shape.geometry.faces
            
            if not verts or not faces:
                return None
            
            if 'Wall' in ifc_type:
                # R1-FIX: Für Wände nur eine Seite (nach Normalenrichtung gruppiert)
                # Gruppiere Faces nach Normalenrichtung (z.B. +Y vs -Y)
                faces_by_direction = {}
                
                for i in range(0, len(faces), 3):
                    try:
                        idx1, idx2, idx3 = faces[i]*3, faces[i+1]*3, faces[i+2]*3
                        v1 = (verts[idx1], verts[idx1+1], verts[idx1+2])
                        v2 = (verts[idx2], verts[idx2+1], verts[idx2+2])
                        v3 = (verts[idx3], verts[idx3+1], verts[idx3+2])
                        
                        # Berechne Normale
                        v1v2 = (v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2])
                        v1v3 = (v3[0]-v1[0], v3[1]-v1[1], v3[2]-v1[2])
                        nx = v1v2[1]*v1v3[2] - v1v2[2]*v1v3[1]
                        ny = v1v2[2]*v1v3[0] - v1v2[0]*v1v3[2]
                        nz = v1v2[0]*v1v3[1] - v1v2[1]*v1v3[0]
                        length = (nx**2 + ny**2 + nz**2)**0.5
                        
                        if length == 0:
                            continue
                        
                        nx_norm = nx / length
                        ny_norm = ny / length
                        nz_norm = nz / length
                        
                        # Nur Seitenflächen (horizontale Normale)
                        if abs(nz_norm) > 0.1:
                            continue
                        
                        # Gruppiere nach Normalenrichtung (gerundet auf 0.1)
                        direction_key = (round(nx_norm, 1), round(ny_norm, 1))
                        
                        if direction_key not in faces_by_direction:
                            faces_by_direction[direction_key] = []
                        
                        # Heron's Formel
                        a = ((v2[0]-v1[0])**2 + (v2[1]-v1[1])**2 + (v2[2]-v1[2])**2)**0.5
                        b = ((v3[0]-v2[0])**2 + (v3[1]-v2[1])**2 + (v3[2]-v2[2])**2)**0.5
                        c = ((v1[0]-v3[0])**2 + (v1[1]-v3[1])**2 + (v1[2]-v3[2])**2)**0.5
                        
                        s = (a + b + c) / 2
                        if s > a and s > b and s > c:
                            face_area = (s*(s-a)*(s-b)*(s-c))**0.5
                            faces_by_direction[direction_key].append(face_area)
                    except:
                        pass
                
                # R1-FIX: Nimm die größte Richtungsgruppe (meist Außenseite)
                # Bei geclippten Wänden ist das die korrekte Einzelfläche
                if faces_by_direction:
                    max_direction = max(faces_by_direction.items(), key=lambda x: sum(x[1]))
                    total_area = sum(max_direction[1])
                    return round(total_area, 2) if total_area > 0 else None
                
                return None
            
            else:
                # Für Slabs/Dächer: Summiere alle Faces
                total_area = 0.0
                for i in range(0, len(faces), 3):
                    try:
                        idx1, idx2, idx3 = faces[i]*3, faces[i+1]*3, faces[i+2]*3
                        v1 = (verts[idx1], verts[idx1+1], verts[idx1+2])
                        v2 = (verts[idx2], verts[idx2+1], verts[idx2+2])
                        v3 = (verts[idx3], verts[idx3+1], verts[idx3+2])
                        
                        a = ((v2[0]-v1[0])**2 + (v2[1]-v1[1])**2 + (v2[2]-v1[2])**2)**0.5
                        b = ((v3[0]-v2[0])**2 + (v3[1]-v2[1])**2 + (v3[2]-v2[2])**2)**0.5
                        c = ((v1[0]-v3[0])**2 + (v1[1]-v3[1])**2 + (v1[2]-v3[2])**2)**0.5
                        
                        s = (a + b + c) / 2
                        if s > a and s > b and s > c:
                            total_area += (s*(s-a)*(s-b)*(s-c))**0.5
                    except:
                        pass
                
                return round(total_area, 2) if total_area > 0 else None
            
        except:
            return None
    
    def _calculate_orientation(self, shape) -> Tuple[Optional[float], Optional[float]]:
        """Berechnet Orientierung und Neigung"""
        try:
            verts = shape.geometry.verts
            if not verts or len(verts) < 9:
                return None, None
            
            p1 = (verts[0], verts[1], verts[2])
            p2 = (verts[3], verts[4], verts[5])
            p3 = (verts[6], verts[7], verts[8])
            
            v1 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
            v2 = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2])
            
            nx = v1[1] * v2[2] - v1[2] * v2[1]
            ny = v1[2] * v2[0] - v1[0] * v2[2]
            nz = v1[0] * v2[1] - v1[1] * v2[0]
            
            length = math.sqrt(nx**2 + ny**2 + nz**2)
            if length == 0:
                return None, None
            
            nx, ny, nz = nx/length, ny/length, nz/length
            
            orientation = math.degrees(math.atan2(nx, ny))
            if orientation < 0:
                orientation += 360
            
            inclination = math.degrees(math.acos(abs(nz)))
            
            return round(orientation, 1), round(inclination, 1)
            
        except:
            return None, None
    
    def _calculate_height(self, shape) -> Optional[float]:
        """Berechnet Höhe"""
        try:
            verts = shape.geometry.verts
            if not verts:
                return None
            
            zs = [verts[i] for i in range(2, len(verts), 3)]
            height = max(zs) - min(zs)
            
            return round(height, 2) if height > 0 else None
            
        except:
            return None
    
    def _calculate_roof_area_from_slabs(self, roof_guid: str) -> Optional[float]:
        """S4-FIX: Aggregiere Fläche aus zugehörigen Slabs"""
        try:
            roof_ifc = self.ifc_cache.get(roof_guid)
            if not roof_ifc or not hasattr(roof_ifc, 'IsDecomposedBy'):
                return None
            
            total_area = 0.0
            for rel in roof_ifc.IsDecomposedBy:
                for elem in rel.RelatedObjects:
                    if elem.is_a('IfcSlab'):
                        # Finde Slab in geometry.roofs
                        for slab in self.geometry.roofs:
                            if slab.guid == elem.GlobalId and slab.area:
                                total_area += slab.area
            
            return round(total_area, 2) if total_area > 0 else None
            
        except:
            return None


def parse_ifc_file(ifc_file_path: str) -> Dict[str, Any]:
    """
    Parst IFC-Datei mit 8-Schritte-Pipeline
    """
    parser = IFCParser(ifc_file_path)
    geometry = parser.parse()
    
    # M3-FIX: predefined_type im JSON
    def element_to_dict(elem: IFCElement) -> Dict[str, Any]:
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
            "parent_element_guid": elem.parent_element_guid,
            "predefined_type": elem.predefined_type,
            "is_external": elem.is_external,
            "u_value": elem.u_value,
            "properties": elem.properties
        }
    
    return {
        "project_name": geometry.project_name,
        "building_name": geometry.building_name,
        "building_guid": geometry.building_guid,
        "storeys": geometry.storeys,
        "spaces": geometry.spaces,
        "walls": [element_to_dict(e) for e in geometry.walls],
        "roofs": [element_to_dict(e) for e in geometry.roofs],
        "floors": [element_to_dict(e) for e in geometry.slabs],
        "windows": [element_to_dict(e) for e in geometry.windows],
        "doors": [element_to_dict(e) for e in geometry.doors],
        "all_elements": [element_to_dict(e) for e in geometry.all_elements],
        "material_layers": geometry.material_layers,
        "warnings": geometry.warnings,
        "errors": geometry.errors
    }
