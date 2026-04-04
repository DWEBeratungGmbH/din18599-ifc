"""
DIN18599 IFC Parsers
Parst IFC und EVEBI Dateien für Sidecar-Generierung
"""

from .evebi_parser import parse_evea, EVEBIData

# ifc_parser wurde durch ifc_parser_v3 ersetzt
# Import wird hier nicht gemacht — wird direkt in roundtrip_processor.py importiert

__all__ = [
    'parse_evea',
    'EVEBIData',
]
