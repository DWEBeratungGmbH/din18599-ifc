"""Neutral domain models shared by import adapters and sidecar builders."""

from .import_model import (
    CalculationResult,
    ConstructionRecord,
    EnergySystemRecord,
    GeometryElement,
    ImportBundle,
    Provenance,
    RoomRecord,
    StoreyRecord,
    ZoneRecord,
)
from .sidecar_builder import DraftBuildError, build_draft_sidecar
from .sidecar_bridge import bundle_from_sidecar

__all__ = [
    "CalculationResult",
    "ConstructionRecord",
    "DraftBuildError",
    "EnergySystemRecord",
    "GeometryElement",
    "ImportBundle",
    "Provenance",
    "RoomRecord",
    "StoreyRecord",
    "ZoneRecord",
    "build_draft_sidecar",
    "bundle_from_sidecar",
]
