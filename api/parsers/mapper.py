"""
Mapping Engine
Verknüpft IFC-Geometrie mit EVEBI-Daten
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from .ifc_parser import IFCElement, IFCGeometry
from .evebi_parser import EVEBIElement, EVEBIData


@dataclass
class ElementMatch:
    """Match zwischen IFC und EVEBI Element"""
    ifc_element: IFCElement
    evebi_element: EVEBIElement
    confidence: float  # 0.0 - 1.0
    match_method: str  # 'posno', 'name', 'geometry', 'manual'


@dataclass
class MappingResult:
    """Ergebnis des Mappings"""
    matches: List[ElementMatch] = field(default_factory=list)
    unmatched_ifc: List[IFCElement] = field(default_factory=list)
    unmatched_evebi: List[EVEBIElement] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)


def map_ifc_to_evebi(
    ifc_geometry: IFCGeometry,
    evebi_data: EVEBIData,
    strategy: str = 'auto'
) -> MappingResult:
    """
    Verknüpft IFC-Geometrie mit EVEBI-Daten
    
    Args:
        ifc_geometry: Geparste IFC-Geometrie
        evebi_data: Geparste EVEBI-Daten
        strategy: 'auto', 'posno', 'name', 'geometry'
        
    Returns:
        MappingResult mit Matches und Statistiken
    """
    result = MappingResult()
    
    # Kopien für Tracking
    remaining_ifc = list(ifc_geometry.all_elements)
    remaining_evebi = list(evebi_data.elements)
    
    if strategy in ['auto', 'posno']:
        # Strategie 1: PosNo-basiert (höchste Priorität)
        matches, remaining_ifc, remaining_evebi = _match_by_posno(
            remaining_ifc, remaining_evebi
        )
        result.matches.extend(matches)
    
    if strategy in ['auto', 'name']:
        # Strategie 2: Name-basiert
        matches, remaining_ifc, remaining_evebi = _match_by_name(
            remaining_ifc, remaining_evebi
        )
        result.matches.extend(matches)
    
    if strategy in ['auto', 'geometry']:
        # Strategie 3: Geometrie-basiert (Fallback)
        matches, remaining_ifc, remaining_evebi = _match_by_geometry(
            remaining_ifc, remaining_evebi
        )
        result.matches.extend(matches)
    
    # Unmatched Elements
    result.unmatched_ifc = remaining_ifc
    result.unmatched_evebi = remaining_evebi
    
    # Statistiken
    result.stats = {
        'total_ifc': len(ifc_geometry.all_elements),
        'total_evebi': len(evebi_data.elements),
        'matched': len(result.matches),
        'unmatched_ifc': len(result.unmatched_ifc),
        'unmatched_evebi': len(result.unmatched_evebi),
        'match_rate': len(result.matches) / max(len(ifc_geometry.all_elements), 1)
    }
    
    return result


def _match_by_posno(
    ifc_elements: List[IFCElement],
    evebi_elements: List[EVEBIElement]
) -> Tuple[List[ElementMatch], List[IFCElement], List[EVEBIElement]]:
    """Matching via Positionsnummer (PosNo)"""
    matches = []
    remaining_ifc = []
    remaining_evebi = list(evebi_elements)
    
    for ifc_elem in ifc_elements:
        if not ifc_elem.tag:
            remaining_ifc.append(ifc_elem)
            continue
        
        # Suche EVEBI-Element mit gleicher PosNo
        matched = False
        for evebi_elem in remaining_evebi:
            if evebi_elem.posno and evebi_elem.posno == ifc_elem.tag:
                matches.append(ElementMatch(
                    ifc_element=ifc_elem,
                    evebi_element=evebi_elem,
                    confidence=1.0,
                    match_method='posno'
                ))
                remaining_evebi.remove(evebi_elem)
                matched = True
                break
        
        if not matched:
            remaining_ifc.append(ifc_elem)
    
    return matches, remaining_ifc, remaining_evebi


def _match_by_name(
    ifc_elements: List[IFCElement],
    evebi_elements: List[EVEBIElement]
) -> Tuple[List[ElementMatch], List[IFCElement], List[EVEBIElement]]:
    """Matching via Bauteil-Name"""
    matches = []
    remaining_ifc = []
    remaining_evebi = list(evebi_elements)
    
    for ifc_elem in ifc_elements:
        # Suche EVEBI-Element mit ähnlichem Namen
        best_match = None
        best_similarity = 0.0
        
        for evebi_elem in remaining_evebi:
            similarity = _name_similarity(ifc_elem.name, evebi_elem.name)
            if similarity > best_similarity and similarity > 0.7:  # Threshold
                best_similarity = similarity
                best_match = evebi_elem
        
        if best_match:
            matches.append(ElementMatch(
                ifc_element=ifc_elem,
                evebi_element=best_match,
                confidence=best_similarity,
                match_method='name'
            ))
            remaining_evebi.remove(best_match)
        else:
            remaining_ifc.append(ifc_elem)
    
    return matches, remaining_ifc, remaining_evebi


def _match_by_geometry(
    ifc_elements: List[IFCElement],
    evebi_elements: List[EVEBIElement]
) -> Tuple[List[ElementMatch], List[IFCElement], List[EVEBIElement]]:
    """Matching via Geometrie (Fläche + Orientierung)"""
    matches = []
    remaining_ifc = []
    remaining_evebi = list(evebi_elements)
    
    for ifc_elem in ifc_elements:
        if not ifc_elem.area:
            remaining_ifc.append(ifc_elem)
            continue
        
        # Suche EVEBI-Element mit ähnlicher Geometrie
        best_match = None
        best_confidence = 0.0
        
        for evebi_elem in remaining_evebi:
            confidence = _geometry_similarity(ifc_elem, evebi_elem)
            if confidence > best_confidence and confidence > 0.7:  # Threshold
                best_confidence = confidence
                best_match = evebi_elem
        
        if best_match:
            matches.append(ElementMatch(
                ifc_element=ifc_elem,
                evebi_element=best_match,
                confidence=best_confidence,
                match_method='geometry'
            ))
            remaining_evebi.remove(best_match)
        else:
            remaining_ifc.append(ifc_elem)
    
    return matches, remaining_ifc, remaining_evebi


def _name_similarity(name1: str, name2: str) -> float:
    """Berechnet Ähnlichkeit zwischen zwei Namen (vereinfacht)"""
    name1 = name1.lower().strip()
    name2 = name2.lower().strip()
    
    if name1 == name2:
        return 1.0
    
    # Levenshtein-Distanz (vereinfacht)
    if name1 in name2 or name2 in name1:
        return 0.8
    
    # Wort-basiert
    words1 = set(name1.split())
    words2 = set(name2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)


def _geometry_similarity(ifc_elem: IFCElement, evebi_elem: EVEBIElement) -> float:
    """Berechnet Geometrie-Ähnlichkeit"""
    confidence = 0.0
    
    # Flächen-Vergleich (50% Gewicht)
    if ifc_elem.area and evebi_elem.area:
        area_diff = abs(ifc_elem.area - evebi_elem.area) / max(ifc_elem.area, evebi_elem.area)
        if area_diff < 0.05:  # < 5% Abweichung
            confidence += 0.5
        elif area_diff < 0.10:  # < 10% Abweichung
            confidence += 0.3
    
    # Orientierungs-Vergleich (30% Gewicht)
    if ifc_elem.orientation is not None and evebi_elem.orientation is not None:
        orientation_diff = abs(ifc_elem.orientation - evebi_elem.orientation)
        # Berücksichtige 360° Wrap-around
        if orientation_diff > 180:
            orientation_diff = 360 - orientation_diff
        
        if orientation_diff < 10:  # < 10° Abweichung
            confidence += 0.3
        elif orientation_diff < 20:  # < 20° Abweichung
            confidence += 0.15
    
    # Neigungs-Vergleich (20% Gewicht)
    if ifc_elem.inclination is not None and evebi_elem.inclination is not None:
        inclination_diff = abs(ifc_elem.inclination - evebi_elem.inclination)
        if inclination_diff < 5:  # < 5° Abweichung
            confidence += 0.2
        elif inclination_diff < 10:  # < 10° Abweichung
            confidence += 0.1
    
    return confidence
