#!/usr/bin/env python3
"""
Systematische Slab-Analyse basierend auf IFC Best Practices
Nutzt PredefinedType, IsExternal, Decomposes und andere Kriterien
"""

import sys
import ifcopenshell
import ifcopenshell.util.element
from pathlib import Path
from collections import defaultdict

def analyze_slabs_systematic(ifc_path: str):
    """Systematische Slab-Analyse nach Best Practices"""
    
    print(f"\n{'='*80}")
    print(f"📐 SYSTEMATISCHE SLAB-ANALYSE (Best Practices)")
    print(f"{'='*80}\n")
    
    ifc_file = ifcopenshell.open(ifc_path)
    slabs = ifc_file.by_type('IfcSlab')
    
    print(f"📊 Total: {len(slabs)} IfcSlab Elemente\n")
    
    # Gruppierung nach verschiedenen Kriterien
    by_predefined = defaultdict(list)
    by_parent_type = defaultdict(list)
    by_is_external = defaultdict(list)
    
    print(f"{'─'*80}")
    print(f"DETAILLIERTE SLAB-ANALYSE")
    print(f"{'─'*80}\n")
    
    for i, slab in enumerate(slabs, 1):
        print(f"Slab #{i}: {slab.Name or 'Unnamed'} (GUID: {slab.GlobalId[:8]}...)")
        
        # 1. PredefinedType (primärer Klassifikator)
        pred_type = str(slab.PredefinedType) if hasattr(slab, 'PredefinedType') else 'NOTDEFINED'
        print(f"   PredefinedType:    {pred_type}")
        by_predefined[pred_type].append(slab)
        
        # 2. IsExternal Property (für Dächer/externe Slabs)
        try:
            psets = ifcopenshell.util.element.get_psets(slab)
            is_external = psets.get('Pset_SlabCommon', {}).get('IsExternal', None)
            print(f"   IsExternal:        {is_external}")
            by_is_external[str(is_external)].append(slab)
        except:
            print(f"   IsExternal:        N/A")
        
        # 3. Parent via Decomposes (IfcRelAggregates)
        parent_info = "Keine"
        if hasattr(slab, 'Decomposes') and slab.Decomposes:
            for rel in slab.Decomposes:
                parent = rel.RelatingObject
                parent_info = f"{parent.is_a()}: {parent.Name}"
                by_parent_type[parent.is_a()].append(slab)
        print(f"   Parent (Decomposes): {parent_info}")
        
        # 4. Geschoss
        storey_info = "Keine"
        if hasattr(slab, 'ContainedInStructure'):
            for rel in slab.ContainedInStructure:
                if rel.RelatingStructure.is_a('IfcBuildingStorey'):
                    storey = rel.RelatingStructure
                    storey_info = storey.Name
        print(f"   Geschoss:          {storey_info}")
        
        # 5. Geometrie
        has_geom = "✅" if (hasattr(slab, 'Representation') and slab.Representation) else "❌"
        print(f"   Geometrie:         {has_geom}")
        
        print()
    
    # Zusammenfassung
    print(f"{'='*80}")
    print(f"ZUSAMMENFASSUNG")
    print(f"{'='*80}\n")
    
    print(f"📋 Nach PredefinedType:")
    for pred_type, slab_list in sorted(by_predefined.items()):
        print(f"   {pred_type:20} {len(slab_list):3} Slabs")
    
    print(f"\n🔗 Nach Parent-Typ:")
    for parent_type, slab_list in sorted(by_parent_type.items()):
        print(f"   {parent_type:20} {len(slab_list):3} Slabs")
    
    print(f"\n🌍 Nach IsExternal:")
    for is_ext, slab_list in sorted(by_is_external.items()):
        print(f"   {is_ext:20} {len(slab_list):3} Slabs")
    
    # Empfehlungen
    print(f"\n{'='*80}")
    print(f"💡 KLASSIFIZIERUNGS-EMPFEHLUNGEN")
    print(f"{'='*80}\n")
    
    roof_slabs = by_parent_type.get('IfcRoof', [])
    if roof_slabs:
        print(f"✅ DACH-SLABS: {len(roof_slabs)} Slabs haben IfcRoof als Parent")
        print(f"   → Diese sollten als ROOF klassifiziert werden")
        print(f"   → Flächen sollten zum Parent-Dach aggregiert werden\n")
    
    standalone_slabs = [s for s in slabs if not (hasattr(s, 'Decomposes') and s.Decomposes)]
    if standalone_slabs:
        print(f"⚠️  STANDALONE SLABS: {len(standalone_slabs)} Slabs ohne Parent")
        print(f"   → Klassifizierung über PredefinedType oder IsExternal")
        print(f"   → Oder über Geschoss-Position (oberste = Dach, unterste = Boden)\n")
    
    print(f"{'='*80}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python systematic-slab-analysis.py <ifc-file>")
        sys.exit(1)
    
    ifc_path = sys.argv[1]
    
    if not Path(ifc_path).exists():
        print(f"❌ Datei nicht gefunden: {ifc_path}")
        sys.exit(1)
    
    analyze_slabs_systematic(ifc_path)
