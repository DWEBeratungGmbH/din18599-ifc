"""Build a v4.0 draft sidecar from neutral import records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .import_model import ImportBundle, Provenance

SCHEMA_URL = "https://din18599-ifc.de/schema/v4.0/sidecar"
SCHEMA_VERSION = "4.0.0"


class DraftBuildError(ValueError):
    """Raised when neutral records cannot form a schema-valid draft."""


def build_draft_sidecar(
    bundle: ImportBundle,
    *,
    project_name: str,
    building_type: str,
    ifc_file_ref: str | None = None,
) -> dict[str, Any]:
    """Build a strict v4.0 draft from normalized records.

    The builder intentionally refuses incomplete element or room records. A
    caller must enrich those records before asking the neutral core to emit a
    schema-valid sidecar.
    """
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    provenance = bundle.provenance or Provenance(origin="urn:source:unknown")

    sidecar: dict[str, Any] = {
        "schema_info": {"url": SCHEMA_URL, "version": SCHEMA_VERSION},
        "meta": {
            "project_name": project_name,
            "norm_editions": {"din_18599": "2018-09"},
            "created_at": now,
            "updated_at": now,
            "validation": {
                "level": "draft",
                "validated_at": now,
                "ruleset_version": "0.1.0",
            },
            "source": {
                "origin": provenance.origin,
                "tool": provenance.tool or "neutral-import-core",
                "tool_version": provenance.tool_version or "0.1.0",
            },
        },
        "input": {
            "building": {
                **bundle.metadata.get("building", {}),
                "type": building_type,
            }
        },
    }

    if ifc_file_ref:
        sidecar["meta"]["ifc_file_ref"] = ifc_file_ref

    if bundle.constructions:
        sidecar["input"]["constructions"] = [
            _construction_to_dict(construction)
            for construction in bundle.constructions
        ]

    if bundle.storeys:
        sidecar["input"]["storeys"] = [
            _storey_to_dict(storey) for storey in bundle.storeys
        ]

    if bundle.elements:
        sidecar["input"]["element_groups"] = [
            _element_to_group(element) for element in bundle.elements
        ]

    if bundle.rooms:
        sidecar["input"]["rooms"] = [_room_to_dict(room) for room in bundle.rooms]

    if bundle.zones:
        sidecar["input"]["zones"] = [
            {
                "id": zone.id,
                "name": zone.name,
                "zone_type": "thermal",
            }
            for zone in bundle.zones
        ]

    return sidecar


def _source_kind(provenance: Provenance | None) -> str:
    origin = provenance.origin if provenance else ""
    if origin.startswith("urn:adapter:"):
        return "IMPORT_ADAPTER"
    if origin.startswith("urn:ifc:") or origin == "IFC_PARSER":
        return "IFC"
    if origin.startswith("urn:catalog:"):
        return "CATALOG"
    if origin.startswith("urn:manual:"):
        return "MANUAL"
    return "DERIVED"


def _construction_to_dict(construction: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": construction.id,
        "name": construction.name,
        "source": _source_kind(construction.provenance),
    }
    if construction.provenance and construction.provenance.source_id:
        result["origin_ref"] = construction.provenance.source_id
    if construction.u_value is not None:
        result["u_value"] = construction.u_value
    if construction.total_thickness_m is not None:
        result["total_thickness_m"] = construction.total_thickness_m
    if construction.layers:
        result["sequences"] = [{"layers": construction.layers}]
    return result


def _storey_to_dict(storey: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"id": storey.id, "name": storey.name}
    if storey.source_id:
        result["ifc_guid"] = storey.source_id
    if storey.elevation_m is not None:
        result["elevation_m"] = storey.elevation_m
    if storey.below_ground is not None:
        result["below_ground"] = storey.below_ground
    return result


def _element_to_group(element: Any) -> dict[str, Any]:
    fingerprint = element.metadata.get("fingerprint")
    if not isinstance(fingerprint, dict):
        raise DraftBuildError(
            f"Element {element.id!r} lacks a project-plane fingerprint"
        )
    required = {"normal_x", "normal_y", "dist_m"}
    missing = required - fingerprint.keys()
    if missing:
        raise DraftBuildError(
            f"Element {element.id!r} fingerprint lacks: {', '.join(sorted(missing))}"
        )

    result: dict[str, Any] = {
        "id": element.id,
        "name": element.name,
        "element_type": element.element_type,
        "fingerprint": fingerprint,
    }
    if element.construction_ref:
        result["construction_ref"] = element.construction_ref
    if element.u_value is not None:
        result["u_value"] = element.u_value
    if element.source_id:
        result["member_elements"] = [{
            "source_id": element.source_id,
            "source_kind": element.metadata.get("source_kind", "ifc_guid"),
        }]
    return result


def _room_to_dict(room: Any) -> dict[str, Any]:
    heating_status = room.metadata.get("heating_status")
    if heating_status not in {"heated", "unheated", "low_heated"}:
        raise DraftBuildError(
            f"Room {room.id!r} lacks a confirmed heating_status"
        )
    result: dict[str, Any] = {
        "id": room.id,
        "name": room.name,
        "heating_status": heating_status,
    }
    if room.source_id:
        result["ifc_guid"] = room.source_id
    if room.area_m2 is not None:
        result["area_ngf_m2"] = room.area_m2
    if room.height_m is not None:
        result["height_m"] = room.height_m
    if room.volume_m3 is not None:
        result["volume_ve_m3"] = room.volume_m3
    if room.storey_ref:
        result["storey_ref"] = room.storey_ref
    return result
