"""
Roundtrip Merger - IFC Sidecar + EVEBI Daten zusammenführen

Workflow:
1. IFC → Sidecar Input (Parser v3.6)
2. EVEBI → Extrahierte Daten (EVEBI Parser v2)
3. Merge: Sidecar Input + EVEBI Daten → Vollständiges Sidecar (Input + Output)
"""

import json
from typing import Dict, Any, List
from api.parsers.ifc_parser_v3 import parse_ifc_file
from api.parsers.evebi_parser import parse_evea


def merge_roundtrip(ifc_path: str, evea_path: str) -> Dict[str, Any]:
    """
    Führt IFC-Sidecar und EVEBI-Daten zusammen
    
    Returns:
        Vollständiges Sidecar JSON mit input (IFC) + output (EVEBI)
    """
    print('=' * 60)
    print('ROUNDTRIP MERGER - IFC + EVEBI')
    print('=' * 60)
    print()
    
    # 1. IFC → Sidecar Input
    print('STEP 1: IFC → Sidecar Input')
    print(f'  Datei: {ifc_path}')
    sidecar = parse_ifc_file(ifc_path)
    print(f'  ✅ {len(sidecar["input"]["envelope"]["walls"])} Wände, '
          f'{len(sidecar["input"]["envelope"]["roofs"])} Dächer, '
          f'{len(sidecar["input"]["building"]["rooms"])} Räume')
    print()
    
    # 2. EVEBI → Extrahierte Daten
    print('STEP 2: EVEBI → Extrahierte Daten')
    print(f'  Datei: {evea_path}')
    evebi_data = parse_evea(evea_path)
    print(f'  ✅ {len(evebi_data.constructions)} Konstruktionen, '
          f'{len(evebi_data.elements)} Bauteile, '
          f'{len(evebi_data.zones)} Zonen')
    print()
    
    # 3. Merge: U-Werte aus EVEBI in Sidecar Input
    print('STEP 3: Merge U-Werte (EVEBI → Sidecar Input)')
    u_value_count = _merge_u_values(sidecar, evebi_data)
    print(f'  ✅ {u_value_count} U-Werte ergänzt')
    print()
    
    # 4. Merge: Konstruktionen aus EVEBI in Sidecar Input
    print('STEP 4: Merge Konstruktionen (EVEBI → Sidecar Input)')
    construction_count = _merge_constructions(sidecar, evebi_data)
    print(f'  ✅ {construction_count} Konstruktionen ergänzt')
    print()
    
    # 5. Merge: Systeme aus EVEBI in Sidecar Input
    print('STEP 5: Merge Systeme (EVEBI → Sidecar Input)')
    systems_count = _merge_systems(sidecar, evebi_data)
    print(f'  ✅ {systems_count} Systeme ergänzt')
    print()
    
    # 6. Output: Berechnungsergebnisse (Placeholder - EVEBI hat keine Ergebnisse)
    print('STEP 6: Output-Snapshot (Placeholder)')
    _add_output_snapshot(sidecar, evebi_data)
    print(f'  ⚠️  EVEBI-Datei enthält keine Berechnungsergebnisse')
    print(f'  ℹ️  Output-Snapshot mit Dummy-Werten erstellt')
    print()
    
    print('=' * 60)
    print('ROUNDTRIP MERGE ABGESCHLOSSEN ✅')
    print('=' * 60)
    
    return sidecar


def _merge_u_values(sidecar: Dict[str, Any], evebi_data) -> int:
    """Ergänzt U-Werte aus EVEBI in Sidecar-Bauteile"""
    count = 0
    
    # Erstelle GUID → U-Wert Mapping aus EVEBI
    evebi_u_values = {}
    for elem in evebi_data.elements:
        if elem.u_value is not None and elem.u_value > 0:
            evebi_u_values[elem.guid] = elem.u_value
    
    # Ergänze U-Werte in Sidecar
    for wall in sidecar['input']['envelope']['walls']:
        if wall['u_value'] == 0.0 and wall['id'] in evebi_u_values:
            wall['u_value'] = round(evebi_u_values[wall['id']], 3)
            count += 1
    
    for roof in sidecar['input']['envelope']['roofs']:
        if roof['u_value'] == 0.0 and roof['id'] in evebi_u_values:
            roof['u_value'] = round(evebi_u_values[roof['id']], 3)
            count += 1
    
    for floor in sidecar['input']['envelope']['floors']:
        if floor['u_value'] == 0.0 and floor['id'] in evebi_u_values:
            floor['u_value'] = round(evebi_u_values[floor['id']], 3)
            count += 1
    
    for window in sidecar['input']['envelope']['windows']:
        if window['u_value'] == 0.0 and window['id'] in evebi_u_values:
            window['u_value'] = round(evebi_u_values[window['id']], 3)
            count += 1
    
    return count


def _merge_constructions(sidecar: Dict[str, Any], evebi_data) -> int:
    """Ergänzt Konstruktionen aus EVEBI in Sidecar"""
    constructions = []
    
    for konstr in evebi_data.constructions:
        constructions.append({
            'id': konstr.guid,
            'name': konstr.name,
            'u_value': round(konstr.u_value, 3) if konstr.u_value else None,
            'layers': [
                {
                    'material': layer.material_name,
                    'thickness': layer.thickness,
                    'lambda': layer.lambda_value,
                    'position': layer.position
                }
                for layer in konstr.layers
            ]
        })
    
    # Füge Konstruktionen zum Sidecar hinzu
    if 'constructions' not in sidecar['input']:
        sidecar['input']['constructions'] = []
    
    sidecar['input']['constructions'] = constructions
    
    return len(constructions)


def _merge_systems(sidecar: Dict[str, Any], evebi_data) -> int:
    """Ergänzt technische Systeme aus EVEBI in Sidecar"""
    count = 0
    
    if 'systems' not in sidecar['input']:
        sidecar['input']['systems'] = {}
    
    # Heizung
    if evebi_data.heating_systems:
        sidecar['input']['systems']['heating'] = evebi_data.heating_systems
        count += len(evebi_data.heating_systems)
    
    # Warmwasser
    if evebi_data.dhw_systems:
        sidecar['input']['systems']['dhw'] = evebi_data.dhw_systems
        count += len(evebi_data.dhw_systems)
    
    # Lüftung
    if evebi_data.ventilation_systems:
        sidecar['input']['systems']['ventilation'] = evebi_data.ventilation_systems
        count += len(evebi_data.ventilation_systems)
    
    # PV
    if evebi_data.pv_systems:
        sidecar['input']['systems']['pv'] = evebi_data.pv_systems
        count += len(evebi_data.pv_systems)
    
    return count


def _add_output_snapshot(sidecar: Dict[str, Any], evebi_data) -> None:
    """
    Fügt Output-Snapshot hinzu (Placeholder, da EVEBI keine Ergebnisse enthält)
    
    In einer echten Berechnung würden hier die DIN 18599-Ergebnisse stehen:
    - Nutzenergie (useful_energy)
    - Endenergie (final_energy)
    - Primärenergie (primary_energy)
    - CO2-Emissionen (co2_emissions)
    """
    sidecar['output'] = {
        'snapshots': [
            {
                'id': 'snapshot_001',
                'meta': {
                    'calculation_date': '2026-04-01',
                    'software': 'EVEBI',
                    'version': '1.0',
                    'standard': 'DIN 18599:2018',
                    'valid': True
                },
                'useful_energy': {
                    'per_zone': [],
                    'total': {
                        'heating': None,
                        'cooling': None,
                        'dhw': None,
                        'lighting': None,
                        'ventilation': None
                    }
                },
                'final_energy': {
                    'reference_system': {
                        'heating': None,
                        'dhw': None,
                        'total': None
                    },
                    'by_carrier': [],
                    'by_zone_and_application': [],
                    'total': None
                },
                'primary_energy': {
                    'reference_system': {
                        'non_renewable': None,
                        'renewable': None,
                        'total': None
                    },
                    'by_carrier': [],
                    'by_zone_and_application': [],
                    'total': {
                        'non_renewable': None,
                        'renewable': None,
                        'total': None
                    }
                },
                'co2_emissions': {
                    'by_carrier': [],
                    'by_zone_and_application': [],
                    'total': None
                },
                'specific_values': {
                    'reference_area': None,
                    'useful_energy': None,
                    'final_energy': None,
                    'primary_energy': None,
                    'co2_emissions': None
                },
                'savings': {
                    'final_energy_percent': None,
                    'primary_energy_percent': None,
                    'co2_percent': None,
                    'cost_annual_euro': None
                }
            }
        ]
    }


if __name__ == '__main__':
    # Test
    result = merge_roundtrip(
        'sources/IFC_EVBI/DIN18599TestIFCv2.ifc',
        'sources/IFC_EVBI/DIN18599Test_260401.evea'
    )
    
    with open('output_roundtrip_merged.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print()
    print('✅ Ergebnis: output_roundtrip_merged.json')
