#!/usr/bin/env python3
"""
Tiefgehende IFC-Analyse mit ifcopenshell
Zeigt alle Details über IFC-Elemente, Beziehungen und Geometrie
"""

import sys
import ifcopenshell
import ifcopenshell.geom
from pathlib import Path

def deep_analyze_element(element, ifc_file):
    """Tiefgehende Analyse eines einzelnen IFC-Elements"""
    
    print(f"\n{'─'*70}")
    print(f"🔍 DEEP DIVE: {element.Name or element.is_a()}")
    print(f"{'─'*70}")
    
    # Basis-Infos
    print(f"\n📋 Basis-Informationen:")
    print(f"   Typ:              {element.is_a()}")
    print(f"   GUID:             {element.GlobalId}")
    print(f"   Name:             {element.Name}")
    print(f"   Description:      {element.Description if hasattr(element, 'Description') else 'N/A'}")
    print(f"   Tag:              {element.Tag if hasattr(element, 'Tag') else 'N/A'}")
    print(f"   ObjectType:       {element.ObjectType if hasattr(element, 'ObjectType') else 'N/A'}")
    
    # Representation Details
    print(f"\n🎨 Geometrie/Representation:")
    if hasattr(element, 'Representation') and element.Representation:
        rep = element.Representation
        print(f"   Representation:   ✅ Vorhanden")
        print(f"   Typ:              {rep.is_a()}")
        
        if hasattr(rep, 'Representations'):
            print(f"   Anzahl Reps:      {len(rep.Representations)}")
            for i, r in enumerate(rep.Representations, 1):
                print(f"\n   Rep #{i}:")
                print(f"      Type:          {r.RepresentationType}")
                print(f"      Identifier:    {r.RepresentationIdentifier if hasattr(r, 'RepresentationIdentifier') else 'N/A'}")
                if hasattr(r, 'Items'):
                    print(f"      Items:         {len(r.Items)} Geometrie-Items")
                    for j, item in enumerate(r.Items[:3], 1):
                        print(f"         Item {j}:    {item.is_a()}")
    else:
        print(f"   Representation:   ❌ FEHLT!")
        print(f"   → Keine Geometrie-Daten im IFC")
        print(f"   → Muss aus EVEBI oder anderen Quellen ergänzt werden")
    
    # ObjectPlacement
    print(f"\n📍 Platzierung:")
    if hasattr(element, 'ObjectPlacement') and element.ObjectPlacement:
        placement = element.ObjectPlacement
        print(f"   Placement:        ✅ {placement.is_a()}")
        if hasattr(placement, 'RelativePlacement'):
            rel_place = placement.RelativePlacement
            print(f"   Relative:         {rel_place.is_a()}")
            if hasattr(rel_place, 'Location'):
                loc = rel_place.Location
                if hasattr(loc, 'Coordinates'):
                    coords = loc.Coordinates
                    print(f"   Koordinaten:      X={coords[0]:.2f}, Y={coords[1]:.2f}, Z={coords[2]:.2f}")
    else:
        print(f"   Placement:        ❌ Keine Platzierung")
    
    # Material
    print(f"\n🧱 Material:")
    found_material = False
    if hasattr(element, 'HasAssociations'):
        for assoc in element.HasAssociations:
            if assoc.is_a('IfcRelAssociatesMaterial'):
                mat = assoc.RelatingMaterial
                print(f"   Material:         ✅ {mat.is_a()}")
                if hasattr(mat, 'Name'):
                    print(f"   Name:             {mat.Name}")
                
                # Material-Layers
                if mat.is_a('IfcMaterialLayerSetUsage') or mat.is_a('IfcMaterialLayerSet'):
                    layer_set = mat.ForLayerSet if hasattr(mat, 'ForLayerSet') else mat
                    if hasattr(layer_set, 'MaterialLayers'):
                        print(f"   Layers:           {len(layer_set.MaterialLayers)} Schichten")
                        for i, layer in enumerate(layer_set.MaterialLayers, 1):
                            print(f"      Layer {i}:      {layer.Material.Name} ({layer.LayerThickness}mm)")
                
                found_material = True
    
    if not found_material:
        print(f"   Material:         ❌ Kein Material zugewiesen")
    
    # Properties
    print(f"\n⚙️  Properties:")
    if hasattr(element, 'IsDefinedBy'):
        prop_count = 0
        for definition in element.IsDefinedBy:
            if definition.is_a('IfcRelDefinesByProperties'):
                pset = definition.RelatingPropertyDefinition
                if pset.is_a('IfcPropertySet'):
                    print(f"\n   PropertySet: {pset.Name}")
                    for prop in pset.HasProperties:
                        if prop.is_a('IfcPropertySingleValue'):
                            value = prop.NominalValue.wrappedValue if prop.NominalValue else 'N/A'
                            print(f"      {prop.Name:20} = {value}")
                            prop_count += 1
        
        if prop_count == 0:
            print(f"   Keine Properties gefunden")
    else:
        print(f"   Keine Properties")
    
    # Beziehungen
    print(f"\n🔗 Beziehungen:")
    
    # Geschoss
    if hasattr(element, 'ContainedInStructure'):
        for rel in element.ContainedInStructure:
            if rel.RelatingStructure.is_a('IfcBuildingStorey'):
                storey = rel.RelatingStructure
                print(f"   Geschoss:         {storey.Name} (GUID: {storey.GlobalId[:8]}...)")
    
    # Typ-Beziehung
    if hasattr(element, 'IsTypedBy'):
        for rel in element.IsTypedBy:
            elem_type = rel.RelatingType
            print(f"   Typ:              {elem_type.Name} ({elem_type.is_a()})")
    
    # Öffnungen (für Wände)
    if hasattr(element, 'HasOpenings'):
        print(f"   Öffnungen:        {len(element.HasOpenings)} Öffnungen")
        for rel in element.HasOpenings[:3]:  # Erste 3
            opening = rel.RelatedOpeningElement
            print(f"      → {opening.Name or 'Unnamed'} (GUID: {opening.GlobalId[:8]}...)")
            
            # Was füllt die Öffnung?
            if hasattr(opening, 'HasFillings'):
                for fill_rel in opening.HasFillings:
                    filling = fill_rel.RelatedBuildingElement
                    print(f"         Gefüllt mit: {filling.Name} ({filling.is_a()})")
    
    # Räumliche Struktur
    if hasattr(element, 'Decomposes'):
        for rel in element.Decomposes:
            parent = rel.RelatingObject
            print(f"   Teil von:         {parent.Name} ({parent.is_a()})")
    
    print(f"\n{'─'*70}\n")


def analyze_ifc_deep(ifc_path: str):
    """Tiefgehende IFC-Analyse"""
    
    print(f"\n{'='*70}")
    print(f"🔬 TIEFGEHENDE IFC-ANALYSE")
    print(f"{'='*70}\n")
    print(f"Datei: {Path(ifc_path).name}\n")
    
    # IFC-Datei laden
    ifc_file = ifcopenshell.open(ifc_path)
    
    # Projekt-Info
    project = ifc_file.by_type('IfcProject')[0]
    print(f"📁 Projekt: {project.Name}")
    print(f"   Schema: {ifc_file.schema}")
    print(f"   Anzahl Entities: {len(list(ifc_file))}")
    
    # Alle Dächer analysieren
    roofs = ifc_file.by_type('IfcRoof')
    print(f"\n{'='*70}")
    print(f"🏠 DÄCHER - Tiefgehende Analyse ({len(roofs)} Elemente)")
    print(f"{'='*70}")
    
    for roof in roofs:
        deep_analyze_element(roof, ifc_file)
    
    # Prüfe ob es IfcSpace gibt (Räume mit Geometrie)
    spaces = ifc_file.by_type('IfcSpace')
    if spaces:
        print(f"\n{'='*70}")
        print(f"🏠 RÄUME - Übersicht ({len(spaces)} Elemente)")
        print(f"{'='*70}\n")
        
        for space in spaces[:2]:  # Erste 2 Räume
            print(f"Raum: {space.Name or space.LongName}")
            print(f"   GUID:             {space.GlobalId}")
            print(f"   Geometrie:        {'✅' if space.Representation else '❌'}")
            
            # Geschoss
            if hasattr(space, 'Decomposes'):
                for rel in space.Decomposes:
                    parent = rel.RelatingObject
                    if parent.is_a('IfcBuildingStorey'):
                        print(f"   Geschoss:         {parent.Name}")
            print()
    
    # Prüfe IfcBuildingElementProxy (manchmal werden Dächer so modelliert)
    proxies = ifc_file.by_type('IfcBuildingElementProxy')
    if proxies:
        print(f"\n{'='*70}")
        print(f"🔧 PROXY-ELEMENTE ({len(proxies)} Elemente)")
        print(f"{'='*70}\n")
        
        for proxy in proxies[:3]:
            print(f"Proxy: {proxy.Name}")
            print(f"   Typ:              {proxy.ObjectType if hasattr(proxy, 'ObjectType') else 'N/A'}")
            print(f"   Geometrie:        {'✅' if proxy.Representation else '❌'}")
            print()
    
    # Geometrie-Statistik
    print(f"\n{'='*70}")
    print(f"📊 GEOMETRIE-STATISTIK")
    print(f"{'='*70}\n")
    
    element_types = ['IfcWall', 'IfcRoof', 'IfcSlab', 'IfcWindow', 'IfcDoor']
    
    for elem_type in element_types:
        elements = ifc_file.by_type(elem_type)
        if elements:
            with_geom = sum(1 for e in elements if hasattr(e, 'Representation') and e.Representation)
            without_geom = len(elements) - with_geom
            
            print(f"{elem_type:20} Total: {len(elements):3}  Mit Geometrie: {with_geom:3}  Ohne: {without_geom:3}")
    
    print(f"\n{'='*70}")
    print(f"✅ Tiefgehende Analyse abgeschlossen")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python deep-analyze-ifc.py <ifc-file>")
        print("\nBeispiel:")
        print("  python deep-analyze-ifc.py sources/IFC_EVBI/DIN18599TestIFCv2.ifc")
        sys.exit(1)
    
    ifc_path = sys.argv[1]
    
    if not Path(ifc_path).exists():
        print(f"❌ Datei nicht gefunden: {ifc_path}")
        sys.exit(1)
    
    analyze_ifc_deep(ifc_path)
