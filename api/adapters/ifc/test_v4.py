"""Contract tests for the IFC adapter bridge."""

from __future__ import annotations

from .v4 import bundle_from_ifc_sidecar
from core.sidecar_builder import build_draft_sidecar


def test_ifc_sidecar_roundtrip_uses_neutral_core() -> None:
    source = {
        "schema_info": {
            "url": "https://din18599-ifc.de/schema/v4.0/sidecar",
            "version": "4.0.0",
        },
        "meta": {
            "project_name": "IFC bridge test",
            "ifc_file_ref": "model.ifc",
            "norm_editions": {"din_18599": "2018-09"},
            "source": {
                "origin": "IFC_PARSER",
                "tool": "IFC v4 parser",
                "tool_version": "0.1.0",
            },
        },
        "input": {
            "building": {
                "type": "residential",
                "ngf_m2": 24.0,
                "storeys_above_ground": 1,
            },
            "storeys": [
                {
                    "id": "S-0001",
                    "ifc_guid": "ifc-storey-1",
                    "name": "Ground floor",
                    "elevation_m": 0.0,
                    "below_ground": False,
                }
            ],
            "element_groups": [
                {
                    "id": "W-0001",
                    "name": "External wall",
                    "element_type": "wall",
                    "fingerprint": {
                        "normal_x": 1.0,
                        "normal_y": 0.0,
                        "normal_z": 0.0,
                        "dist_m": 4.25,
                        "coordinate_system": "project",
                    },
                    "member_elements": [
                        {"source_id": "ifc-wall-1", "source_kind": "ifc_guid"}
                    ],
                }
            ],
            "rooms": [
                {
                    "id": "R-0001",
                    "name": "Living room",
                    "ifc_guid": "ifc-space-1",
                    "heating_status": "heated",
                    "area_ngf_m2": 24.0,
                }
            ],
        },
    }

    bundle = bundle_from_ifc_sidecar(source)
    rebuilt = build_draft_sidecar(
        bundle,
        project_name="IFC bridge test",
        building_type="residential",
        ifc_file_ref="model.ifc",
    )

    assert bundle.provenance is not None
    assert bundle.provenance.origin == "IFC_PARSER"
    assert rebuilt["meta"]["source"]["origin"] == "IFC_PARSER"
    assert rebuilt["input"]["building"]["ngf_m2"] == 24.0
    assert rebuilt["input"]["storeys"][0]["ifc_guid"] == "ifc-storey-1"
    assert rebuilt["input"]["element_groups"][0]["member_elements"][0]["source_id"] == "ifc-wall-1"
    assert rebuilt["input"]["rooms"][0]["heating_status"] == "heated"
