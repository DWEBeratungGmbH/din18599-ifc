#!/usr/bin/env python3
"""
IFC-Analyse-Tool
Zeigt detaillierte Informationen über IFC-Elemente
"""

import sys
import ifcopenshell
from pathlib import Path

def analyze_ifc(ifc_path: str):
    """Analysiert eine IFC-Datei und zeigt Details"""
    
    print(f"\n{'='*60}")
    print(f"IFC-Analyse: {Path(ifc_path).name}")
    print(f"{'='*60}\n")
    
    # IFC-Datei laden
    ifc_file = ifcopenshell.open(ifc_path)
    
    # Projekt-Info
    project = ifc_file.by_type('IfcProject')[0]
    print(f"📁 Projekt: {project.Name}")
    print(f"   Schema: {ifc_file.schema}")
    print()
    
    # Gebäude-Info
    buildings = ifc_file.by_type('IfcBuilding')
    if buildings:
        building = buildings[0]
        print(f"🏢 Gebäude: {building.Name}")
        print(f"   GUID: {building.GlobalId}")
        print()
    
    # Element-Typen zählen
    print("📊 Element-Übersicht:")
    element_types = {
        'IfcWall': 'Wände',
        'IfcRoof': 'Dächer',
        'IfcSlab': 'Decken/Böden',
        'IfcWindow': 'Fenster',
        'IfcDoor': 'Türen',
        'IfcSpace': 'Räume',
        'IfcBuildingStorey': 'Geschosse'
    }
    
    for ifc_type, label in element_types.items():
        elements = ifc_file.by_type(ifc_type)
        if elements:
            print(f"   {label:20} {len(elements):3} Elemente")
    print()
    
    # Detaillierte Dach-Analyse
    roofs = ifc_file.by_type('IfcRoof')
    if roofs:
        print(f"{'='*60}")
        print(f"🏠 DÄCHER - Detailanalyse ({len(roofs)} Elemente)")
        print(f"{'='*60}\n")
        
        for i, roof in enumerate(roofs, 1):
            print(f"Dach #{i}:")
            print(f"   Name:           {roof.Name}")
            print(f"   GUID:           {roof.GlobalId}")
            print(f"   Tag:            {roof.Tag if hasattr(roof, 'Tag') else 'N/A'}")
            print(f"   Typ:            {roof.is_a()}")
            
            # Representation prüfen
            if hasattr(roof, 'Representation') and roof.Representation:
                print(f"   Representation: ✅ Vorhanden")
                rep = roof.Representation
                if hasattr(rep, 'Representations'):
                    for r in rep.Representations:
                        print(f"      - {r.RepresentationType}: {len(r.Items) if hasattr(r, 'Items') else 0} Items")
            else:
                print(f"   Representation: ❌ FEHLT (keine Geometrie!)")
            
            # Material
            if hasattr(roof, 'HasAssociations'):
                for assoc in roof.HasAssociations:
                    if assoc.is_a('IfcRelAssociatesMaterial'):
                        mat = assoc.RelatingMaterial
                        print(f"   Material:       {mat.Name if hasattr(mat, 'Name') else mat}")
            
            # Geschoss
            if hasattr(roof, 'ContainedInStructure'):
                for rel in roof.ContainedInStructure:
                    if rel.RelatingStructure.is_a('IfcBuildingStorey'):
                        print(f"   Geschoss:       {rel.RelatingStructure.Name}")
            
            # Properties
            if hasattr(roof, 'IsDefinedBy'):
                props = []
                for definition in roof.IsDefinedBy:
                    if definition.is_a('IfcRelDefinesByProperties'):
                        pset = definition.RelatingPropertyDefinition
                        if pset.is_a('IfcPropertySet'):
                            for prop in pset.HasProperties:
                                if prop.is_a('IfcPropertySingleValue'):
                                    props.append(f"{prop.Name}={prop.NominalValue.wrappedValue if prop.NominalValue else 'N/A'}")
                if props:
                    print(f"   Properties:     {', '.join(props[:3])}")
            
            print()
    
    # Decken/Böden-Analyse
    slabs = ifc_file.by_type('IfcSlab')
    if slabs:
        print(f"{'='*60}")
        print(f"📐 DECKEN/BÖDEN - Übersicht ({len(slabs)} Elemente)")
        print(f"{'='*60}\n")
        
        for i, slab in enumerate(slabs[:5], 1):  # Nur erste 5
            name = slab.Name or "Unnamed"
            print(f"   {i}. {name:30} GUID: {slab.GlobalId[:8]}... {'✅' if slab.Representation else '❌'}")
        
        if len(slabs) > 5:
            print(f"   ... und {len(slabs)-5} weitere")
        print()
    
    # Fenster-Analyse
    windows = ifc_file.by_type('IfcWindow')
    if windows:
        print(f"{'='*60}")
        print(f"🪟 FENSTER - Übersicht ({len(windows)} Elemente)")
        print(f"{'='*60}\n")
        
        # Prüfe Parent-Child-Beziehungen
        windows_with_parent = 0
        for window in windows:
            if hasattr(window, 'FillsVoids'):
                for rel in window.FillsVoids:
                    if rel.RelatingOpeningElement:
                        opening = rel.RelatingOpeningElement
                        if hasattr(opening, 'VoidsElements'):
                            for void_rel in opening.VoidsElements:
                                if void_rel.RelatingBuildingElement:
                                    windows_with_parent += 1
                                    break
        
        print(f"   Fenster mit Parent-Wand: {windows_with_parent}/{len(windows)}")
        
        # Erste 3 Fenster im Detail
        for i, window in enumerate(windows[:3], 1):
            print(f"\n   Fenster #{i}:")
            print(f"      Name: {window.Name}")
            print(f"      GUID: {window.GlobalId}")
            
            # Parent-Wand finden
            if hasattr(window, 'FillsVoids'):
                for rel in window.FillsVoids:
                    if rel.RelatingOpeningElement:
                        opening = rel.RelatingOpeningElement
                        if hasattr(opening, 'VoidsElements'):
                            for void_rel in opening.VoidsElements:
                                if void_rel.RelatingBuildingElement:
                                    parent = void_rel.RelatingBuildingElement
                                    print(f"      Parent: {parent.Name} ({parent.GlobalId[:8]}...)")
        print()
    
    print(f"{'='*60}")
    print(f"✅ Analyse abgeschlossen")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze-ifc.py <ifc-file>")
        print("\nBeispiel:")
        print("  python analyze-ifc.py sources/IFC_EVBI/DIN18599TestIFCv2.ifc")
        sys.exit(1)
    
    ifc_path = sys.argv[1]
    
    if not Path(ifc_path).exists():
        print(f"❌ Datei nicht gefunden: {ifc_path}")
        sys.exit(1)
    
    analyze_ifc(ifc_path)
