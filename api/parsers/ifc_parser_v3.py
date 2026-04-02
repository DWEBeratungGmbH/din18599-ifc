"""
IFC Parser v3.2 - Schema v2.3 konform mit DIN 18599 Beiblatt 3

8-Schritte-Pipeline: für DIN18599 Sidecar Generator

Angepasst an Schema v2.3:
P1: Output-Format → Schema v2.3 (envelope.walls/roofs/floors/windows/doors)
P2: din_code ableiten (Bauteiltyp + boundary_condition + inclination)
P3: boundary_condition ableiten (is_external + Z-Position + Storey-Name)
P4: fx_factor ableiten (exterior=1.0, ground=0.6, unheated=0.8/0.5)
P5: Zone-Geometrie berechnen (IfcSpace: area, volume, height)
P6: room_ref zuordnen (Element → Room via IfcRelSpaceBoundary)
S4: Slab-Fläche nur Oberseite (nz-Filter)
"""

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import math
import logging

# Logging statt print für Produktionscode
logger = logging.getLogger(__name__)

try:
    from .ifc_material_extractor import extract_material_layers, layer_structure_to_dict
    HAS_MATERIAL_EXTRACTOR = True
except ImportError:
    HAS_MATERIAL_EXTRACTOR = False
    logger.warning("ifc_material_extractor nicht gefunden - Schichtaufbauten werden übersprungen")


# ============================================================
# P4: Fx-Faktor Defaults nach DIN 18599-2
# ============================================================
FX_DEFAULTS = {
    "exterior": 1.0,
    "ground": 0.6,        # DIN 18599-2, vereinfacht
    "unheated": 0.5,      # Keller/Dachboden, konservativ
    "adjacent": 0.0,      # Andere Zone, kein Wärmeverlust nach außen
}

# P4: Differenziertere Fx-Werte nach Bauteiltyp
FX_UNHEATED_BY_TYPE = {
    "DA": 0.8,   # Dach → unbeheizter Dachraum
    "DU": 0.8,
    "BA": 1.0,   # Boden an Außenluft (Pilotis)
    "BU": 0.5,   # Boden → unbeheizter Keller
    "WU": 0.5,   # Wand → unbeheizter Bereich
}


@dataclass
class IFCElement:
    """Einzelnes Bauteil mit allen Attributen"""
    guid: str
    ifc_type: str
    name: str
    tag: Optional[str] = None
    predefined_type: Optional[str] = None
    
    # Geometrie
    area: Optional[float] = None
    orientation: Optional[float] = None  # Azimut [0-360°]
    inclination: Optional[float] = None  # Neigung [0-90°]
    
    # Material/Konstruktion
    u_value: Optional[float] = None
    material_name: Optional[str] = None
    
    # Beziehungen
    storey_guid: Optional[str] = None
    parent_element_guid: Optional[str] = None  # Für Fenster/Türen
    
    # Properties
    properties: Dict[str, Any] = field(default_factory=dict)
    is_external: Optional[bool] = None
    
    # Abgeleitete Werte (P2-P6)
    boundary_condition: Optional[str] = None  # P3
    din_code: Optional[str] = None            # P2
    fx_factor: Optional[float] = None         # P4
    room_ref: Optional[str] = None            # K3: room_ref (IfcSpace GUID), nicht zone_ref
    # Z-Position für boundary_condition Ableitung
    z_min: Optional[float] = None


@dataclass
class IFCGeometry:
    """Vollständige IFC-Geometrie für Schema v2.3"""
    schema: str = ""
    project_name: str = ""
    site_name: Optional[str] = None
    building_name: Optional[str] = None
    building_guid: Optional[str] = None
    latitude: Optional[float] = None   # P2: Breitengrad
    longitude: Optional[float] = None  # P2: Längengrad

    storeys: List[Dict[str, Any]] = field(default_factory=list)
    spaces: List[Dict[str, Any]] = field(default_factory=list)   # P5: erweitert

    walls: List[IFCElement] = field(default_factory=list)
    roofs: List[IFCElement] = field(default_factory=list)
    slabs: List[IFCElement] = field(default_factory=list)
    windows: List[IFCElement] = field(default_factory=list)
    doors: List[IFCElement] = field(default_factory=list)
    all_elements: List[IFCElement] = field(default_factory=list)

    material_layers: List[Dict[str, Any]] = field(default_factory=list)

    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class IFCParser:
    """8-Schritte IFC Parser für DIN 18599 Schema v2.2"""

    def __init__(self, ifc_file_path: str):
        self.ifc_file = ifcopenshell.open(ifc_file_path)
        self.settings = ifcopenshell.geom.settings()
        self.settings.set(self.settings.USE_WORLD_COORDS, True)
        self.geometry = IFCGeometry()
        self.ifc_cache: Dict[str, Any] = {}

    def parse(self) -> IFCGeometry:
        """Führt alle 8 Schritte aus"""
        logger.info("IFC PARSER v3 - 8-Schritte-Pipeline")

        self.step1_header()
        self.step2_spatial_structure()
        self.step3_collect_elements()
        self.step4_extract_properties()
        self.step5_extract_materials()
        self.step6_extract_relationships()
        self.step7_calculate_geometry()
        # P2-P4: Neue Ableitungsschritte NACH Geometrie
        self._derive_boundary_conditions()   # P3
        self._derive_din_codes()             # P2
        self._derive_fx_factors()            # P4
        self._derive_room_refs()             # P6
        self.step8_validate()

        logger.info("PARSING ABGESCHLOSSEN")
        return self.geometry

    # ============================================================
    # STEP 1: Header
    # ============================================================
    def step1_header(self):
        """Step 1: Header - Schema, Projekt, Software"""
        logger.info("Step 1: Header...")

        project = self.ifc_file.by_type('IfcProject')[0]
        self.geometry.schema = self.ifc_file.schema
        self.geometry.project_name = project.Name or "Unbekannt"

        buildings = self.ifc_file.by_type('IfcBuilding')
        if buildings:
            self.geometry.building_name = buildings[0].Name
            self.geometry.building_guid = buildings[0].GlobalId
        
        # P2: IfcSite Geodaten extrahieren
        sites = self.ifc_file.by_type('IfcSite')
        if sites:
            site = sites[0]
            self.geometry.site_name = site.Name
            # RefLatitude/RefLongitude sind Tuples: (degrees, minutes, seconds, [millionths])
            if hasattr(site, 'RefLatitude') and site.RefLatitude:
                self.geometry.latitude = self._parse_ifc_latlong(site.RefLatitude)
            if hasattr(site, 'RefLongitude') and site.RefLongitude:
                self.geometry.longitude = self._parse_ifc_latlong(site.RefLongitude)

    # ============================================================
    # STEP 2: Räumliche Struktur + P5 Zone-Geometrie
    # ============================================================
    def step2_spatial_structure(self):
        """Step 2: Geschosse, Räume mit Geometrie (P5)"""
        logger.info("Step 2: Räumliche Struktur...")

        for storey in self.ifc_file.by_type('IfcBuildingStorey'):
            self.geometry.storeys.append({
                'id': storey.GlobalId,
                'name': storey.Name,
                'elevation': storey.Elevation if hasattr(storey, 'Elevation') else None,
            })

        # P5: Zone-Geometrie aus IfcSpace berechnen
        for space in self.ifc_file.by_type('IfcSpace'):
            space_data = {
                'id': space.GlobalId,
                'ifc_guid': space.GlobalId,
                'name': space.Name or 'Unnamed',
                'area': None,
                'volume': None,
                'height': None,
                'storey_ref': None,
            }

            # P5: Storey-Zuordnung
            try:
                if hasattr(space, 'ContainedInStructure') and space.ContainedInStructure:
                    for rel in space.ContainedInStructure:
                        if rel.RelatingStructure.is_a('IfcBuildingStorey'):
                            space_data['storey_ref'] = rel.RelatingStructure.GlobalId
                            break
                else:
                    # B3: Fallback - Suche über Decomposes
                    if hasattr(space, 'Decomposes'):
                        for rel in space.Decomposes:
                            if hasattr(rel, 'RelatingObject') and rel.RelatingObject.is_a('IfcBuildingStorey'):
                                space_data['storey_ref'] = rel.RelatingObject.GlobalId
                                logger.debug(f"Space {space.Name}: storey_ref via Decomposes")
                                break
            except (AttributeError, TypeError) as e:
                logger.debug(f"Space {space.Name}: storey_ref Fehler: {e}")

            # P5: Geometrie aus IfcElementQuantity (bevorzugt)
            try:
                psets = ifcopenshell.util.element.get_psets(space)
                for pset_name, pset_vals in psets.items():
                    if 'Qto' in pset_name or 'Quantity' in pset_name or 'BaseQuantities' in pset_name:
                        if 'NetFloorArea' in pset_vals:
                            space_data['area'] = round(pset_vals['NetFloorArea'], 2)
                        elif 'GrossFloorArea' in pset_vals:
                            space_data['area'] = round(pset_vals['GrossFloorArea'], 2)
                        if 'NetVolume' in pset_vals:
                            space_data['volume'] = round(pset_vals['NetVolume'], 2)
                        elif 'GrossVolume' in pset_vals:
                            space_data['volume'] = round(pset_vals['GrossVolume'], 2)
                        if 'Height' in pset_vals:
                            space_data['height'] = round(pset_vals['Height'], 2)
            except Exception as e:
                logger.debug(f"Quantity-Extraktion für Space {space.Name}: {e}")

            # P5: Fallback - Geometrie aus Shape berechnen
            if space_data['area'] is None or space_data['volume'] is None:
                try:
                    shape = ifcopenshell.geom.create_shape(self.settings, space)
                    verts = shape.geometry.verts
                    if verts:
                        xs = [verts[i] for i in range(0, len(verts), 3)]
                        ys = [verts[i] for i in range(1, len(verts), 3)]
                        zs = [verts[i] for i in range(2, len(verts), 3)]

                        if space_data['height'] is None:
                            height_calc = round(max(zs) - min(zs), 2)
                            # B2: Plausibilitätsprüfung
                            if height_calc < 50.0:
                                space_data['height'] = height_calc
                            else:
                                logger.warning(f"Space {space.Name}: height={height_calc}m unrealistisch, verworfen")

                        # Fläche aus Mesh-Oberseite (nz > 0.9)
                        if space_data['area'] is None:
                            faces = shape.geometry.faces
                            top_area = self._sum_faces_by_normal(
                                verts, faces, nz_min=0.9
                            )
                            if top_area and top_area > 0:
                                space_data['area'] = round(top_area, 2)

                        if space_data['volume'] is None and space_data['area'] and space_data['height']:
                            volume_calc = round(space_data['area'] * space_data['height'], 2)
                            # B2: Plausibilitätsprüfung
                            if volume_calc < 10000.0:
                                space_data['volume'] = volume_calc
                            else:
                                logger.warning(f"Space {space.Name}: volume={volume_calc}m³ unrealistisch, verworfen")
                except Exception as e:
                    logger.debug(f"Shape-Extraktion für Space {space.Name}: {e}")

            self.geometry.spaces.append(space_data)

        logger.info(f"   Geschosse: {len(self.geometry.storeys)}, Räume: {len(self.geometry.spaces)}")

    # ============================================================
    # STEP 3: Bauteile inventarisieren
    # ============================================================
    def step3_collect_elements(self):
        """Step 3: Bauteile sammeln + GUID-Cache aufbauen"""
        logger.info("Step 3: Bauteile sammeln...")

        for wall in self.ifc_file.by_type('IfcWall'):
            elem = self._extract_element_basic(wall)
            if elem:
                self.ifc_cache[elem.guid] = wall
                self.geometry.walls.append(elem)
                self.geometry.all_elements.append(elem)

        for roof in self.ifc_file.by_type('IfcRoof'):
            elem = self._extract_element_basic(roof)
            if elem:
                self.ifc_cache[elem.guid] = roof
                self.geometry.roofs.append(elem)
                self.geometry.all_elements.append(elem)

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

        logger.info(
            f"   W:{len(self.geometry.walls)} R:{len(self.geometry.roofs)} "
            f"S:{len(self.geometry.slabs)} F:{len(self.geometry.windows)} T:{len(self.geometry.doors)}"
        )

    # ============================================================
    # STEP 4: Properties
    # ============================================================
    def step4_extract_properties(self):
        """Step 4: IsExternal, U-Werte, Psets"""
        logger.info("Step 4: Properties...")

        count = 0
        for elem in self.geometry.all_elements:
            try:
                ifc_elem = self.ifc_cache.get(elem.guid)
                if not ifc_elem:
                    continue

                psets = ifcopenshell.util.element.get_psets(ifc_elem)

                # IsExternal + U-Wert aus typspezifischem Pset
                for pset_key in ('Pset_WallCommon', 'Pset_SlabCommon',
                                 'Pset_RoofCommon', 'Pset_WindowCommon',
                                 'Pset_DoorCommon'):
                    if pset_key in psets:
                        if elem.is_external is None:
                            elem.is_external = psets[pset_key].get('IsExternal')
                        if elem.u_value is None:
                            elem.u_value = psets[pset_key].get('ThermalTransmittance')

                elem.properties = psets
                count += 1

            except Exception as e:
                logger.debug(f"Properties für {elem.guid}: {e}")

        logger.info(f"   Properties für {count} Elemente")

    # ============================================================
    # STEP 5: Materialien
    # ============================================================
    def step5_extract_materials(self):
        """Step 5: Materialien und Schichten"""
        logger.info("Step 5: Materialien...")

        for elem in self.geometry.all_elements:
            try:
                ifc_elem = self.ifc_cache.get(elem.guid)
                if not ifc_elem:
                    continue

                if hasattr(ifc_elem, 'HasAssociations'):
                    for assoc in ifc_elem.HasAssociations:
                        if assoc.is_a('IfcRelAssociatesMaterial'):
                            mat = assoc.RelatingMaterial
                            if hasattr(mat, 'Name'):
                                elem.material = mat.Name

                if HAS_MATERIAL_EXTRACTOR:
                    layer_structure = extract_material_layers(ifc_elem, self.ifc_file)
                    if layer_structure:
                        layer_dict = layer_structure_to_dict(layer_structure)
                        layer_dict['element_guid'] = elem.guid
                        self.geometry.material_layers.append(layer_dict)

            except Exception as e:
                logger.debug(f"Material für {elem.guid}: {e}")

    # ============================================================
    # STEP 6: Beziehungen
    # ============================================================
    def step6_extract_relationships(self):
        """Step 6: Parent-Child (Fenster/Tür → Wand)"""
        logger.info("Step 6: Beziehungen...")

        count = 0
        for child in self.geometry.windows + self.geometry.doors:
            try:
                ifc_elem = self.ifc_cache.get(child.guid)
                if not ifc_elem or not hasattr(ifc_elem, 'FillsVoids'):
                    continue

                for rel in ifc_elem.FillsVoids:
                    opening = rel.RelatingOpeningElement
                    if opening and hasattr(opening, 'VoidsElements'):
                        for void_rel in opening.VoidsElements:
                            if void_rel.RelatingBuildingElement:
                                child.parent_element_guid = void_rel.RelatingBuildingElement.GlobalId
                                count += 1
                                break
            except Exception as e:
                logger.debug(f"Beziehung für {child.guid}: {e}")

        logger.info(f"   {count} Parent-Child-Beziehungen")

    # ============================================================
    # STEP 7: Geometrie
    # ============================================================
    def step7_calculate_geometry(self):
        """Step 7: Fläche, Orientierung, Neigung, Z-Position"""
        logger.info("Step 7: Geometrie...")

        # R2-FIX: Erst Slabs/Wände, dann Roofs
        non_roofs = [e for e in self.geometry.all_elements if e.ifc_type != 'IfcRoof']
        roofs_only = [e for e in self.geometry.all_elements if e.ifc_type == 'IfcRoof']
        count = 0

        for elem in non_roofs + roofs_only:
            try:
                ifc_elem = self.ifc_cache.get(elem.guid)
                if not ifc_elem:
                    continue

                # P1: Fläche primär aus IfcElementQuantity (genauer als Mesh)
                elem.area = self._extract_area_from_quantities(ifc_elem, elem.ifc_type, elem.predefined_type)

                # Fallback: Mesh-Berechnung wenn Quantity fehlt
                if elem.area is None:
                    shape = ifcopenshell.geom.create_shape(self.settings, ifc_elem)
                    verts = shape.geometry.verts
                    faces = shape.geometry.faces

                    if not verts or not faces:
                        continue

                    # Fläche berechnen
                    if 'Wall' in elem.ifc_type:
                        elem.area = self._calculate_wall_area(verts, faces)
                    elif 'Slab' in elem.ifc_type or 'Roof' in elem.ifc_type:
                        # S4: Nur Oberseite für Slabs (nz > 0.9), alle Faces für Roof-Slabs
                        if elem.predefined_type == 'FLOOR' or elem.predefined_type == 'BASESLAB':
                            top_area = self._sum_faces_by_normal(verts, faces, nz_min=0.9)
                            elem.area = round(top_area, 2) if top_area else None
                        else:
                            elem.area = self._calculate_total_surface(verts, faces)
                    else:
                        elem.area = self._calculate_total_surface(verts, faces)
                else:
                    # Für Orientierung/Neigung brauchen wir trotzdem Shape
                    shape = ifcopenshell.geom.create_shape(self.settings, ifc_elem)
                    verts = shape.geometry.verts
                    faces = shape.geometry.faces

                    if not verts or not faces:
                        continue

                # Orientierung + Neigung
                elem.orientation, elem.inclination = self._calculate_orientation(shape)

                # Höhe
                zs = [verts[i] for i in range(2, len(verts), 3)]
                elem.height = round(max(zs) - min(zs), 2) if zs else None

                # P3: Z-Position speichern für boundary_condition Ableitung
                elem.z_min = round(min(zs), 2) if zs else None

                count += 1

            except Exception as e:
                # S4-FIX: Für IfcRoof ohne eigene Geometrie
                if elem.ifc_type == 'IfcRoof':
                    elem.area = self._calculate_roof_area_from_slabs(elem.guid)
                else:
                    logger.debug(f"Geometrie für {elem.name}: {e}")

        logger.info(f"   Geometrie für {count} Elemente")

    # ============================================================
    # P3: boundary_condition ableiten
    # ============================================================
    def _derive_boundary_conditions(self):
        """P3: Leite boundary_condition ab aus is_external + Z-Position + Storey + TypeName"""
        logger.info("   P3: boundary_conditions ableiten...")

        # P1: Counter für aggregierte Warnungen
        aw_false_count = 0
        window_door_false_count = 0

        for elem in self.geometry.all_elements:
            # B4: TypeName-Heuristik wenn IsExternal fehlt
            type_name = elem.properties.get('Pset_CompType', {}).get('TypeName', '')
            if not type_name:
                type_name = elem.properties.get('Pset_WallCommon', {}).get('Reference', '')
            
            # P2: Keller-Boden Heuristik (vor IsExternal-Check)
            if elem.ifc_type == 'IfcSlab' and elem.predefined_type in ('BASESLAB', 'FLOOR'):
                # Lookup Storey für Keller-Erkennung
                storey_name = ""
                storey_elevation = None
                if elem.storey_guid:
                    for s in self.geometry.storeys:
                        if s['id'] == elem.storey_guid:
                            storey_name = s.get('name', '')
                            storey_elevation = s.get('elevation')
                            break
                
                # Keller-Heuristik: Name enthält "Keller" ODER Elevation < 0
                is_basement = 'keller' in storey_name.lower() or (storey_elevation is not None and storey_elevation < 0)
                
                if is_basement:
                    elem.boundary_condition = "ground"
                    continue
                # Fallback: IsExternal=True UND z_min <= 0.1
                elif elem.is_external is True and elem.z_min is not None and elem.z_min <= 0.1:
                    elem.boundary_condition = "ground"
                    continue
            
            if elem.is_external is True:
                elem.boundary_condition = "exterior"

            elif elem.is_external is False:
                # B4: Fenster/Türen sind semantisch immer exterior
                if elem.ifc_type in ('IfcWindow', 'IfcDoor'):
                    elem.boundary_condition = "exterior"
                    window_door_false_count += 1
                # B4: Korrektur wenn TypeName "AW" enthält
                elif 'AW' in type_name or 'Außenwand' in type_name or 'Aussenwand' in type_name:
                    elem.boundary_condition = "exterior"
                    aw_false_count += 1
                else:
                    # Prüfe ob unbeheizt (Keller, Dachboden) via storey_guid Lookup
                    storey_name = ""
                    if elem.storey_guid:
                        for s in self.geometry.storeys:
                            if s['id'] == elem.storey_guid:
                                storey_name = s.get('name', '')
                                break
                    storey_lower = storey_name.lower()
                    if any(kw in storey_lower for kw in ('keller', 'unbeheizt', 'garage', 'dachboden')):
                        elem.boundary_condition = "unheated"
                    else:
                        elem.boundary_condition = "adjacent"
            else:
                # B4: Kein IsExternal → TypeName-Heuristik
                if 'AW' in type_name or 'Außenwand' in type_name or 'Aussenwand' in type_name:
                    elem.boundary_condition = "exterior"
                    logger.debug(f"{elem.name}: IsExternal=None, TypeName={type_name} → exterior")
                elif elem.ifc_type in ('IfcWindow', 'IfcDoor'):
                    # Fenster/Türen default exterior
                    elem.boundary_condition = "exterior"
                elif elem.z_min is not None and elem.z_min <= 0.1:
                    elem.boundary_condition = "ground"
                else:
                    elem.boundary_condition = "exterior"

        # P1: Aggregierte Warnungen (statt 39 einzelne)
        if aw_false_count > 0:
            self.geometry.warnings.append(
                f"{aw_false_count} Wände mit AW-Typ haben IsExternal=False (automatisch auf exterior korrigiert)"
            )
        if window_door_false_count > 0:
            logger.debug(f"{window_door_false_count} Fenster/Türen mit IsExternal=False → exterior")

    # ============================================================
    # P2: din_code ableiten
    # ============================================================
    def _derive_din_codes(self):
        """P2: Leite DIN 18599 Bauteilcode ab (Beiblatt 3)"""
        logger.info("   P2: DIN-Codes ableiten...")

        # Mapping: Bauteiltyp-Buchstabe
        TYPE_MAP = {
            'IfcWall': 'W', 'IfcWallStandardCase': 'W',
            'IfcSlab': 'B',  # Boden (default, wird ggf. zu D)
            'IfcRoof': 'D',
            'IfcWindow': 'F',
            'IfcDoor': 'T',
        }

        # Mapping: Randbedingung-Buchstabe
        BOUNDARY_MAP = {
            'exterior': 'A',
            'ground': 'E',
            'unheated': 'U',
            'adjacent': 'Z',
        }

        for elem in self.geometry.all_elements:
            type_char = TYPE_MAP.get(elem.ifc_type, '?')

            # Slab-Differenzierung: Dach (D) vs. Boden (B)
            if elem.ifc_type == 'IfcSlab':
                if elem.predefined_type == 'ROOF':
                    type_char = 'D'
                elif elem.predefined_type == 'BASESLAB':
                    type_char = 'B'
                else:
                    # Heuristik: Neigung > 45° → eher Dach
                    if elem.inclination is not None and elem.inclination > 45:
                        type_char = 'D'

            # Fenster-Differenzierung: FA vs FD vs FL
            if elem.ifc_type == 'IfcWindow' and elem.boundary_condition == 'exterior':
                if elem.inclination is not None:
                    if elem.inclination >= 60:
                        type_char = 'F'   # FA = Wandfenster
                    elif elem.inclination >= 22:
                        # Dachflächenfenster → Code FD
                        elem.din_code = "FD"
                        continue
                    else:
                        # Lichtkuppel → Code FL
                        elem.din_code = "FL"
                        continue

            bc_char = BOUNDARY_MAP.get(elem.boundary_condition, 'A')
            elem.din_code = f"{type_char}{bc_char}"

    # ============================================================
    # P4: fx_factor ableiten
    # ============================================================
    def _derive_fx_factors(self):
        """P4: Leite Fx-Korrekturfaktor ab"""
        logger.info("   P4: Fx-Faktoren ableiten...")

        for elem in self.geometry.all_elements:
            bc = elem.boundary_condition or "exterior"

            if bc == "unheated" and elem.din_code in FX_UNHEATED_BY_TYPE:
                elem.fx_factor = FX_UNHEATED_BY_TYPE[elem.din_code]
            else:
                elem.fx_factor = FX_DEFAULTS.get(bc, 1.0)

    # ============================================================
    # P6: room_ref zuordnen
    # ============================================================
    def _derive_room_refs(self):
        """P6: Ordne Elemente Räumen zu via IfcRelSpaceBoundary"""
        logger.info("   P6: Room-Referenzen zuordnen...")

        # Versuch 1: IfcRelSpaceBoundary (ideal)
        boundary_count = 0
        for rel in self.ifc_file.by_type('IfcRelSpaceBoundary'):
            try:
                space_guid = rel.RelatingSpace.GlobalId
                elem_guid = rel.RelatedBuildingElement.GlobalId if rel.RelatedBuildingElement else None
                if elem_guid:
                    for elem in self.geometry.all_elements:
                        if elem.guid == elem_guid and elem.room_ref is None:
                            elem.room_ref = space_guid
                            boundary_count += 1
            except (AttributeError, TypeError):
                continue

        if boundary_count > 0:
            logger.info(f"   {boundary_count} room_refs via SpaceBoundary")
            return

        # Versuch 2: Fallback - gleicher Storey + gleicher Raum (heuristisch)
        logger.info("   Keine SpaceBoundary → Fallback: Storey-basiert")
        storey_to_space: Dict[str, str] = {}
        for space in self.geometry.spaces:
            sr = space.get('storey_ref')
            if sr and sr not in storey_to_space:
                storey_to_space[sr] = space['id']

        for elem in self.geometry.all_elements:
            if elem.room_ref is None and elem.storey_guid:
                elem.room_ref = storey_to_space.get(elem.storey_guid)

    # ============================================================
    # STEP 8: Validierung
    # ============================================================
    def step8_validate(self):
        """Step 8: DIN 18599 Konsistenzprüfung"""
        logger.info("Step 8: Validierung...")

        # R4-FIX: TypeObject-basierte AW/IW Prüfung
        for wall in self.geometry.walls:
            if wall.is_external is False:
                type_name = wall.properties.get('Pset_CompType', {}).get('TypeName', '')
                if not type_name:
                    type_name = wall.properties.get('Pset_WallCommon', {}).get('Reference', '')
                if 'AW' in type_name or 'Außenwand' in type_name or 'Aussenwand' in type_name:
                    self.geometry.warnings.append(
                        f"Wand '{wall.name}' (Typ: {type_name}) ist AW-typisiert, aber IsExternal=False"
                    )

        # U-Wert Prüfung
        zero_u = sum(1 for w in self.geometry.walls if w.u_value == 0.0)
        if zero_u > 0:
            self.geometry.warnings.append(f"{zero_u} Wände mit U-Wert = 0.0")

        # Geometrie-Prüfung
        no_geom = sum(1 for e in self.geometry.all_elements if e.area is None)
        if no_geom > 0:
            self.geometry.warnings.append(f"{no_geom} Elemente ohne Flächenberechnung")

        # P5: Rooms-Prüfung
        rooms_without_volume = sum(
            1 for s in self.geometry.spaces if s.get('volume') is None
        )
        if rooms_without_volume > 0:
            self.geometry.warnings.append(f"{rooms_without_volume} Rooms ohne Volumen")

        # SpaceBoundary-Prüfung
        sb_count = len(self.ifc_file.by_type('IfcRelSpaceBoundary'))
        if sb_count == 0:
            self.geometry.warnings.append("Keine IfcRelSpaceBoundary (room_ref ist heuristisch)")

        # BASESLAB-Prüfung
        has_baseslab = any(
            e.predefined_type == 'BASESLAB' for e in self.geometry.slabs
        )
        if not has_baseslab:
            self.geometry.warnings.append("Keine Bodenplatte (BASESLAB) gefunden")

        logger.info(f"   {len(self.geometry.warnings)} Warnungen")

    # ============================================================
    # Hilfsmethoden
    # ============================================================
    def _extract_area_from_quantities(self, ifc_elem, ifc_type: str, predefined_type: Optional[str]) -> Optional[float]:
        """P1: Extrahiere Fläche aus IfcElementQuantity (genauer als Mesh)"""
        try:
            # P4: Fenster/Türen - OverallHeight × OverallWidth (direkt am Element)
            if 'Window' in ifc_type or 'Door' in ifc_type:
                if hasattr(ifc_elem, 'OverallHeight') and hasattr(ifc_elem, 'OverallWidth'):
                    if ifc_elem.OverallHeight and ifc_elem.OverallWidth:
                        area = ifc_elem.OverallHeight * ifc_elem.OverallWidth
                        logger.debug(f"{ifc_type} {ifc_elem.Name}: {ifc_elem.OverallHeight}×{ifc_elem.OverallWidth} = {area:.2f}m²")
                        return round(area, 2)
            
            # Für andere Elemente: Suche in Quantity-Sets
            psets = ifcopenshell.util.element.get_psets(ifc_elem)
            
            for pset_name, pset_vals in psets.items():
                if not ('Qto' in pset_name or 'Quantity' in pset_name or 'BaseQuantities' in pset_name):
                    continue
                
                # Wände: Wandfläche (berücksichtigt Dachschnitte)
                if 'Wall' in ifc_type:
                    if 'NetSideArea' in pset_vals:
                        area = pset_vals['NetSideArea']
                        # V4: Plausibilitätsprüfung (analog zu B2 bei Spaces)
                        if area > 200:
                            logger.warning(f"Wand {ifc_elem.Name}: NetSideArea={area}m² unrealistisch, verworfen")
                            return None
                        return round(area, 2)
                    elif 'GrossSideArea' in pset_vals:
                        area = pset_vals['GrossSideArea']
                        if area > 200:
                            logger.warning(f"Wand {ifc_elem.Name}: GrossSideArea={area}m² unrealistisch, verworfen")
                            return None
                        return round(area, 2)
                    elif 'Wandfläche' in pset_vals:  # CASCADOS custom
                        area = pset_vals['Wandfläche']
                        if area > 200:
                            logger.warning(f"Wand {ifc_elem.Name}: Wandfläche={area}m² unrealistisch, verworfen")
                            return None
                        return round(area, 2)
                
                # Slabs/Roofs: Nettofläche
                elif 'Slab' in ifc_type or 'Roof' in ifc_type:
                    if predefined_type in ('FLOOR', 'BASESLAB'):
                        # Bodenfläche
                        if 'NetArea' in pset_vals:
                            return round(pset_vals['NetArea'], 2)
                        elif 'GrossArea' in pset_vals:
                            return round(pset_vals['GrossArea'], 2)
                    else:
                        # Dachfläche
                        if 'NetArea' in pset_vals:
                            return round(pset_vals['NetArea'], 2)
                        elif 'GrossArea' in pset_vals:
                            return round(pset_vals['GrossArea'], 2)
            
            return None
            
        except Exception as e:
            logger.debug(f"Quantity-Extraktion für {ifc_elem.GlobalId}: {e}")
            return None
    
    def _parse_ifc_latlong(self, coords: Tuple) -> Optional[float]:
        """P2: Parse IFC LatLong Tuple (degrees, minutes, seconds, [millionths]) zu Dezimalgrad"""
        try:
            if not coords or len(coords) < 3:
                return None
            
            degrees = coords[0]
            minutes = coords[1]
            seconds = coords[2]
            
            # Millionths optional (IFC2X3 vs IFC4)
            if len(coords) > 3 and coords[3]:
                seconds += coords[3] / 1000000.0
            
            # Dezimalgrad berechnen
            decimal = abs(degrees) + minutes / 60.0 + seconds / 3600.0
            
            # Vorzeichen
            if degrees < 0:
                decimal = -decimal
            
            return round(decimal, 6)
        
        except Exception as e:
            logger.debug(f"LatLong-Parsing: {e}")
            return None
    
    def _derive_try_region(self, lat: Optional[float], lon: Optional[float]) -> Optional[str]:
        """V1: Leite TRY-Region aus Koordinaten ab (alle 15 DWD-Stationen, Distanzberechnung)"""
        if lat is None or lon is None:
            return None
        
        # Alle 15 DWD Testreferenzjahr-Regionen mit Koordinaten
        # Quelle: DWD TRY 2015
        try_stations = [
            ("01", 54.7, 9.1, "Bremerhaven"),
            ("02", 53.6, 10.0, "Hamburg"),
            ("03", 52.5, 13.4, "Potsdam"),
            ("04", 51.3, 6.8, "Essen"),
            ("05", 50.8, 6.1, "Aachen"),
            ("06", 49.5, 8.5, "Bad Marienberg"),
            ("07", 50.0, 8.6, "Frankfurt/Main"),
            ("08", 49.9, 10.9, "Würzburg"),
            ("09", 48.8, 9.2, "Stuttgart"),
            ("10", 48.1, 11.6, "München"),
            ("11", 47.8, 10.9, "Garmisch-Partenkirchen"),
            ("12", 50.8, 12.9, "Chemnitz"),
            ("13", 51.5, 11.9, "Halle"),
            ("14", 52.1, 11.6, "Magdeburg"),
            ("15", 54.5, 13.4, "Rostock")
        ]
        
        # Finde nächste Station (euklidische Distanz)
        import math
        min_distance = float('inf')
        nearest_region = "04"  # Fallback
        
        for region_id, station_lat, station_lon, name in try_stations:
            # Euklidische Distanz (vereinfacht, für Deutschland ausreichend)
            distance = math.sqrt(
                (lat - station_lat) ** 2 + (lon - station_lon) ** 2
            )
            if distance < min_distance:
                min_distance = distance
                nearest_region = region_id
        
        return nearest_region
    
    def _extract_element_basic(self, ifc_elem) -> Optional[IFCElement]:
        """Extrahiert Basis-Informationen"""
        try:
            guid = ifc_elem.GlobalId
            ifc_type = ifc_elem.is_a()
            name = ifc_elem.Name or f'{ifc_type} {guid[:8]}'
            tag = ifc_elem.Tag if hasattr(ifc_elem, 'Tag') else None

            predefined_type = None
            if hasattr(ifc_elem, 'PredefinedType') and ifc_elem.PredefinedType:
                predefined_type = str(ifc_elem.PredefinedType)

            storey = None
            storey_guid = None
            try:
                if hasattr(ifc_elem, 'ContainedInStructure'):
                    for rel in ifc_elem.ContainedInStructure:
                        if rel.RelatingStructure.is_a('IfcBuildingStorey'):
                            storey = rel.RelatingStructure.Name
                            storey_guid = rel.RelatingStructure.GlobalId
                            break
            except (AttributeError, TypeError):
                pass

            return IFCElement(
                guid=guid,
                ifc_type=ifc_type,
                name=name,
                tag=tag,
                storey_guid=storey_guid,
                predefined_type=predefined_type,
            )

        except Exception as e:
            logger.debug(f"Element-Extraktion fehlgeschlagen: {e}")
            return None

    def _calculate_wall_area(self, verts, faces) -> Optional[float]:
        """R1-FIX: Wandfläche via Normalengruppierung, größte Seite"""
        faces_by_direction: Dict[Tuple, List[float]] = {}

        for i in range(0, len(faces), 3):
            try:
                idx1, idx2, idx3 = faces[i] * 3, faces[i + 1] * 3, faces[i + 2] * 3
                v1 = (verts[idx1], verts[idx1 + 1], verts[idx1 + 2])
                v2 = (verts[idx2], verts[idx2 + 1], verts[idx2 + 2])
                v3 = (verts[idx3], verts[idx3 + 1], verts[idx3 + 2])

                nz_norm = self._face_nz(v1, v2, v3)
                if nz_norm is None or abs(nz_norm) > 0.1:
                    continue  # Nur Seitenflächen

                nx, ny = self._face_normal_xy(v1, v2, v3)
                if nx is None:
                    continue

                key = (round(nx, 1), round(ny, 1))
                area = self._triangle_area(v1, v2, v3)
                if area:
                    faces_by_direction.setdefault(key, []).append(area)
            except (IndexError, ValueError):
                continue

        if faces_by_direction:
            best = max(faces_by_direction.values(), key=sum)
            return round(sum(best), 2)
        return None

    def _sum_faces_by_normal(self, verts, faces, nz_min: float = 0.9) -> Optional[float]:
        """S4: Summiere Faces deren Normale nach oben zeigt (nz > nz_min)"""
        total = 0.0
        for i in range(0, len(faces), 3):
            try:
                idx1, idx2, idx3 = faces[i] * 3, faces[i + 1] * 3, faces[i + 2] * 3
                v1 = (verts[idx1], verts[idx1 + 1], verts[idx1 + 2])
                v2 = (verts[idx2], verts[idx2 + 1], verts[idx2 + 2])
                v3 = (verts[idx3], verts[idx3 + 1], verts[idx3 + 2])

                nz = self._face_nz(v1, v2, v3)
                if nz is not None and nz > nz_min:
                    area = self._triangle_area(v1, v2, v3)
                    if area:
                        total += area
            except (IndexError, ValueError):
                continue

        return total if total > 0 else None

    def _calculate_total_surface(self, verts, faces) -> Optional[float]:
        """K2: Dachfläche nur Außenseite (Dachschräge), nicht Unterseite/Kanten
        
        Filter: Faces mit abs(nz) < 0.9 (Neigung 0-80° von Horizontalen)
        - Dachschräge: nz ≈ 0.2-0.7 (abhängig von Neigung)
        - Unterseite: nz ≈ -0.9 bis -1.0 (nach unten zeigend) → ausschließen
        - Kanten: nz ≈ 0 (vertikal) → OK, aber meist klein
        """
        total = 0.0
        for i in range(0, len(faces), 3):
            try:
                idx1, idx2, idx3 = faces[i] * 3, faces[i + 1] * 3, faces[i + 2] * 3
                v1 = (verts[idx1], verts[idx1 + 1], verts[idx1 + 2])
                v2 = (verts[idx2], verts[idx2 + 1], verts[idx2 + 2])
                v3 = (verts[idx3], verts[idx3 + 1], verts[idx3 + 2])

                # K2: Nur Faces mit abs(nz) < 0.9 (Dachschräge, nicht Unterseite)
                nz = self._face_nz(v1, v2, v3)
                if nz is not None and abs(nz) < 0.9:
                    area = self._triangle_area(v1, v2, v3)
                    if area:
                        total += area
            except (IndexError, ValueError):
                continue

        return round(total, 2) if total > 0 else None

    @staticmethod
    def _triangle_area(v1, v2, v3) -> Optional[float]:
        """Dreiecksfläche via Kreuzprodukt (numerisch stabiler als Heron)"""
        ax, ay, az = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
        bx, by, bz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
        cx = ay * bz - az * by
        cy = az * bx - ax * bz
        cz = ax * by - ay * bx
        area = 0.5 * math.sqrt(cx * cx + cy * cy + cz * cz)
        return area if area > 1e-10 else None

    @staticmethod
    def _face_nz(v1, v2, v3) -> Optional[float]:
        """Normalisierte Z-Komponente der Face-Normale"""
        ax, ay, az = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
        bx, by, bz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
        nx = ay * bz - az * by
        ny = az * bx - ax * bz
        nz = ax * by - ay * bx
        length = math.sqrt(nx * nx + ny * ny + nz * nz)
        return nz / length if length > 1e-10 else None

    @staticmethod
    def _face_normal_xy(v1, v2, v3) -> Tuple[Optional[float], Optional[float]]:
        """Normalisierte XY-Komponenten der Face-Normale"""
        ax, ay, az = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
        bx, by, bz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
        nx = ay * bz - az * by
        ny = az * bx - ax * bz
        nz = ax * by - ay * bx
        length = math.sqrt(nx * nx + ny * ny + nz * nz)
        if length < 1e-10:
            return None, None
        return nx / length, ny / length

    def _calculate_orientation(self, shape) -> Tuple[Optional[float], Optional[float]]:
        """B1: Orientierung/Neigung aus dominanter Face-Gruppe (größte Fläche)"""
        try:
            verts = shape.geometry.verts
            faces = shape.geometry.faces
            if not verts or not faces or len(verts) < 9:
                return None, None

            # Gruppiere Faces nach Normalenrichtung (gerundet auf 0.1)
            face_groups: Dict[Tuple[float, float, float], List[float]] = {}

            for i in range(0, len(faces), 3):
                try:
                    idx1, idx2, idx3 = faces[i] * 3, faces[i + 1] * 3, faces[i + 2] * 3
                    v1 = (verts[idx1], verts[idx1 + 1], verts[idx1 + 2])
                    v2 = (verts[idx2], verts[idx2 + 1], verts[idx2 + 2])
                    v3 = (verts[idx3], verts[idx3 + 1], verts[idx3 + 2])

                    # Kreuzprodukt für Normale
                    ax, ay, az = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
                    bx, by, bz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
                    nx = ay * bz - az * by
                    ny = az * bx - ax * bz
                    nz = ax * by - ay * bx

                    # Fläche
                    area = 0.5 * math.sqrt(nx * nx + ny * ny + nz * nz)
                    if area < 1e-10:
                        continue

                    # Normalisiere Normale
                    length = math.sqrt(nx * nx + ny * ny + nz * nz)
                    nx, ny, nz = nx / length, ny / length, nz / length

                    # Gruppiere nach gerundeter Normale
                    key = (round(nx, 1), round(ny, 1), round(nz, 1))
                    if key not in face_groups:
                        face_groups[key] = []
                    face_groups[key].append(area)

                except (IndexError, ValueError, ZeroDivisionError):
                    continue

            if not face_groups:
                return None, None

            # Finde dominante Gruppe (größte Gesamtfläche)
            dominant_key = max(face_groups.keys(), key=lambda k: sum(face_groups[k]))
            avg_nx, avg_ny, avg_nz = dominant_key

            # Normalisiere (falls durch Rundung denormalisiert)
            length = math.sqrt(avg_nx ** 2 + avg_ny ** 2 + avg_nz ** 2)
            if length < 1e-10:
                return None, None
            avg_nx, avg_ny, avg_nz = avg_nx / length, avg_ny / length, avg_nz / length

            # Orientierung (Azimut)
            orientation = math.degrees(math.atan2(avg_nx, avg_ny))
            if orientation < 0:
                orientation += 360

            # Neigung (von Vertikale)
            inclination = math.degrees(math.acos(min(abs(avg_nz), 1.0)))

            return round(orientation, 1), round(inclination, 1)

        except (ValueError, ZeroDivisionError):
            return None, None

    def _calculate_roof_area_from_slabs(self, roof_guid: str) -> Optional[float]:
        """Aggregiere Dachfläche aus zugehörigen Slabs"""
        try:
            roof_ifc = self.ifc_cache.get(roof_guid)
            if not roof_ifc or not hasattr(roof_ifc, 'IsDecomposedBy'):
                return None

            total = 0.0
            for rel in roof_ifc.IsDecomposedBy:
                for obj in rel.RelatedObjects:
                    if obj.is_a('IfcSlab'):
                        for slab in self.geometry.roofs:
                            if slab.guid == obj.GlobalId and slab.area:
                                total += slab.area
            return round(total, 2) if total > 0 else None

        except Exception as e:
            logger.debug(f"Roof-Slab-Aggregation: {e}")
            return None


# ============================================================
# P1: Output-Format → Schema v2.2
# ============================================================
def parse_ifc_file(ifc_file_path: str) -> Dict[str, Any]:
    """
    V3: Parst IFC-Datei und gibt Schema v2.3 konformes Dictionary zurück.
    
    Struktur: input.building (storeys, dwelling_units, zones, rooms) + input.envelope (walls, roofs, ...)
    
    Neu in v2.3:
    - rooms[] statt zones[] (IfcSpace → room)
    - dwelling_units[] (leer, manuell zu ergänzen)
    - zones[] (leer, thermische Zonen manuell zu ergänzen)
    - Elemente haben room_ref (IfcSpace GUID) statt zone_ref
    """
    parser = IFCParser(ifc_file_path)
    geometry = parser.parse()

    def opaque_to_dict(elem: IFCElement) -> Dict[str, Any]:
        """Opakes Element → Schema v2.3 opaque_element"""
        return {
            "id": elem.guid,
            "ifc_guid": elem.guid,
            "ifc_type": elem.ifc_type,
            "predefined_type": elem.predefined_type,
            "name": elem.name,
            "area": elem.area,
            "orientation": elem.orientation,
            "inclination": elem.inclination,
            "u_value": elem.u_value,
            "boundary_condition": elem.boundary_condition,
            "din_code": elem.din_code,
            "fx_factor": elem.fx_factor,
            "room_ref": elem.room_ref,  # K3: room_ref (IfcSpace GUID)
            "zone_ref": None,  # Wird manuell ergänzt (thermische Zone)
            "storey_ref": elem.storey_guid,
            "construction_ref": None,  # Wird aus Katalog ergänzt
        }

    def transparent_to_dict(elem: IFCElement) -> Dict[str, Any]:
        """Transparentes Element → Schema v2.3 transparent_element"""
        return {
            "id": elem.guid,
            "ifc_guid": elem.guid,
            "ifc_type": elem.ifc_type,
            "name": elem.name,
            "area": elem.area,
            "orientation": elem.orientation,
            "inclination": elem.inclination,
            "u_value": elem.u_value,
            "g_value": None,               # Nicht aus IFC ableitbar
            "tau_value": None,              # Nicht aus IFC ableitbar
            "g_value_perpendicular": None,  # Nicht aus IFC ableitbar
            "g_value_summer": None,         # Wird aus EVEBI/Katalog ergänzt
            "g_value_winter": None,         # Wird aus EVEBI/Katalog ergänzt
            "is_glazed": elem.ifc_type == 'IfcWindow',
            "boundary_condition": elem.boundary_condition,
            "din_code": elem.din_code,
            "fx_factor": elem.fx_factor,
            "parent_wall_guid": elem.parent_element_guid,
            "room_ref": elem.room_ref,  # K3: room_ref (IfcSpace GUID)
            "zone_ref": None,  # Wird manuell ergänzt (thermische Zone)
            "storey_ref": elem.storey_guid,
            "shading_factor_f_sh": None,    # Wird ergänzt
            "construction_ref": None,
        }

    # P1: Schema v2.3 Struktur (flach: dwelling_units, zones, rooms)
    return {
        "schema_info": {
            "url": "https://din18599-ifc.de/schema/v2.3/complete",
            "version": "2.3.0"
        },
        "meta": {
            "project_name": geometry.project_name,
            "ifc_file_ref": ifc_file_path,
            "ifc_schema": geometry.schema,
        },
        "input": {
            "building": {
                "name": geometry.building_name,
                "building_guid": geometry.building_guid,
                "storeys": geometry.storeys,
                "dwelling_units": [],  # Wird manuell oder aus IFC ergänzt
                "zones": [],           # Wird manuell oder aus IfcZone ergänzt
                "rooms": [
                    {
                        "id": s['id'],
                        "ifc_guid": s['ifc_guid'],
                        "name": s['name'],
                        "area": s.get('area'),
                        "volume": s.get('volume'),
                        "height": s.get('height'),
                        "zone_ref": None,           # Wird manuell ergänzt
                        "dwelling_unit_ref": None,  # Optional
                        "storey_ref": s.get('storey_ref'),
                    }
                    for s in geometry.spaces
                ],
            },
            "envelope": {
                "walls": [opaque_to_dict(e) for e in geometry.walls],
                # P3: Nur IfcSlabs (ROOF), keine IfcRoof-Aggregate (Doppelzählung)
                "roofs": [opaque_to_dict(e) for e in geometry.roofs if e.ifc_type != 'IfcRoof'],
                "floors": [opaque_to_dict(e) for e in geometry.slabs],
                "windows": [transparent_to_dict(e) for e in geometry.windows],
                "doors": [transparent_to_dict(e) for e in geometry.doors],
            },
            "material_layers": [],  # TODO: Material-Extractor fixen (aktuell ImportError)
            # P2: Climate aus IfcSite Geodaten
            "climate": {
                "try_region": parser._derive_try_region(geometry.latitude, geometry.longitude),
                "latitude": geometry.latitude,
                "longitude": geometry.longitude,
            } if geometry.latitude or geometry.longitude else None,
        },
        "warnings": geometry.warnings,
        "errors": geometry.errors,
    }
