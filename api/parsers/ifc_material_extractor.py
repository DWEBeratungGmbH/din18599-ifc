"""
IFC Material Layer Extractor

Extrahiert vollständige Material-Schichtaufbauten aus IFC-Dateien.
Keine Katalog-Matches - nur direkte Extraktion der IFC-Daten.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class MaterialLayer:
    """Eine einzelne Material-Schicht"""
    position: int
    material_name: str
    thickness: float  # in Metern
    lambda_value: Optional[float] = None  # W/(m·K)
    density: Optional[float] = None  # kg/m³
    specific_heat: Optional[float] = None  # J/(kg·K)
    ifc_material_guid: Optional[str] = None


@dataclass
class LayerStructure:
    """Vollständiger Schichtaufbau"""
    ifc_guid: str
    name: str
    element_type: str  # WALL, ROOF, FLOOR, etc.
    layers: List[MaterialLayer] = field(default_factory=list)
    total_thickness: float = 0.0
    u_value_calculated: Optional[float] = None
    ifc_material_layer_set_guid: Optional[str] = None


def extract_material_layers(ifc_element, ifc_file) -> Optional[LayerStructure]:
    """
    Extrahiert Material-Schichtaufbau aus IFC-Element
    
    Strategie:
    1. IfcRelAssociatesMaterial finden
    2. IfcMaterialLayerSetUsage → IfcMaterialLayerSet
    3. Alle IfcMaterialLayer extrahieren
    4. Material-Properties auslesen (Lambda, Dichte, etc.)
    
    Returns:
        LayerStructure oder None (wenn keine Material-Info vorhanden)
    """
    try:
        # Material-Zuordnung finden
        material_association = None
        for rel in ifc_file.get_inverse(ifc_element):
            if rel.is_a('IfcRelAssociatesMaterial'):
                material_association = rel.RelatingMaterial
                break
        
        if not material_association:
            return None
        
        # Material-Layer-Set extrahieren
        layer_set = None
        layer_set_guid = None
        
        if material_association.is_a('IfcMaterialLayerSetUsage'):
            layer_set = material_association.ForLayerSet
            layer_set_guid = layer_set.id() if hasattr(layer_set, 'id') else None
        elif material_association.is_a('IfcMaterialLayerSet'):
            layer_set = material_association
            layer_set_guid = layer_set.id() if hasattr(layer_set, 'id') else None
        elif material_association.is_a('IfcMaterial'):
            # Einzelnes Material (keine Schichten)
            return _create_single_material_structure(
                ifc_element, 
                material_association
            )
        else:
            return None
        
        if not layer_set or not hasattr(layer_set, 'MaterialLayers'):
            return None
        
        # Schichten extrahieren
        layers = []
        total_thickness = 0.0
        
        for i, ifc_layer in enumerate(layer_set.MaterialLayers):
            material = ifc_layer.Material
            thickness = ifc_layer.LayerThickness if hasattr(ifc_layer, 'LayerThickness') else 0.0
            
            # Material-Properties extrahieren
            lambda_value, density, specific_heat = _extract_material_properties(
                material, 
                ifc_file
            )
            
            layer = MaterialLayer(
                position=i + 1,
                material_name=material.Name if material.Name else f"Material {i+1}",
                thickness=thickness,
                lambda_value=lambda_value,
                density=density,
                specific_heat=specific_heat,
                ifc_material_guid=material.id() if hasattr(material, 'id') else None
            )
            
            layers.append(layer)
            total_thickness += thickness
        
        # U-Wert berechnen (vereinfacht)
        u_value = _calculate_u_value(layers) if layers else None
        
        # LayerStructure erstellen
        structure = LayerStructure(
            ifc_guid=ifc_element.GlobalId,
            name=layer_set.LayerSetName if hasattr(layer_set, 'LayerSetName') and layer_set.LayerSetName else ifc_element.Name or "Unbenannt",
            element_type=ifc_element.is_a().replace('Ifc', '').upper(),
            layers=layers,
            total_thickness=total_thickness,
            u_value_calculated=u_value,
            ifc_material_layer_set_guid=layer_set_guid
        )
        
        return structure
        
    except Exception as e:
        print(f"Fehler beim Extrahieren von Material-Layers für {ifc_element.GlobalId}: {e}")
        return None


def _create_single_material_structure(
    ifc_element, 
    ifc_material
) -> LayerStructure:
    """Erstellt LayerStructure für Elemente mit nur einem Material"""
    
    lambda_value, density, specific_heat = _extract_material_properties(
        ifc_material, 
        None
    )
    
    # Dicke schätzen (falls nicht verfügbar)
    thickness = 0.24  # Default 24cm
    
    layer = MaterialLayer(
        position=1,
        material_name=ifc_material.Name if ifc_material.Name else "Unbekanntes Material",
        thickness=thickness,
        lambda_value=lambda_value,
        density=density,
        specific_heat=specific_heat,
        ifc_material_guid=ifc_material.id() if hasattr(ifc_material, 'id') else None
    )
    
    u_value = _calculate_u_value([layer]) if lambda_value else None
    
    return LayerStructure(
        ifc_guid=ifc_element.GlobalId,
        name=ifc_element.Name or "Unbenannt",
        element_type=ifc_element.is_a().replace('Ifc', '').upper(),
        layers=[layer],
        total_thickness=thickness,
        u_value_calculated=u_value,
        ifc_material_layer_set_guid=None
    )


def _extract_material_properties(
    ifc_material, 
    ifc_file
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Extrahiert Material-Properties aus IFC
    
    Returns:
        (lambda, density, specific_heat)
    """
    lambda_value = None
    density = None
    specific_heat = None
    
    try:
        # PropertySets durchsuchen
        if ifc_file and hasattr(ifc_material, 'HasProperties'):
            for prop_set in ifc_material.HasProperties:
                if not hasattr(prop_set, 'Properties'):
                    continue
                
                for prop in prop_set.Properties:
                    if not hasattr(prop, 'Name') or not hasattr(prop, 'NominalValue'):
                        continue
                    
                    name = prop.Name.lower()
                    value = prop.NominalValue.wrappedValue if hasattr(prop.NominalValue, 'wrappedValue') else None
                    
                    # Lambda (Wärmeleitfähigkeit)
                    if 'thermal' in name and 'conductivity' in name:
                        lambda_value = float(value) if value else None
                    
                    # Dichte
                    elif 'density' in name or 'massdensity' in name:
                        density = float(value) if value else None
                    
                    # Spezifische Wärmekapazität
                    elif 'specific' in name and 'heat' in name:
                        specific_heat = float(value) if value else None
        
    except Exception as e:
        print(f"Fehler beim Extrahieren von Material-Properties: {e}")
    
    return lambda_value, density, specific_heat


def _calculate_u_value(layers: List[MaterialLayer]) -> Optional[float]:
    """
    Berechnet U-Wert aus Schichten (vereinfacht nach DIN EN ISO 6946)
    
    U = 1 / (Rsi + ΣR + Rse)
    R = d / λ
    
    Rsi = 0.13 (Innen)
    Rse = 0.04 (Außen)
    """
    try:
        # Wärmewiderstände
        r_si = 0.13  # Innerer Wärmeübergangswiderstand
        r_se = 0.04  # Äußerer Wärmeübergangswiderstand
        
        # Schichtwiderstände
        r_layers = 0.0
        for layer in layers:
            if layer.lambda_value and layer.lambda_value > 0:
                r_layers += layer.thickness / layer.lambda_value
            else:
                # Wenn Lambda fehlt, können wir keinen U-Wert berechnen
                return None
        
        # Gesamt-Wärmewiderstand
        r_total = r_si + r_layers + r_se
        
        # U-Wert
        u_value = 1.0 / r_total if r_total > 0 else None
        
        return round(u_value, 3) if u_value else None
        
    except Exception as e:
        print(f"Fehler bei U-Wert-Berechnung: {e}")
        return None


def layer_structure_to_dict(structure: LayerStructure) -> Dict[str, Any]:
    """Konvertiert LayerStructure zu Dictionary für Sidecar JSON"""
    return {
        "id": f"LS-{structure.ifc_guid[:8]}",
        "name": structure.name,
        "type": structure.element_type,
        "layers": [
            {
                "position": layer.position,
                "material_name": layer.material_name,
                "thickness": round(layer.thickness, 4),
                "lambda": round(layer.lambda_value, 4) if layer.lambda_value else None,
                "density": round(layer.density, 2) if layer.density else None,
                "specific_heat": round(layer.specific_heat, 2) if layer.specific_heat else None,
                "ifc_material_guid": layer.ifc_material_guid
            }
            for layer in structure.layers
        ],
        "total_thickness": round(structure.total_thickness, 4),
        "u_value_calculated": structure.u_value_calculated,
        "source": "ifc_material_layer_set",
        "ifc_material_layer_set_guid": structure.ifc_material_layer_set_guid
    }
