#!/usr/bin/env python3
"""
Analysiert die Beziehung zwischen IfcRoof und IfcSlab
Zeigt welche Slabs zu welchem Dach gehören
"""

import sys
import ifcopenshell
import ifcopenshell.geom
from pathlib import Path

def analyze_roof_slabs(ifc_path: str):
    """Analysiert Dach-Slab-Beziehungen"""
    
    print(f"\n{'='*70}")
    print(f"🏠 DACH-FLÄCHEN ANALYSE")
    print(f"{'='*70}\n")
    
    ifc_file = ifcopenshell.open(ifc_path)
    
    # Geometrie-Settings
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    
    # Alle Dächer
    roofs = ifc_file.by_type('IfcRoof')
    print(f"📊 Gefunden: {len(roofs)} Dächer\n")
    
    for roof in roofs:
        print(f"{'─'*70}")
        print(f"🏠 {roof.Name} (GUID: {roof.GlobalId})")
        print(f"{'─'*70}")
        
        # Finde zugehörige Slabs über verschiedene Beziehungen
        related_slabs = []
        
        # 1. IsDecomposedBy (Dach → Slabs)
        if hasattr(roof, 'IsDecomposedBy'):
            for rel in roof.IsDecomposedBy:
                for elem in rel.RelatedObjects:
                    if elem.is_a('IfcSlab'):
                        related_slabs.append(('IsDecomposedBy', elem))
        
        # 2. Slabs die "Decomposes" auf dieses Dach haben
        all_slabs = ifc_file.by_type('IfcSlab')
        for slab in all_slabs:
            if hasattr(slab, 'Decomposes'):
                for rel in slab.Decomposes:
                    if rel.RelatingObject.GlobalId == roof.GlobalId:
                        related_slabs.append(('Decomposes', slab))
        
        # 3. Slabs im gleichen Geschoss mit "Dach" im Namen
        roof_storey = None
        if hasattr(roof, 'ContainedInStructure'):
            for rel in roof.ContainedInStructure:
                if rel.RelatingStructure.is_a('IfcBuildingStorey'):
                    roof_storey = rel.RelatingStructure
        
        if roof_storey:
            for slab in all_slabs:
                if hasattr(slab, 'ContainedInStructure'):
                    for rel in slab.ContainedInStructure:
                        if rel.RelatingStructure.GlobalId == roof_storey.GlobalId:
                            # Prüfe ob Slab zum Dach gehört (Name-Matching)
                            slab_name = (slab.Name or "").lower()
                            roof_name = roof.Name.lower()
                            
                            # Extrahiere Dach-Nummer
                            roof_num = None
                            if "dach" in roof_name:
                                import re
                                match = re.search(r'dach\s*(\d+)', roof_name)
                                if match:
                                    roof_num = match.group(1)
                            
                            # Prüfe ob Slab diese Nummer hat
                            if roof_num and roof_num in slab_name:
                                # Prüfe ob nicht schon in Liste
                                if not any(s[1].GlobalId == slab.GlobalId for s in related_slabs):
                                    related_slabs.append(('SameStorey+Name', slab))
        
        # Zeige gefundene Slabs
        if related_slabs:
            print(f"\n✅ Gefunden: {len(related_slabs)} Dachflächen (Slabs)\n")
            
            total_area = 0.0
            
            for i, (method, slab) in enumerate(related_slabs, 1):
                slab_name = slab.Name or f"Unnamed Slab {slab.GlobalId[:8]}"
                
                # Berechne Fläche
                area = 0.0
                try:
                    shape = ifcopenshell.geom.create_shape(settings, slab)
                    
                    # Fläche aus Bounding Box
                    verts = shape.geometry.verts
                    if verts and len(verts) >= 9:
                        xs = [verts[i] for i in range(0, len(verts), 3)]
                        ys = [verts[i] for i in range(1, len(verts), 3)]
                        
                        width = max(xs) - min(xs)
                        depth = max(ys) - min(ys)
                        area = width * depth
                        total_area += area
                except:
                    pass
                
                print(f"   {i}. {slab_name:30} {area:8.2f} m²  (via {method})")
            
            print(f"\n   {'─'*60}")
            print(f"   GESAMT-FLÄCHE:                   {total_area:8.2f} m²")
            print()
        else:
            print(f"\n❌ Keine Dachflächen gefunden\n")
    
    print(f"{'='*70}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze-roof-slabs.py <ifc-file>")
        sys.exit(1)
    
    ifc_path = sys.argv[1]
    
    if not Path(ifc_path).exists():
        print(f"❌ Datei nicht gefunden: {ifc_path}")
        sys.exit(1)
    
    analyze_roof_slabs(ifc_path)
