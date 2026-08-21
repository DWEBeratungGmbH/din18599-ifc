"""Integration contract for the neutral IFC adapter and real fixture."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FIXTURE = REPO / "sources" / "IFC_EVBI" / "DIN18599TestIFCv4.ifc"
SCHEMA = REPO / "schema" / "v4.0" / "sidecar.schema.json"


def test_real_ifc_fixture_builds_valid_neutral_sidecar() -> None:
    from jsonschema import Draft7Validator

    from .v4 import parse_ifc_to_neutral_sidecar

    sidecar = parse_ifc_to_neutral_sidecar(
        str(FIXTURE),
        project_name="IFC neutral fixture",
        building_type="non_residential",
        ifc_file_ref=FIXTURE.name,
    )
    errors = list(
        Draft7Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(sidecar)
    )

    assert not errors
    assert sidecar["schema_info"]["version"] == "4.0.0"
    assert sidecar["meta"]["source"]["origin"] == "IFC_PARSER"
    assert sidecar["input"]["element_groups"]
    assert sidecar["input"]["rooms"]
    assert sidecar["input"]["constructions"]


if __name__ == "__main__":
    test_real_ifc_fixture_builds_valid_neutral_sidecar()
    print("PASS: real IFC fixture builds valid neutral sidecar")
