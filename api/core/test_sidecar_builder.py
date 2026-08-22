"""Focused tests for the neutral draft builder."""

from __future__ import annotations

from .import_model import GeometryElement, ImportBundle, Provenance
from .sidecar_bridge import bundle_from_sidecar
from .sidecar_builder import DraftBuildError, build_draft_sidecar


def test_build_draft_sidecar_emits_neutral_v4_shape() -> None:
    bundle = ImportBundle(
        provenance=Provenance(origin="urn:ifc:parser", tool="ifc-parser"),
        elements=[
            GeometryElement(
                id="W1",
                name="External wall",
                element_type="wall",
                source_id="ifc-wall-1",
                metadata={
                    "fingerprint": {
                        "normal_x": 1.0,
                        "normal_y": 0.0,
                        "normal_z": 0.0,
                        "dist_m": 2.5,
                        "coordinate_system": "project",
                    }
                },
            )
        ],
    )

    sidecar = build_draft_sidecar(
        bundle,
        project_name="Neutral test",
        building_type="residential",
        ifc_file_ref="model.ifc",
    )

    assert sidecar["schema_info"]["version"] == "4.0.0"
    assert sidecar["meta"]["source"]["origin"] == "urn:ifc:parser"
    assert sidecar["input"]["building"]["type"] == "residential"
    assert sidecar["input"]["element_groups"][0]["fingerprint"]["dist_m"] == 2.5


def test_builder_rejects_incomplete_element() -> None:
    bundle = ImportBundle(
        elements=[GeometryElement(id="W1", name="Wall", element_type="wall")]
    )

    try:
        build_draft_sidecar(
            bundle,
            project_name="Invalid test",
            building_type="residential",
        )
    except DraftBuildError as error:
        assert "fingerprint" in str(error)
    else:
        raise AssertionError("incomplete element was accepted")


def test_sidecar_bridge_preserves_neutral_records() -> None:
    sidecar = {
        "meta": {
            "project_name": "Bridge test",
            "ifc_file_ref": "model.ifc",
            "source": {"origin": "urn:ifc:parser", "tool": "ifc-parser"},
        },
        "input": {
            "building": {"type": "residential"},
            "element_groups": [
                {
                    "id": "W1",
                    "name": "Wall",
                    "element_type": "wall",
                    "fingerprint": {"normal_x": 1.0, "normal_y": 0.0, "dist_m": 2.0},
                    "member_elements": [{"source_id": "ifc-wall-1", "source_kind": "ifc_guid"}],
                }
            ],
            "rooms": [{"id": "R1", "name": "Room", "heating_status": "heated"}],
        },
    }

    bundle = bundle_from_sidecar(sidecar)

    assert bundle.metadata["project_name"] == "Bridge test"
    assert bundle.elements[0].metadata["fingerprint"]["dist_m"] == 2.0
    assert bundle.elements[0].source_id == "ifc-wall-1"
    assert bundle.rooms[0].metadata["heating_status"] == "heated"
