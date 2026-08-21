"""Neutral contract tests for external-import metadata."""

from .orchestrator import ParseResult


def test_legacy_channel_has_neutral_adapter_metadata() -> None:
    result = ParseResult(
        kanal="evebi_beg_geg_xml",
        ki_extrahiert={},
        ki_confidence=1.0,
    )

    assert result.adapter == "adapter:evebi"
    assert result.source_format == "beg_geg_xml"
    assert result.kanal == "evebi_beg_geg_xml"


def test_ifc_channel_has_neutral_adapter_metadata() -> None:
    result = ParseResult(
        kanal="ifc",
        ki_extrahiert={},
        ki_confidence=0.0,
    )

    assert result.adapter == "adapter:ifc"
    assert result.source_format == "ifc"
