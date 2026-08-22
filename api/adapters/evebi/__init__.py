"""EVEBI compatibility adapter.

The adapter namespace is intentionally explicit. The wrapped parser remains in
``parsers.evebi_parser`` for now so existing legacy imports keep working while
callers migrate away from the generic parser package.
"""

from parsers.evebi_parser import EVEBIData, evebi_data_to_dict, parse_evea
from .normalizer import normalize_evebi

__all__ = ["EVEBIData", "evebi_data_to_dict", "normalize_evebi", "parse_evea"]
