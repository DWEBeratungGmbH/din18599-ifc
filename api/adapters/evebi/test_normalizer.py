"""Contract tests for the EVEBI adapter normalization boundary."""

from __future__ import annotations

from parsers.evebi_parser import (
    EVEBIConstruction,
    EVEBIData,
    EVEBIElement,
    EVEBILayer,
    EVEBIZone,
)
from .normalizer import normalize_evebi


def test_normalize_evebi_keeps_neutral_records() -> None:
    data = EVEBIData(
        project_guid="project-1",
        project_name="Test project",
        constructions=[
            EVEBIConstruction(
                guid="construction-1",
                name="Wall assembly",
                u_value=0.24,
                layers=[
                    EVEBILayer(
                        material_name="Insulation",
                        thickness=0.12,
                        lambda_value=0.035,
                        position=1,
                    )
                ],
                total_thickness=0.12,
            )
        ],
        elements=[
            EVEBIElement(
                guid="element-1",
                name="External wall",
                element_type="Wall",
                area=42.0,
                orientation=180.0,
                inclination=90.0,
                u_value=0.24,
                construction_ref="construction-1",
                posno="001",
            )
        ],
        zones=[EVEBIZone(guid="zone-1", name="Ground floor", area=80.0, volume=200.0)],
        heating_systems=[{"guid": "system-1", "name": "Heat pump", "art": "heat_pump"}],
    )

    bundle = normalize_evebi(data, source_ref="sample.evea")

    assert bundle.metadata["project_name"] == "Test project"
    assert bundle.provenance is not None
    assert bundle.provenance.origin == "urn:adapter:evebi"
    assert bundle.provenance.source_id == "sample.evea"
    assert bundle.elements[0].element_type == "wall"
    assert bundle.elements[0].position_number == "001"
    assert bundle.constructions[0].layers[0]["thickness_m"] == 0.12
    assert bundle.rooms[0].area_m2 == 80.0
    assert bundle.zones[0].id == "zone-1"
    assert bundle.systems[0].system_type == "heating"
