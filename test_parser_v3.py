#!/usr/bin/env python3
"""
End-to-End Test: Parser v3 gegen DIN18599Test v3.ifc
"""
import json
import sys
import os

# Direkter Import ohne Package-Struktur
sys.path.insert(0, os.path.dirname(__file__))

# Import Parser v3 direkt
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import math
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Kopiere Parser v3 Code hier rein
exec(open('api/parsers/ifc_parser_v3.py').read())

if __name__ == '__main__':
    ifc_path = 'sources/IFC_EVBI/DIN18599TestIFCv3.ifc'
    
    print("=" * 60)
    print("PARSER v3 - END-TO-END TEST")
    print("=" * 60)
    print(f"IFC File: {ifc_path}")
    print()
    
    result = parse_ifc_file(ifc_path)
    
    # Schreibe Output
    output_path = 'output_v3_test.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Zusammenfassung
    print("=" * 60)
    print("OUTPUT SUMMARY")
    print("=" * 60)
    print(f"Project: {result['meta']['project_name']}")
    print(f"IFC Schema: {result['meta']['ifc_schema']}")
    print()
    
    print("Building:")
    print(f"  Storeys: {len(result['input']['building']['storeys'])}")
    for s in result['input']['building']['storeys']:
        print(f"    - {s['name']} (elevation: {s.get('elevation')})")
    print()
    
    print(f"  Zones: {len(result['input']['building']['zones'])}")
    zones_with_volume = sum(1 for z in result['input']['building']['zones'] if z.get('volume'))
    print(f"    - Mit Volume: {zones_with_volume}/{len(result['input']['building']['zones'])}")
    for z in result['input']['building']['zones'][:3]:
        print(f"    - {z['name']}: area={z.get('area')}, volume={z.get('volume')}, height={z.get('height')}")
    print()
    
    print("Envelope:")
    walls = result['input']['envelope']['walls']
    roofs = result['input']['envelope']['roofs']
    floors = result['input']['envelope']['floors']
    windows = result['input']['envelope']['windows']
    doors = result['input']['envelope']['doors']
    
    print(f"  Walls: {len(walls)}")
    if walls:
        din_codes = set(w.get('din_code') for w in walls if w.get('din_code'))
        print(f"    - DIN Codes: {sorted(din_codes)}")
        with_fx = sum(1 for w in walls if w.get('fx_factor') is not None)
        print(f"    - Mit fx_factor: {with_fx}/{len(walls)}")
        with_zone = sum(1 for w in walls if w.get('zone_ref'))
        print(f"    - Mit zone_ref: {with_zone}/{len(walls)}")
        
        # Beispiel-Wand
        if walls:
            w = walls[0]
            print(f"    - Beispiel: {w['name']}")
            print(f"      din_code={w.get('din_code')}, bc={w.get('boundary_condition')}, fx={w.get('fx_factor')}")
    print()
    
    print(f"  Roofs: {len(roofs)}")
    if roofs:
        din_codes = set(r.get('din_code') for r in roofs if r.get('din_code'))
        print(f"    - DIN Codes: {sorted(din_codes)}")
    print()
    
    print(f"  Floors: {len(floors)}")
    if floors:
        din_codes = set(f.get('din_code') for f in floors if f.get('din_code'))
        print(f"    - DIN Codes: {sorted(din_codes)}")
        # Prüfe BASESLAB
        baseslabs = [f for f in floors if f.get('predefined_type') == 'BASESLAB']
        print(f"    - BASESLAB: {len(baseslabs)}")
        if baseslabs:
            bs = baseslabs[0]
            print(f"      {bs['name']}: area={bs.get('area')}, din_code={bs.get('din_code')}")
    print()
    
    print(f"  Windows: {len(windows)}")
    if windows:
        din_codes = set(w.get('din_code') for w in windows if w.get('din_code'))
        print(f"    - DIN Codes: {sorted(din_codes)}")
        # Prüfe Neigung
        fa = sum(1 for w in windows if w.get('din_code') == 'FA')
        fd = sum(1 for w in windows if w.get('din_code') == 'FD')
        fl = sum(1 for w in windows if w.get('din_code') == 'FL')
        print(f"    - FA (≥60°): {fa}, FD (22-60°): {fd}, FL (<22°): {fl}")
    print()
    
    print(f"  Doors: {len(doors)}")
    print()
    
    print("Validation:")
    print(f"  Warnings: {len(result.get('warnings', []))}")
    if result.get('warnings'):
        for w in result['warnings'][:5]:
            print(f"    - {w}")
    print(f"  Errors: {len(result.get('errors', []))}")
    print()
    
    print("=" * 60)
    print(f"✅ Output written to: {output_path}")
    print("=" * 60)
