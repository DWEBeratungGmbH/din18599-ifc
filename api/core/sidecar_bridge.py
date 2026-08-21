"""Bridge between neutral import records and v4 sidecar dictionaries."""

from __future__ import annotations

from typing import Any

from .import_model import (
    ConstructionRecord,
    GeometryElement,
    ImportBundle,
    Provenance,
    RoomRecord,
    StoreyRecord,
    ZoneRecord,
)


def bundle_from_sidecar(sidecar: dict[str, Any]) -> ImportBundle:
    """Read the neutral, non-derived parts of a v4 sidecar into records."""
    meta = sidecar.get("meta", {})
    source = meta.get("source", {})
    provenance = Provenance(
        origin=source.get("origin", "urn:source:unknown"),
        tool=source.get("tool"),
        tool_version=source.get("tool_version"),
        source_id=meta.get("ifc_file_ref"),
    )
    input_data = sidecar.get("input", {})

    storeys = [
        StoreyRecord(
            id=record["id"],
            name=record.get("name", record["id"]),
            source_id=record.get("ifc_guid"),
            elevation_m=record.get("elevation_m"),
            below_ground=record.get("below_ground"),
            provenance=provenance,
        )
        for record in input_data.get("storeys", [])
    ]

    constructions = [
        ConstructionRecord(
            id=record["id"],
            name=record.get("name", record["id"]),
            u_value=record.get("u_value"),
            layers=[
                layer
                for sequence in record.get("sequences", [])
                for layer in sequence.get("layers", [])
            ],
            total_thickness_m=record.get("total_thickness_m"),
            provenance=provenance,
        )
        for record in input_data.get("constructions", [])
    ]

    elements = []
    for group in input_data.get("element_groups", []):
        members = group.get("member_elements", [])
        source_id = members[0].get("source_id") if members else None
        metadata = {
            "fingerprint": group["fingerprint"],
            "source_kind": members[0].get("source_kind", "ifc_guid") if members else "ifc_guid",
        }
        elements.append(
            GeometryElement(
                id=group["id"],
                name=group.get("name", group["id"]),
                element_type=group["element_type"],
                source_id=source_id,
                u_value=group.get("u_value"),
                construction_ref=group.get("construction_ref"),
                provenance=provenance,
                metadata=metadata,
            )
        )

    rooms = [
        RoomRecord(
            id=record["id"],
            name=record.get("name", record["id"]),
            source_id=record.get("ifc_guid"),
            area_m2=record.get("area_ngf_m2"),
            volume_m3=record.get("volume_ve_m3"),
            height_m=record.get("height_m"),
            storey_ref=record.get("storey_ref"),
            provenance=provenance,
            metadata={"heating_status": record.get("heating_status")},
        )
        for record in input_data.get("rooms", [])
    ]

    zones = [
        ZoneRecord(
            id=record["id"],
            name=record.get("name", record["id"]),
            usage_profile_ref=record.get("usage_profile_ref"),
            provenance=provenance,
        )
        for record in input_data.get("zones", [])
    ]

    return ImportBundle(
        provenance=provenance,
        elements=elements,
        storeys=storeys,
        constructions=constructions,
        rooms=rooms,
        zones=zones,
        metadata={
            "project_name": meta.get("project_name", ""),
            "building": dict(input_data.get("building", {})),
        },
    )
