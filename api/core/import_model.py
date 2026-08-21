"""Neutral import records shared by format adapters.

Adapters translate product-specific source data into these records before a
sidecar is built. No source format, vendor, or file extension belongs here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class Provenance:
    """Origin metadata for an imported or derived record."""

    origin: str
    tool: Optional[str] = None
    tool_version: Optional[str] = None
    source_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GeometryElement:
    """A geometric or building element with optional energy attributes."""

    id: str
    name: str
    element_type: str
    source_id: Optional[str] = None
    position_number: Optional[str] = None
    area_m2: Optional[float] = None
    orientation_deg: Optional[float] = None
    inclination_deg: Optional[float] = None
    u_value: Optional[float] = None
    construction_ref: Optional[str] = None
    boundary_condition: Optional[str] = None
    provenance: Optional[Provenance] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StoreyRecord:
    """A building storey or level."""

    id: str
    name: str
    source_id: Optional[str] = None
    elevation_m: Optional[float] = None
    below_ground: Optional[bool] = None
    provenance: Optional[Provenance] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConstructionRecord:
    """A reusable construction or layer assembly."""

    id: str
    name: str
    u_value: Optional[float] = None
    layers: list[dict[str, Any]] = field(default_factory=list)
    total_thickness_m: Optional[float] = None
    provenance: Optional[Provenance] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RoomRecord:
    """A geometrically identified room or space."""

    id: str
    name: str
    source_id: Optional[str] = None
    area_m2: Optional[float] = None
    volume_m3: Optional[float] = None
    height_m: Optional[float] = None
    storey_ref: Optional[str] = None
    provenance: Optional[Provenance] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ZoneRecord:
    """A thermal or organizational zone."""

    id: str
    name: str
    area_m2: Optional[float] = None
    volume_m3: Optional[float] = None
    usage_profile_ref: Optional[str] = None
    room_refs: list[str] = field(default_factory=list)
    provenance: Optional[Provenance] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnergySystemRecord:
    """An energy, hot-water, ventilation, or generation system."""

    id: str
    name: str
    system_type: str
    energy_source: Optional[str] = None
    year_built: Optional[int] = None
    nominal_power_kw: Optional[float] = None
    efficiency: Optional[float] = None
    provenance: Optional[Provenance] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CalculationResult:
    """A result produced by an external calculation process."""

    id: str
    kind: str
    value: float
    unit: Optional[str] = None
    period: Optional[str] = None
    provenance: Optional[Provenance] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportBundle:
    """Normalized import payload consumed by neutral sidecar services."""

    provenance: Optional[Provenance] = None
    elements: list[GeometryElement] = field(default_factory=list)
    storeys: list[StoreyRecord] = field(default_factory=list)
    constructions: list[ConstructionRecord] = field(default_factory=list)
    rooms: list[RoomRecord] = field(default_factory=list)
    zones: list[ZoneRecord] = field(default_factory=list)
    systems: list[EnergySystemRecord] = field(default_factory=list)
    results: list[CalculationResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
