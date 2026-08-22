"""Normalize EVEBI parser results into the neutral import model."""

from __future__ import annotations

from typing import Any

from core.import_model import (
    ConstructionRecord,
    EnergySystemRecord,
    GeometryElement,
    ImportBundle,
    Provenance,
    RoomRecord,
    ZoneRecord,
)
from parsers.evebi_parser import EVEBIData


_ADAPTER_ORIGIN = "urn:adapter:evebi"


def _provenance(data: EVEBIData, source_ref: str | None) -> Provenance:
    return Provenance(
        origin=_ADAPTER_ORIGIN,
        source_id=source_ref or data.project_guid or None,
        metadata={"project_guid": data.project_guid},
    )


def _element_type(value: str) -> str:
    return value.strip().lower() or "other"


def normalize_evebi(
    data: EVEBIData,
    *,
    source_ref: str | None = None,
) -> ImportBundle:
    """Convert parsed product data into neutral records.

    The adapter preserves source identifiers in provenance and metadata while
    keeping product-specific field names out of the neutral model.
    """
    provenance = _provenance(data, source_ref)

    constructions = [
        ConstructionRecord(
            id=construction.guid,
            name=construction.name,
            u_value=construction.u_value,
            layers=[
                {
                    "position": layer.position,
                    "material_name": layer.material_name,
                    "thickness_m": layer.thickness,
                    "lambda": layer.lambda_value,
                }
                for layer in construction.layers
            ],
            total_thickness_m=construction.total_thickness or None,
            provenance=provenance,
        )
        for construction in data.constructions
    ]

    elements = [
        GeometryElement(
            id=element.guid,
            name=element.name,
            element_type=_element_type(element.element_type),
            source_id=element.guid,
            position_number=element.posno,
            area_m2=element.area,
            orientation_deg=element.orientation,
            inclination_deg=element.inclination,
            u_value=element.u_value,
            construction_ref=element.construction_ref,
            boundary_condition=element.boundary_condition,
            provenance=provenance,
        )
        for element in data.elements
    ]

    rooms = [
        RoomRecord(
            id=zone.guid,
            name=zone.name,
            source_id=zone.guid,
            area_m2=zone.area,
            volume_m3=zone.volume,
            provenance=provenance,
        )
        for zone in data.zones
    ]

    zones = [
        ZoneRecord(
            id=zone.guid,
            name=zone.name,
            area_m2=zone.area,
            volume_m3=zone.volume,
            provenance=provenance,
        )
        for zone in data.zones
    ]

    systems: list[EnergySystemRecord] = []
    for system_type, records in (
        ("heating", data.heating_systems),
        ("hot_water", data.dhw_systems),
        ("ventilation", data.ventilation_systems),
        ("generation", data.pv_systems),
    ):
        systems.extend(_normalize_system(record, system_type, provenance) for record in records)

    return ImportBundle(
        provenance=provenance,
        elements=elements,
        constructions=constructions,
        rooms=rooms,
        zones=zones,
        systems=systems,
        metadata={"project_name": data.project_name},
    )


def _normalize_system(
    record: dict[str, Any],
    system_type: str,
    provenance: Provenance,
) -> EnergySystemRecord:
    """Map a source system dictionary while retaining unknown fields."""
    known = {"guid", "name", "art", "year_built"}
    return EnergySystemRecord(
        id=str(record.get("guid") or record.get("id") or f"{system_type}:unnamed"),
        name=str(record.get("name") or system_type),
        system_type=system_type,
        year_built=record.get("year_built"),
        provenance=provenance,
        metadata={
            "source_type": record.get("art"),
            **{key: value for key, value in record.items() if key not in known},
        },
    )
