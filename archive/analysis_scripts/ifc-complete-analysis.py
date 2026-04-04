#!/usr/bin/env python3
"""
Umfassende IFC-Analyse nach 8-Schritte-Methode
Kombiniert alle Analyse-Funktionen in einem Skript

Usage:
    python ifc-complete-analysis.py <ifc-file> [--step STEP] [--detail]
    
Options:
    --step STEP    Nur einen bestimmten Schritt ausführen (1-8)
    --detail       Detaillierte Ausgabe
    --json         JSON-Export der Ergebnisse
"""

import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element


class IFCAnalyzer:
    """Umfassende IFC-Analyse nach Best Practices"""
    
    def __init__(self, ifc_path: str):
        self.ifc_path = ifc_path
        self.ifc_file = ifcopenshell.open(ifc_path)
        self.settings = ifcopenshell.geom.settings()
        self.settings.set(self.settings.USE_WORLD_COORDS, True)
        self.results = {}
    
    def analyze_all(self, detail: bool = False):
        """Führt alle 8 Analyse-Schritte aus"""
        print(f"\n{'='*80}")
        print(f"🔬 UMFASSENDE IFC-ANALYSE")
        print(f"{'='*80}\n")
        print(f"Datei: {Path(self.ifc_path).name}\n")
        
        self.step1_header()
        self.step2_spatial_structure()
        self.step3_building_elements()
        self.step4_properties()
        self.step5_materials()
        self.step6_relationships()
        self.step7_geometry()
        self.step8_validation()
        
        print(f"\n{'='*80}")
        print(f"✅ ANALYSE ABGESCHLOSSEN")
        print(f"{'='*80}\n")
        
        return self.results
    
    def step1_header(self):
        """Schritt 1: Header analysieren (Schema, Version, Software)"""
        print(f"{'─'*80}")
        print(f"1️⃣  HEADER - Schema, Version, Software")
        print(f"{'─'*80}\n")
        
        project = self.ifc_file.by_type('IfcProject')[0]
        
        header_info = {
            'schema': self.ifc_file.schema,
            'project_name': project.Name,
            'project_description': project.Description if hasattr(project, 'Description') else None,
            'total_entities': len(list(self.ifc_file))
        }
        
        print(f"   Schema:              {header_info['schema']}")
        print(f"   Projekt:             {header_info['project_name']}")
        if header_info['project_description']:
            print(f"   Beschreibung:        {header_info['project_description']}")
        print(f"   Anzahl Entities:     {header_info['total_entities']}")
        print()
        
        self.results['header'] = header_info
    
    def step2_spatial_structure(self):
        """Schritt 2: Räumliche Struktur (Projekt → Site → Gebäude → Geschosse)"""
        print(f"{'─'*80}")
        print(f"2️⃣  RÄUMLICHE STRUKTUR - Projekt → Site → Gebäude → Geschosse")
        print(f"{'─'*80}\n")
        
        # Site
        sites = self.ifc_file.by_type('IfcSite')
        print(f"   🌍 Sites: {len(sites)}")
        for site in sites:
            print(f"      → {site.Name}")
        
        # Gebäude
        buildings = self.ifc_file.by_type('IfcBuilding')
        print(f"\n   🏢 Gebäude: {len(buildings)}")
        for building in buildings:
            print(f"      → {building.Name}")
        
        # Geschosse
        storeys = self.ifc_file.by_type('IfcBuildingStorey')
        print(f"\n   📐 Geschosse: {len(storeys)}")
        for storey in storeys:
            elevation = storey.Elevation if hasattr(storey, 'Elevation') else 'N/A'
            print(f"      → {storey.Name:30} Elevation: {elevation}")
        
        # Räume
        spaces = self.ifc_file.by_type('IfcSpace')
        print(f"\n   🏠 Räume: {len(spaces)}")
        
        print()
        
        self.results['spatial_structure'] = {
            'sites': len(sites),
            'buildings': len(buildings),
            'storeys': len(storeys),
            'spaces': len(spaces)
        }
    
    def step3_building_elements(self):
        """Schritt 3: Bauteile inventarisieren (Wände, Decken, Fenster, etc.)"""
        print(f"{'─'*80}")
        print(f"3️⃣  BAUTEILE - Inventarisierung")
        print(f"{'─'*80}\n")
        
        element_types = {
            'IfcWall': 'Wände',
            'IfcSlab': 'Decken/Böden',
            'IfcRoof': 'Dächer',
            'IfcWindow': 'Fenster',
            'IfcDoor': 'Türen',
            'IfcBeam': 'Träger',
            'IfcColumn': 'Stützen',
            'IfcStair': 'Treppen',
            'IfcRailing': 'Geländer'
        }
        
        element_counts = {}
        
        for ifc_type, label in element_types.items():
            elements = self.ifc_file.by_type(ifc_type)
            count = len(elements)
            element_counts[ifc_type] = count
            
            if count > 0:
                # Zähle mit/ohne Geometrie
                with_geom = sum(1 for e in elements if hasattr(e, 'Representation') and e.Representation)
                print(f"   {label:20} {count:3} Elemente  (Geometrie: {with_geom}/{count})")
        
        print()
        
        self.results['building_elements'] = element_counts
    
    def step4_properties(self):
        """Schritt 4: Properties und Quantities (Psets, Qtos)"""
        print(f"{'─'*80}")
        print(f"4️⃣  PROPERTIES - Psets und Quantities")
        print(f"{'─'*80}\n")
        
        # Analysiere Wände als Beispiel
        walls = self.ifc_file.by_type('IfcWall')
        
        if walls:
            print(f"   Beispiel: Erste Wand\n")
            wall = walls[0]
            print(f"   Name: {wall.Name}")
            
            try:
                psets = ifcopenshell.util.element.get_psets(wall)
                
                # Prüfe IsExternal (wichtig für AW/IW-Zuordnung!)
                is_external = psets.get('Pset_WallCommon', {}).get('IsExternal', None)
                
                if psets:
                    for pset_name, props in psets.items():
                        if not pset_name.startswith('Qto'):  # Nur Psets, keine Quantities
                            print(f"\n   PropertySet: {pset_name}")
                            for prop_name, prop_value in props.items():
                                if prop_name != 'id':  # Überspringe interne ID
                                    print(f"      {prop_name:30} = {prop_value}")
                else:
                    print(f"   ⚠️  Keine Properties gefunden")
                
                # Validiere IsExternal für Außenwände
                if is_external == False and 'AW' in wall.Name:
                    print(f"\n   ❌ FEHLER: Wand '{wall.Name}' ist als Außenwand benannt, aber IsExternal=False!")
                    
            except Exception as e:
                print(f"   ⚠️  Fehler beim Lesen der Properties: {e}")
        
        print()
        
        # Zähle Property Sets
        all_psets = set()
        for element in self.ifc_file.by_type('IfcElement'):
            try:
                psets = ifcopenshell.util.element.get_psets(element)
                all_psets.update(psets.keys())
            except:
                pass
        
        print(f"   📊 Gesamt: {len(all_psets)} verschiedene Property Sets gefunden")
        print()
        
        self.results['properties'] = {
            'total_psets': len(all_psets),
            'pset_names': list(all_psets)
        }
    
    def step5_materials(self):
        """Schritt 5: Materialien und Schichten"""
        print(f"{'─'*80}")
        print(f"5️⃣  MATERIALIEN - Materialien und Schichtaufbauten")
        print(f"{'─'*80}\n")
        
        # Alle Materialien
        materials = self.ifc_file.by_type('IfcMaterial')
        print(f"   📦 Materialien: {len(materials)}")
        for mat in materials:
            print(f"      → {mat.Name}")
        
        # Material Layer Sets
        layer_sets = self.ifc_file.by_type('IfcMaterialLayerSet')
        print(f"\n   📚 Material Layer Sets: {len(layer_sets)}")
        
        for i, layer_set in enumerate(layer_sets[:3], 1):  # Erste 3
            print(f"\n   Layer Set #{i}: {layer_set.LayerSetName if hasattr(layer_set, 'LayerSetName') else 'Unnamed'}")
            if hasattr(layer_set, 'MaterialLayers'):
                total_thickness = 0
                for layer in layer_set.MaterialLayers:
                    thickness = layer.LayerThickness
                    total_thickness += thickness
                    print(f"      → {layer.Material.Name:30} {thickness*1000:.1f} mm")
                print(f"      {'─'*50}")
                print(f"      Gesamt-Dicke:                    {total_thickness*1000:.1f} mm")
        
        print()
        
        self.results['materials'] = {
            'total_materials': len(materials),
            'total_layer_sets': len(layer_sets)
        }
    
    def step6_relationships(self):
        """Schritt 6: Beziehungen (IfcRel...)"""
        print(f"{'─'*80}")
        print(f"6️⃣  BEZIEHUNGEN - Aggregation, Zuordnung, Typen")
        print(f"{'─'*80}\n")
        
        # Verschiedene Relationship-Typen
        rel_types = {
            'IfcRelAggregates': 'Aggregation (Parent-Child)',
            'IfcRelContainedInSpatialStructure': 'Räumliche Zuordnung',
            'IfcRelDefinesByType': 'Typ-Zuordnung',
            'IfcRelDefinesByProperties': 'Property-Zuordnung',
            'IfcRelAssociatesMaterial': 'Material-Zuordnung',
            'IfcRelVoidsElement': 'Öffnungen (Voids)',
            'IfcRelFillsElement': 'Füllungen (Fenster/Türen)',
            'IfcRelSpaceBoundary': 'Raum-Grenzen'
        }
        
        rel_counts = {}
        
        for rel_type, label in rel_types.items():
            rels = self.ifc_file.by_type(rel_type)
            count = len(rels)
            rel_counts[rel_type] = count
            
            status = "✅" if count > 0 else "❌"
            print(f"   {status} {label:40} {count:4} Beziehungen")
        
        print()
        
        # Spezial-Analyse: Fenster-Wand-Beziehungen
        windows = self.ifc_file.by_type('IfcWindow')
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
        
        if windows:
            print(f"   💡 Fenster-Wand-Beziehungen: {windows_with_parent}/{len(windows)} Fenster haben Parent-Wand")
            print()
        
        self.results['relationships'] = rel_counts
    
    def step7_geometry(self):
        """Schritt 7: Geometrie-Repräsentation"""
        print(f"{'─'*80}")
        print(f"7️⃣  GEOMETRIE - Repräsentation und Berechnungen")
        print(f"{'─'*80}\n")
        
        # Analysiere Slabs im Detail (wichtig für Dächer)
        slabs = self.ifc_file.by_type('IfcSlab')
        
        by_predefined = defaultdict(list)
        by_parent = defaultdict(list)
        by_representation = defaultdict(list)
        
        for slab in slabs:
            # PredefinedType (FLOOR, ROOF, BASESLAB)
            pred_type = str(slab.PredefinedType) if hasattr(slab, 'PredefinedType') else 'NOTDEFINED'
            by_predefined[pred_type].append(slab)
            
            # Geometrie-Typ prüfen (SweptSolid vs Clipping)
            if hasattr(slab, 'Representation') and slab.Representation:
                for rep in slab.Representation.Representations:
                    for item in rep.Items:
                        rep_type = item.is_a()
                        by_representation[rep_type].append(slab)
                        break
            
            # Parent
            if hasattr(slab, 'Decomposes') and slab.Decomposes:
                for rel in slab.Decomposes:
                    parent = rel.RelatingObject
                    parent_key = f"{parent.is_a()}: {parent.Name}"
                    by_parent[parent_key].append(slab)
        
        print(f"   📐 Slab-Analyse ({len(slabs)} Slabs):\n")
        
        print(f"   Nach PredefinedType:")
        for pred_type, slab_list in sorted(by_predefined.items()):
            print(f"      {pred_type:20} {len(slab_list):3} Slabs")
        
        print(f"\n   Nach Geometrie-Typ (Clipping-Erkennung):")
        for rep_type, slab_list in sorted(by_representation.items()):
            # Dedupliziere
            unique_slabs = list(set(s.GlobalId for s in slab_list))
            print(f"      {rep_type:30} {len(unique_slabs):3} Slabs")
        
        # Warne bei Clipping
        if 'IfcBooleanClippingResult' in by_representation:
            print(f"\n   ⚠️  WARNUNG: {len(set(s.GlobalId for s in by_representation['IfcBooleanClippingResult']))} Slabs nutzen Clipping!")
            print(f"      → Prüfe ob Deckenplatten am Dach geclippt wurden")
        
        if by_parent:
            print(f"\n   Nach Parent (Aggregation):")
            for parent_key, slab_list in sorted(by_parent.items()):
                print(f"      {parent_key:40} {len(slab_list):3} Slabs")
        
        # Dach-Flächen berechnen
        roofs = self.ifc_file.by_type('IfcRoof')
        
        if roofs:
            print(f"\n   🏠 Dach-Flächen (aus Slabs):\n")
            
            for roof in roofs:
                roof_area = 0.0
                slab_count = 0
                
                if hasattr(roof, 'IsDecomposedBy'):
                    for rel in roof.IsDecomposedBy:
                        for elem in rel.RelatedObjects:
                            if elem.is_a('IfcSlab'):
                                slab_count += 1
                                try:
                                    shape = ifcopenshell.geom.create_shape(self.settings, elem)
                                    # B1-FIX: Berechne aus Mesh-Faces, nicht BoundingBox!
                                    # BoundingBox gibt projizierte Fläche, bei 38° Neigung 27% zu klein
                                    verts = shape.geometry.verts
                                    faces = shape.geometry.faces
                                    
                                    if verts and faces:
                                        # Summiere Dreiecksflächen
                                        for i in range(0, len(faces), 3):
                                            try:
                                                idx1, idx2, idx3 = faces[i]*3, faces[i+1]*3, faces[i+2]*3
                                                v1 = (verts[idx1], verts[idx1+1], verts[idx1+2])
                                                v2 = (verts[idx2], verts[idx2+1], verts[idx2+2])
                                                v3 = (verts[idx3], verts[idx3+1], verts[idx3+2])
                                                
                                                # Heron's Formel für Dreiecksfläche
                                                a = ((v2[0]-v1[0])**2 + (v2[1]-v1[1])**2 + (v2[2]-v1[2])**2)**0.5
                                                b = ((v3[0]-v2[0])**2 + (v3[1]-v2[1])**2 + (v3[2]-v2[2])**2)**0.5
                                                c = ((v1[0]-v3[0])**2 + (v1[1]-v3[1])**2 + (v1[2]-v3[2])**2)**0.5
                                                s = (a + b + c) / 2
                                                if s > a and s > b and s > c:
                                                    roof_area += (s*(s-a)*(s-b)*(s-c))**0.5
                                            except:
                                                pass
                                except Exception as e:
                                    # B4-FIX: Spezifisches Exception-Handling
                                    print(f"      ⚠️  Fehler bei {elem.Name}: {str(e)[:50]}")
                
                print(f"      {roof.Name:30} {roof_area:8.2f} m²  ({slab_count} Slabs)")
        
        print()
        
        self.results['geometry'] = {
            'slabs_by_type': {k: len(v) for k, v in by_predefined.items()},
            'slabs_by_parent': {k: len(v) for k, v in by_parent.items()}
        }
    
    def step8_validation(self):
        """Schritt 8: Validierung und Qualitätsprüfung"""
        print(f"{'─'*80}")
        print(f"8️⃣  VALIDIERUNG - Qualitätsprüfung")
        print(f"{'─'*80}\n")
        
        issues = []
        warnings = []
        
        # 1. Prüfe U-Werte
        walls = self.ifc_file.by_type('IfcWall')
        zero_u_values = 0
        
        for wall in walls:
            try:
                psets = ifcopenshell.util.element.get_psets(wall)
                u_value = psets.get('Pset_WallCommon', {}).get('ThermalTransmittance', None)
                if u_value == 0.0:
                    zero_u_values += 1
            except:
                pass
        
        if zero_u_values > 0:
            warnings.append(f"{zero_u_values} Wände haben U-Wert = 0.0 (müssen aus EVEBI ergänzt werden)")
        
        # 2. Prüfe SpaceBoundary
        space_boundaries = self.ifc_file.by_type('IfcRelSpaceBoundary')
        if len(space_boundaries) == 0:
            issues.append("Keine IfcRelSpaceBoundary gefunden (wichtig für DIN 18599)")
        
        # 3. Prüfe Geometrie
        elements_without_geom = 0
        for elem_type in ['IfcWall', 'IfcSlab', 'IfcWindow', 'IfcDoor']:
            elements = self.ifc_file.by_type(elem_type)
            for elem in elements:
                if not (hasattr(elem, 'Representation') and elem.Representation):
                    elements_without_geom += 1
        
        if elements_without_geom > 0:
            warnings.append(f"{elements_without_geom} Elemente ohne Geometrie")
        
        # Ausgabe
        if not issues and not warnings:
            print(f"   ✅ Keine kritischen Probleme gefunden!")
        else:
            if issues:
                print(f"   ❌ KRITISCHE PROBLEME:\n")
                for issue in issues:
                    print(f"      • {issue}")
                print()
            
            if warnings:
                print(f"   ⚠️  WARNUNGEN:\n")
                for warning in warnings:
                    print(f"      • {warning}")
                print()
        
        # Zusammenfassung für DIN 18599
        print(f"   💡 DIN 18599 Eignung:\n")
        
        has_geometry = elements_without_geom < 10
        has_spaces = len(self.ifc_file.by_type('IfcSpace')) > 0
        has_materials = len(self.ifc_file.by_type('IfcMaterial')) > 0
        
        print(f"      Geometrie:           {'✅' if has_geometry else '❌'}")
        print(f"      Räume:               {'✅' if has_spaces else '❌'}")
        print(f"      Materialien:         {'✅' if has_materials else '❌'}")
        print(f"      SpaceBoundary:       {'✅' if len(space_boundaries) > 0 else '❌'}")
        print(f"      U-Werte:             {'⚠️  Aus EVEBI' if zero_u_values > 0 else '✅'}")
        
        print()
        
        self.results['validation'] = {
            'issues': issues,
            'warnings': warnings,
            'din18599_ready': has_geometry and has_spaces and has_materials
        }
    
    def export_json(self, output_path: str):
        """Exportiert Ergebnisse als JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"📄 Ergebnisse exportiert: {output_path}\n")


def main():
    parser = argparse.ArgumentParser(description='Umfassende IFC-Analyse')
    parser.add_argument('ifc_file', help='Pfad zur IFC-Datei')
    parser.add_argument('--step', type=int, choices=range(1, 9), help='Nur einen Schritt ausführen')
    parser.add_argument('--detail', action='store_true', help='Detaillierte Ausgabe')
    parser.add_argument('--json', help='JSON-Export Pfad')
    
    args = parser.parse_args()
    
    if not Path(args.ifc_file).exists():
        print(f"❌ Datei nicht gefunden: {args.ifc_file}")
        sys.exit(1)
    
    analyzer = IFCAnalyzer(args.ifc_file)
    
    if args.step:
        # Nur einen Schritt ausführen
        step_methods = {
            1: analyzer.step1_header,
            2: analyzer.step2_spatial_structure,
            3: analyzer.step3_building_elements,
            4: analyzer.step4_properties,
            5: analyzer.step5_materials,
            6: analyzer.step6_relationships,
            7: analyzer.step7_geometry,
            8: analyzer.step8_validation
        }
        step_methods[args.step]()
    else:
        # Alle Schritte
        analyzer.analyze_all(detail=args.detail)
    
    if args.json:
        analyzer.export_json(args.json)


if __name__ == "__main__":
    main()
