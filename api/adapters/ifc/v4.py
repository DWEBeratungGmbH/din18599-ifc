"""IFC v4 adapter backed by the existing geometry parser."""

from __future__ import annotations

from typing import Any

from core.import_model import ImportBundle
from core.sidecar_bridge import bundle_from_sidecar
from core.sidecar_builder import build_draft_sidecar


def bundle_from_ifc_sidecar(sidecar: dict[str, Any]) -> ImportBundle:
    """Normalize an IFC parser v4 result into the neutral import model."""
    return bundle_from_sidecar(sidecar)


def parse_ifc_to_bundle(
    ifc_path: str,
    *,
    ifc_file_ref: str = "model.ifc",
    base: dict[str, Any] | None = None,
    building_type: str | None = None,
) -> ImportBundle:
    """Parse IFC geometry and return neutral records."""
    from parsers.ifc_v4_parser import parse_ifc_to_sidecar_v4

    sidecar = parse_ifc_to_sidecar_v4(
        ifc_path,
        ifc_file_ref=ifc_file_ref,
        base=base,
        building_type=building_type,
    )
    return bundle_from_ifc_sidecar(sidecar)


def parse_ifc_to_neutral_sidecar(
    ifc_path: str,
    *,
    project_name: str,
    building_type: str,
    ifc_file_ref: str = "model.ifc",
) -> dict[str, Any]:
    """Parse IFC through the adapter and rebuild it with the neutral builder."""
    bundle = parse_ifc_to_bundle(ifc_path, ifc_file_ref=ifc_file_ref)
    return build_draft_sidecar(
        bundle,
        project_name=project_name,
        building_type=building_type,
        ifc_file_ref=ifc_file_ref,
    )
