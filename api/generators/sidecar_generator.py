"""
DIN18599 Sidecar JSON Generator

Generiert vollständige DIN18599 Sidecar JSON Dateien aus IFC + EVEBI Daten.
Implementiert das Mapping gemäß docs/EVEBI_TO_SIDECAR_MAPPING.md
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from difflib import SequenceMatcher

@dataclass
class IFCElement:
    """IFC-Element (aus IFC-Parser)"""
    guid: str
    type: str
    name: str
    area: float
    posno: Optional[str] = None


@dataclass
class EVEBIMaterial:
    """EVEBI-Material (aus EVEBI-Parser)"""
    guid: str
    name: str
    lambda_value: float
    density: float


@dataclass
class EVEBIConstruction:
    """EVEBI-Konstruktion (aus EVEBI-Parser)"""
    guid: str
    name: str
    u_value: float


@dataclass
class EVEBIElement:
    """EVEBI-Bauteil (aus EVEBI-Parser)"""
    guid: str
    name: str
    posno: Optional[str]
    element_type: str
    area: float
    u_value: float
    orientation: Optional[float]
    inclination: Optional[float]
    construction_ref: Optional[str]


@dataclass
class EVEBIZone:
    """EVEBI-Zone (aus EVEBI-Parser)"""
    guid: str
    name: str
    area: float
    volume: float


class SidecarGenerator:
    """Generiert DIN18599 Sidecar JSON aus IFC + EVEBI Daten"""
    
    def __init__(self):
        self.schema_version = "2.0.0"
        self.software_name = "DWEapp"
        self.software_version = "1.0.0"
    
    def generate(
        self,
        ifc_data: Dict[str, Any],
        evebi_data: Dict[str, Any],
        project_name: Optional[str] = None,
        ifc_file_ref: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generiert vollständiges Sidecar JSON
        
        Args:
            ifc_data: Geparste IFC-Daten (aus ifc_parser.py)
            evebi_data: Geparste EVEBI-Daten (aus evebi_parser.py)
            project_name: Projektname (optional)
            ifc_file_ref: IFC-Dateiname (optional)
        
        Returns:
            Vollständiges DIN18599 Sidecar JSON
        """
        
        # IFC-Elemente vorbereiten
        ifc_elements = self._prepare_ifc_elements(ifc_data)
        
        # EVEBI-Daten vorbereiten
        evebi_materials = self._prepare_evebi_materials(evebi_data)
        evebi_constructions = self._prepare_evebi_constructions(evebi_data)
        evebi_elements = self._prepare_evebi_elements(evebi_data)
        evebi_zones = self._prepare_evebi_zones(evebi_data)
        
        # IFC + EVEBI Matching
        matched_elements = self._match_elements(ifc_elements, evebi_elements)
        
        # Sidecar JSON aufbauen
        sidecar = {
            "schema_info": {
                "url": "https://din18599-ifc.de/schema/v1",
                "version": self.schema_version
            },
            "meta": self._generate_meta(
                project_name or evebi_data.get("project_name", "Unbekanntes Projekt"),
                ifc_file_ref or "unknown.ifc",
                ifc_data.get("building_guid")
            ),
            "input": {
                "climate_location": self._generate_climate_location(),
                "zones": self._map_zones(evebi_zones),
                "materials": self._map_materials(evebi_materials),
                "layer_structures": self._map_layer_structures(evebi_constructions),
                "elements": [],
                "windows": []
            }
        }
        
        # Bauteile + Fenster mappen
        elements, windows = self._map_elements(matched_elements)
        sidecar["input"]["elements"] = elements
        sidecar["input"]["windows"] = windows
        
        # Anlagentechnik (falls vorhanden)
        if "systems" in evebi_data:
            sidecar["input"]["systems"] = self._map_systems(evebi_data["systems"])
        
        if "dhw" in evebi_data:
            sidecar["input"]["dhw"] = self._map_dhw(evebi_data["dhw"])
        
        if "ventilation" in evebi_data:
            sidecar["input"]["ventilation"] = self._map_ventilation(evebi_data["ventilation"])
        
        if "pv" in evebi_data:
            sidecar["input"]["pv"] = self._map_pv(evebi_data["pv"])
        
        return sidecar
    
    # ========================================================================
    # IFC-Daten Vorbereitung
    # ========================================================================
    
    def _prepare_ifc_elements(self, ifc_data: Dict[str, Any]) -> List[IFCElement]:
        """Konvertiert IFC-Daten in IFCElement-Objekte"""
        elements = []
        
        for element_type in ["walls", "roofs", "floors", "windows", "doors"]:
            if element_type in ifc_data:
                for elem in ifc_data[element_type]:
                    # PosNo aus Properties extrahieren (falls vorhanden)
                    posno = None
                    if "properties" in elem and "PosNo" in elem["properties"]:
                        posno = elem["properties"]["PosNo"]
                    
                    # Falls keine PosNo in Properties, aus Namen extrahieren
                    # Muster: "Wand - 001", "Fenster - 002", "Außenwand Pos 001"
                    if not posno:
                        posno = self._extract_posno_from_name(elem.get("name", ""))
                    
                    elements.append(IFCElement(
                        guid=elem.get("guid", ""),
                        type=element_type.upper().rstrip("S"),  # "walls" -> "WALL"
                        name=elem.get("name", ""),
                        area=elem.get("area", 0.0),
                        posno=posno
                    ))
        
        return elements
    
    def _extract_posno_from_name(self, name: str) -> Optional[str]:
        """
        Extrahiert PosNo aus Element-Namen
        
        Muster:
        - "Wand - 001" -> "001"
        - "Fenster - 002" -> "002"
        - "Außenwand Pos 001" -> "001"
        - "Tür in Zwischenwand Pos 002" -> "002"
        """
        import re
        
        # Muster 1: " - 001", " - 002" (IFC-Standard)
        match = re.search(r'\s-\s(\d{3,})', name)
        if match:
            return match.group(1)
        
        # Muster 2: "Pos 001", "Pos 002" (EVEBI-Standard)
        match = re.search(r'Pos\s+(\d{3,})', name, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Muster 3: Nur Zahl am Ende "001", "002"
        match = re.search(r'\b(\d{3,})$', name)
        if match:
            return match.group(1)
        
        return None
    
    # ========================================================================
    # EVEBI-Daten Vorbereitung
    # ========================================================================
    
    def _prepare_evebi_materials(self, evebi_data: Dict[str, Any]) -> List[EVEBIMaterial]:
        """Konvertiert EVEBI-Materialien"""
        materials = []
        
        if "materials" in evebi_data:
            for mat in evebi_data["materials"]:
                if mat.get("lambda", 0) > 0:  # Nur echte Materialien
                    materials.append(EVEBIMaterial(
                        guid=mat.get("guid", ""),
                        name=mat.get("name", ""),
                        lambda_value=mat.get("lambda", 0.0),
                        density=mat.get("density", 0.0)
                    ))
        
        return materials
    
    def _prepare_evebi_constructions(self, evebi_data: Dict[str, Any]) -> List[EVEBIConstruction]:
        """Konvertiert EVEBI-Konstruktionen"""
        constructions = []
        
        if "constructions" in evebi_data:
            for konstr in evebi_data["constructions"]:
                constructions.append(EVEBIConstruction(
                    guid=konstr.get("guid", ""),
                    name=konstr.get("name", ""),
                    u_value=konstr.get("u_value", 0.0)
                ))
        
        return constructions
    
    def _prepare_evebi_elements(self, evebi_data: Dict[str, Any]) -> List[EVEBIElement]:
        """Konvertiert EVEBI-Bauteile"""
        elements = []
        
        if "elements" in evebi_data:
            for elem in evebi_data["elements"]:
                elements.append(EVEBIElement(
                    guid=elem.get("guid", ""),
                    name=elem.get("name", ""),
                    posno=elem.get("posno"),
                    element_type=elem.get("element_type", "WALL"),
                    area=elem.get("area", 0.0),
                    u_value=elem.get("u_value", 0.0),
                    orientation=elem.get("orientation"),
                    inclination=elem.get("inclination"),
                    construction_ref=elem.get("construction_ref")
                ))
        
        return elements
    
    def _prepare_evebi_zones(self, evebi_data: Dict[str, Any]) -> List[EVEBIZone]:
        """Konvertiert EVEBI-Zonen"""
        zones = []
        
        if "zones" in evebi_data:
            for zone in evebi_data["zones"]:
                zones.append(EVEBIZone(
                    guid=zone.get("guid", ""),
                    name=zone.get("name", ""),
                    area=zone.get("area", 0.0),
                    volume=zone.get("volume", 0.0)
                ))
        
        return zones
    
    # ========================================================================
    # IFC + EVEBI Matching
    # ========================================================================
    
    def _match_elements(
        self,
        ifc_elements: List[IFCElement],
        evebi_elements: List[EVEBIElement]
    ) -> List[Dict[str, Any]]:
        """
        Matched IFC-Elemente mit EVEBI-Elementen (Optimiert v2)
        
        Matching-Strategie (Multi-Pass):
        1. Pass 1: PosNo-Match (exakt) - Score 1.0
        2. Pass 2: Name + Typ + Fläche (kombiniert) - Score 0.4+
        3. Pass 3: Nur Typ + Fläche (Fallback) - Score 0.3+
        
        Returns:
            Liste von Matches: {"ifc": IFCElement, "evebi": EVEBIElement, "score": float}
        """
        matches = []
        matched_evebi_guids = set()
        unmatched_ifc = []
        
        # Pass 1: PosNo-Match (höchste Priorität)
        for ifc_elem in ifc_elements:
            if not ifc_elem.posno:
                unmatched_ifc.append(ifc_elem)
                continue
            
            matched = False
            for evebi_elem in evebi_elements:
                if evebi_elem.guid in matched_evebi_guids:
                    continue
                
                if evebi_elem.posno and self._normalize_posno(ifc_elem.posno) == self._normalize_posno(evebi_elem.posno):
                    matches.append({
                        "ifc": ifc_elem,
                        "evebi": evebi_elem,
                        "score": 1.0,
                        "method": "posno"
                    })
                    matched_evebi_guids.add(evebi_elem.guid)
                    matched = True
                    break
            
            if not matched:
                unmatched_ifc.append(ifc_elem)
        
        # Pass 2: Name + Typ + Fläche Match
        still_unmatched = []
        for ifc_elem in unmatched_ifc:
            best_match = None
            best_score = 0.0
            
            for evebi_elem in evebi_elements:
                if evebi_elem.guid in matched_evebi_guids:
                    continue
                
                score = self._calculate_match_score(ifc_elem, evebi_elem)
                
                if score > best_score:
                    best_score = score
                    best_match = evebi_elem
            
            # Niedrigere Schwelle für bessere Match-Rate
            if best_match and best_score > 0.35:
                matches.append({
                    "ifc": ifc_elem,
                    "evebi": best_match,
                    "score": best_score,
                    "method": "fuzzy"
                })
                matched_evebi_guids.add(best_match.guid)
            else:
                still_unmatched.append(ifc_elem)
        
        # Ungematchte IFC-Elemente auch hinzufügen (wichtig für Fenster!)
        for ifc_elem in still_unmatched:
            matches.append({
                "ifc": ifc_elem,
                "evebi": None,  # Kein EVEBI-Match
                "score": 0.0,
                "method": "ifc_only"
            })
        
        print(f"\n📊 Matching-Statistik:")
        print(f"   - Pass 1 (PosNo): {len([m for m in matches if m.get('method') == 'posno'])} Matches")
        print(f"   - Pass 2 (Fuzzy): {len([m for m in matches if m.get('method') == 'fuzzy'])} Matches")
        print(f"   - IFC-Only (unmatched): {len([m for m in matches if m.get('method') == 'ifc_only'])} Elemente")
        print(f"   - Total Elemente: {len(matches)}")
        print(f"   - Match-Rate: {len([m for m in matches if m['evebi']]) / len(ifc_elements) * 100:.1f}%")
        
        return matches
    
    def _calculate_match_score(
        self,
        ifc_elem: IFCElement,
        evebi_elem: EVEBIElement
    ) -> float:
        """
        Berechnet Match-Score zwischen IFC- und EVEBI-Element (Optimiert v2)
        
        Gewichtung:
        - Name-Ähnlichkeit: 40%
        - Typ-Match: 30%
        - Flächen-Match: 30%
        
        Returns:
            Score 0.0 - 1.0 (höher = besserer Match)
        """
        score = 0.0
        
        # 1. Name-Match (Gewicht: 0.4) - Verbessert mit Token-Matching
        name_similarity = self._calculate_name_similarity_advanced(ifc_elem.name, evebi_elem.name)
        score += name_similarity * 0.4
        
        # 2. Typ-Match (Gewicht: 0.3) - Mit Fuzzy-Typ-Mapping
        type_match = self._calculate_type_similarity(ifc_elem.type, evebi_elem.element_type)
        score += type_match * 0.3
        
        # 3. Flächen-Match (Gewicht: 0.3) - Erweiterte Toleranz
        if ifc_elem.area > 0 and evebi_elem.area > 0:
            area_diff = abs(ifc_elem.area - evebi_elem.area) / max(ifc_elem.area, evebi_elem.area)
            
            # Gestaffelte Bewertung
            if area_diff < 0.05:  # ±5%
                score += 0.3
            elif area_diff < 0.15:  # ±15%
                score += 0.2
            elif area_diff < 0.25:  # ±25%
                score += 0.1
        
        return score
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Berechnet Name-Ähnlichkeit (0.0 - 1.0) - Legacy"""
        return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
    
    def _calculate_name_similarity_advanced(self, name1: str, name2: str) -> float:
        """
        Erweiterte Name-Ähnlichkeit mit Token-Matching
        
        Strategie:
        1. Exakte Übereinstimmung → 1.0
        2. Token-basiertes Matching (Wörter vergleichen)
        3. Levenshtein-ähnliche Sequenz-Matching
        """
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        
        # Exakt
        if n1 == n2:
            return 1.0
        
        # Normalisierung (Umlaute, Sonderzeichen)
        n1_norm = self._normalize_name(n1)
        n2_norm = self._normalize_name(n2)
        
        if n1_norm == n2_norm:
            return 0.95
        
        # Token-Matching (Wörter)
        tokens1 = set(re.findall(r'\w+', n1_norm))
        tokens2 = set(re.findall(r'\w+', n2_norm))
        
        if tokens1 and tokens2:
            intersection = tokens1 & tokens2
            union = tokens1 | tokens2
            token_score = len(intersection) / len(union) if union else 0.0
        else:
            token_score = 0.0
        
        # Sequenz-Matching
        seq_score = SequenceMatcher(None, n1_norm, n2_norm).ratio()
        
        # Kombiniert (70% Token, 30% Sequenz)
        return token_score * 0.7 + seq_score * 0.3
    
    def _normalize_name(self, name: str) -> str:
        """Normalisiert Namen für besseres Matching"""
        # Umlaute
        replacements = {
            'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
            'á': 'a', 'à': 'a', 'â': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i',
            'ó': 'o', 'ò': 'o', 'ô': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u'
        }
        
        name = name.lower()
        for old, new in replacements.items():
            name = name.replace(old, new)
        
        # Sonderzeichen entfernen (außer Leerzeichen und Zahlen)
        name = re.sub(r'[^a-z0-9\s]', '', name)
        
        # Mehrfache Leerzeichen
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def _normalize_posno(self, posno: str) -> str:
        """Normalisiert PosNo für Matching"""
        # Nur Zahlen extrahieren
        numbers = re.findall(r'\d+', str(posno))
        return numbers[0] if numbers else str(posno)
    
    def _calculate_type_similarity(self, ifc_type: str, evebi_type: str) -> float:
        """
        Berechnet Typ-Ähnlichkeit mit Fuzzy-Mapping
        
        Berücksichtigt:
        - Exakte Übereinstimmung
        - Typ-Synonyme (z.B. WALL ↔ WAND)
        - Typ-Kategorien (z.B. ROOF ↔ DACH)
        """
        # Typ-Mapping (IFC → EVEBI)
        type_mappings = {
            'WALL': ['WALL', 'WAND', 'AUSSENWAND', 'INNENWAND'],
            'ROOF': ['ROOF', 'DACH', 'FLACHDACH', 'STEILDACH'],
            'FLOOR': ['FLOOR', 'SLAB', 'DECKE', 'BODEN', 'BODENPLATTE'],
            'WINDOW': ['WINDOW', 'FENSTER'],
            'DOOR': ['DOOR', 'TUER', 'TÜR']
        }
        
        ifc_upper = ifc_type.upper()
        evebi_upper = evebi_type.upper()
        
        # Exakt
        if ifc_upper == evebi_upper:
            return 1.0
        
        # Fuzzy via Mapping
        for ifc_key, evebi_variants in type_mappings.items():
            if ifc_upper == ifc_key or ifc_upper in evebi_variants:
                if evebi_upper in evebi_variants:
                    return 0.9
        
        # Substring-Match
        if ifc_upper in evebi_upper or evebi_upper in ifc_upper:
            return 0.5
        
        return 0.0
    
    # ========================================================================
    # Sidecar JSON Mapping
    # ========================================================================
    
    def _generate_meta(
        self,
        project_name: str,
        ifc_file_ref: str,
        building_guid: Optional[str]
    ) -> Dict[str, Any]:
        """Generiert Meta-Sektion"""
        return {
            "project_id": f"PRJ-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}",
            "project_name": project_name,
            "ifc_file_ref": ifc_file_ref,
            "ifc_guid_building": building_guid or "unknown",
            "lod": "300",
            "software_name": self.software_name,
            "software_version": self.software_version,
            "calculation_date": datetime.now().isoformat() + "Z",
            "norm_version": "DIN V 18599:2018-09"
        }
    
    def _generate_climate_location(self) -> Dict[str, Any]:
        """Generiert Klima-Standort (Default: Berlin)"""
        return {
            "postcode": "10115",
            "city": "Berlin",
            "try_region_code": 4
        }
    
    def _map_materials(self, materials: List[EVEBIMaterial]) -> List[Dict[str, Any]]:
        """Mappt EVEBI-Materialien zu Sidecar JSON"""
        sidecar_materials = []
        
        for mat in materials:
            sidecar_materials.append({
                "id": f"MAT-{mat.guid[:8]}",
                "name": mat.name,
                "type": "STANDARD",
                "lambda": mat.lambda_value,
                "density": mat.density,
                "specific_heat": 1000,  # Default
                "vapor_resistance_factor": 10  # Default
            })
        
        return sidecar_materials
    
    def _map_layer_structures(
        self,
        constructions: List[EVEBIConstruction]
    ) -> List[Dict[str, Any]]:
        """Mappt EVEBI-Konstruktionen zu Sidecar JSON"""
        sidecar_structures = []
        
        for konstr in constructions:
            # Typ aus Name ableiten
            structure_type = self._detect_structure_type(konstr.name)
            
            sidecar_structures.append({
                "id": f"LS-{konstr.guid[:8]}",
                "name": konstr.name,
                "type": structure_type,
                "layers": [],  # Leer, da EVEBI keine Schichten hat
                "calculated_values": {
                    "u_value_w_m2k": konstr.u_value
                }
            })
        
        return sidecar_structures
    
    def _map_zones(self, zones: List[EVEBIZone]) -> List[Dict[str, Any]]:
        """Mappt EVEBI-Zonen zu Sidecar JSON"""
        sidecar_zones = []
        
        for zone in zones:
            # Höhe berechnen
            height = zone.volume / zone.area if zone.area > 0 else 3.0
            
            sidecar_zones.append({
                "id": f"ZONE-{zone.guid[:8]}",
                "name": zone.name,
                "usage_profile": "17",  # Wohnen (default)
                "area_an": round(zone.area, 2),
                "volume_v": round(zone.volume, 2),
                "height_h": round(height, 2),
                "air_change_n50": 0.6,  # Default
                "design_temp_heating": 20,  # Default
                "design_temp_cooling": 26,  # Default
                "lighting_control": "MANUAL",
                "space_guids": []  # Leer, da keine IFC-Verknüpfung
            })
        
        return sidecar_zones
    
    def _map_elements(
        self,
        matches: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Mappt gematchte Elemente zu Sidecar JSON
        
        Returns:
            (elements, windows)
        """
        sidecar_elements = []
        sidecar_windows = []
        
        for match in matches:
            ifc_elem = match["ifc"]
            evebi_elem = match["evebi"]
            
            # Prüfe ob IFC-Element ein Fenster ist (aus IFC-Typ)
            is_window = ifc_elem.type.lower() in ["window", "ifcwindow"]
            
            if is_window:
                # Fenster (aus IFC, mit oder ohne EVEBI-Match)
                window = {
                    "ifc_guid": ifc_elem.guid,
                    "u_value_glass": evebi_elem.u_value if evebi_elem else 1.1,
                    "u_value_frame": 1.3,  # Default
                    "psi_spacer": 0.03,  # Default
                    "g_value": 0.6,  # Default
                    "frame_fraction": 0.2,  # Default
                    "shading_factor_fs": 1.0,
                    "horizon_angle": 0,
                    "overhang_angle": 0
                }
                sidecar_windows.append(window)
            else:
                # Opakes Bauteil
                element = {
                    "ifc_guid": ifc_elem.guid,
                    "boundary_condition": self._detect_boundary_condition(evebi_elem.name if evebi_elem else ifc_elem.name),
                    "layer_structure_ref": f"LS-{evebi_elem.construction_ref[:8]}" if (evebi_elem and evebi_elem.construction_ref) else None,
                    "u_value_undisturbed": evebi_elem.u_value if evebi_elem else 0,
                    "thermal_bridge_delta_u": 0.02,  # Default
                    "thermal_bridge_type": "SIMPLIFIED",
                    "orientation": (evebi_elem.orientation if evebi_elem else 0) or 0,
                    "inclination": (evebi_elem.inclination if evebi_elem else 90) or 90
                }
                
                # Solar Absorption (nur für Außenbauteile)
                if element["boundary_condition"] == "EXTERIOR":
                    element["solar_absorption"] = 0.5  # Default
                
                sidecar_elements.append(element)
        
        return sidecar_elements, sidecar_windows
    
    def _map_systems(self, systems_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mappt EVEBI-Heizungssysteme zu Sidecar JSON"""
        sidecar_systems = []
        
        for system in systems_data:
            # Typ-Mapping
            system_type = self._map_heating_type(system.get('art', ''))
            
            # Energieträger ermitteln
            energy_source = self._detect_energy_source(system.get('name', ''))
            
            sidecar_system = {
                "id": f"SYS-{system.get('guid', '')[:8]}",
                "type": system_type,
                "name": system.get('name', 'Unbekanntes System'),
                "energy_source": energy_source,
                "year_built": system.get('year_built', 2020),
                "operation_mode": "MONOVALENT"
            }
            
            # Wärmepumpen-spezifisch
            if "HEAT_PUMP" in system_type:
                sidecar_system["heat_pump"] = {
                    "cop_a2_w35": system.get('cop_a2_w35', 4.0),
                    "cop_a7_w35": system.get('cop_a7_w35', 4.5),
                    "refrigerant": "R290"
                }
            
            sidecar_systems.append(sidecar_system)
        
        return sidecar_systems
    
    def _map_dhw(self, dhw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mappt EVEBI-Warmwasser zu Sidecar JSON"""
        sidecar_dhw = []
        
        for dhw in dhw_data:
            dhw_type = self._map_dhw_type(dhw.get('art', ''))
            
            sidecar_dhw_entry = {
                "type": dhw_type,
                "storage_volume": dhw.get('storage_volume', 300),
                "storage_loss_factor": 1.8,
                "circulation": dhw.get('circulation', False),
                "circulation_length": 15 if dhw.get('circulation', False) else 0,
                "pipe_insulation": "100_PERCENT"
            }
            
            sidecar_dhw.append(sidecar_dhw_entry)
        
        return sidecar_dhw
    
    def _map_ventilation(self, vent_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mappt EVEBI-Lüftung zu Sidecar JSON"""
        sidecar_vent = []
        
        for vent in vent_data:
            vent_type = self._map_ventilation_type(vent.get('art', ''))
            has_wrg = vent.get('wrg', 0) > 0 and vent_type != "NATURAL"
            
            sidecar_vent_entry = {
                "type": vent_type,
                "heat_recovery": has_wrg,
                "heat_recovery_efficiency": vent.get('wrg_grad', 0.0) if has_wrg else 0.0,
                "volume_flow": vent.get('volume_flow', 250),
                "spf_fan": 0.35
            }
            
            sidecar_vent.append(sidecar_vent_entry)
        
        return sidecar_vent
    
    def _map_pv(self, pv_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mappt EVEBI-PV zu Sidecar JSON"""
        sidecar_pv = []
        
        for pv in pv_data:
            sidecar_pv_entry = {
                "peak_power": pv.get('peak_power', 10.0),
                "orientation": pv.get('orientation', 180),
                "inclination": pv.get('inclination', 30),
                "system_loss": 0.14,
                "battery_capacity": pv.get('battery_capacity', 0.0)
            }
            
            sidecar_pv.append(sidecar_pv_entry)
        
        return sidecar_pv
    
    # ========================================================================
    # Helper-Funktionen
    # ========================================================================
    
    def _detect_structure_type(self, name: str) -> str:
        """Erkennt Konstruktions-Typ aus Name"""
        name_lower = name.lower()
        
        if "wand" in name_lower:
            return "WALL"
        elif "dach" in name_lower:
            return "ROOF"
        elif "boden" in name_lower or "decke" in name_lower:
            return "FLOOR"
        else:
            return "WALL"  # Default
    
    def _detect_boundary_condition(self, name: str) -> str:
        """Erkennt Randbedingung aus Name"""
        name_lower = name.lower()
        
        if "außen" in name_lower or "aussen" in name_lower:
            return "EXTERIOR"
        elif "erdreich" in name_lower or "bodenplatte" in name_lower:
            return "GROUND"
        elif "innen" in name_lower or "zwischen" in name_lower:
            return "INTERIOR"
        else:
            return "EXTERIOR"  # Default
    
    def _map_heating_type(self, art: str) -> str:
        """Mappt EVEBI Heizungs-Art zu Sidecar System-Typ"""
        art_upper = art.upper()
        
        if "WAERMEPUMPE" in art_upper or "WP" in art_upper:
            if "LUFT" in art_upper:
                return "HEAT_PUMP_AIR"
            elif "SOLE" in art_upper or "ERDWAERME" in art_upper:
                return "HEAT_PUMP_BRINE"
            else:
                return "HEAT_PUMP_AIR"  # Default
        elif "FERNWAERME" in art_upper:
            return "DISTRICT_HEATING"
        elif "KESSEL" in art_upper or "BRENNWERT" in art_upper:
            return "BOILER"
        elif "OFEN" in art_upper:
            return "STOVE"
        else:
            return "BOILER"  # Default
    
    def _detect_energy_source(self, name: str) -> str:
        """Erkennt Energieträger aus System-Name"""
        name_lower = name.lower()
        
        if "strom" in name_lower or "wp" in name_lower or "wärmepumpe" in name_lower:
            return "ELECTRICITY"
        elif "gas" in name_lower or "erdgas" in name_lower:
            return "GAS"
        elif "öl" in name_lower or "oel" in name_lower:
            return "OIL"
        elif "fernwärme" in name_lower or "fernwaerme" in name_lower:
            return "DISTRICT_HEATING"
        elif "holz" in name_lower or "pellet" in name_lower:
            return "BIOMASS"
        else:
            return "GAS"  # Default
    
    def _map_dhw_type(self, art: str) -> str:
        """Mappt EVEBI Warmwasser-Art zu Sidecar DHW-Typ"""
        art_upper = art.upper()
        
        if "ZENTRAL" in art_upper or "HZG" in art_upper:
            return "CENTRAL"
        elif "DEZENTRAL" in art_upper:
            return "DECENTRAL"
        else:
            return "CENTRAL"  # Default
    
    def _map_ventilation_type(self, art: str) -> str:
        """Mappt EVEBI Lüftungs-Art zu Sidecar Ventilation-Typ"""
        art_upper = art.upper()
        
        if "FREI" in art_upper or "FENSTER" in art_upper:
            return "NATURAL"
        elif "ZENTRAL" in art_upper or "RLT" in art_upper:
            return "SUPPLY_EXHAUST"
        elif "DEZENTRAL" in art_upper or "ABLUFT" in art_upper:
            return "EXHAUST_ONLY"
        else:
            return "NATURAL"  # Default
