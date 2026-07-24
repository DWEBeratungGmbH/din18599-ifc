# Golden-Snapshot: IFC-Skelett-Parser (Level `draft`)

Referenz-Ausgabe des IFC -> v4.0-Skelett-Parsers (`api/parsers/ifc_v4_parser.py`),
erzeugt aus der In-Repo-IFC `sources/IFC_EVBI/DIN18599TestIFCv4.ifc`.

Reproduzieren:

```
python3 api/parsers/ifc_v4_parser.py sources/IFC_EVBI/DIN18599TestIFCv4.ifc \
    DIN18599TestIFCv4.ifc > examples/v4.0/din18599test-v4-draft/energy.din18599.json
```

Der Snapshot ist eine menschenlesbare Referenz. Die Test-Wahrheit steht in
`api/parsers/test_ifc_v4_parser.py` (Struktur, Vertragspunkte SPEC §9.1,
Schema-Gueltigkeit, Fingerprint-Idempotenz). Die `*_at`-Zeitstempel in `meta`
sind laufabhaengig — ein reiner Byte-Diff gegen diese Datei ist deshalb kein
Testkriterium.
