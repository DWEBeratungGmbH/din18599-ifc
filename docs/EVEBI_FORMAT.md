# EVEBI Format-Dokumentation

**Version:** 1.0  
**Datum:** 1. April 2026  
**Quelle:** Reverse Engineering von EVEBI 14.1.9  
**Datei:** `.evea` (ZIP-Archiv mit `projekt.xml`)

---

## 📋 Übersicht

EVEBI (Energieberater-Software) speichert Projekte im `.evea` Format:
- **Container:** ZIP-Archiv
- **Hauptdatei:** `projekt.xml` (XML-Struktur)
- **Schema-Version:** 2025-12-11 (XSDVersion)

---

## 🏗️ XML-Struktur (Hierarchie)

```
Projekt (Root)
├── @GUID                    # Projekt-GUID
├── @XSDVersion              # Schema-Version
├── createProgVer            # EVEBI Version (z.B. "14.1.9")
├── programmVersion          # EVEBI Version
├── eing (Eingabe)           # ⭐ HAUPTKNOTEN FÜR ALLE DATEN
│   ├── ETraegerListe        # Energieträger (Strom, Gas, etc.)
│   ├── zDListe              # Zonen-Definitionen
│   ├── weListe              # Wohneinheiten/Gebäude
│   ├── geschosseListe       # Geschosse/Zonen
│   ├── rmListe              # Räume
│   ├── tflListe             # ⭐ BAUTEILE (Teilflächen) - 74 Items
│   ├── btlListe             # Bauteil-Typen (Verbauung, etc.)
│   ├── konstruktionenListe  # ⭐ KONSTRUKTIONEN - 6 Items
│   ├── konstrFensterListe   # Fenster-Konstruktionen
│   ├── hzListe              # Heizung
│   ├── hzErzListe           # Heizungs-Erzeuger
│   ├── twListe              # Trinkwasser/Warmwasser
│   ├── twErzListe           # Warmwasser-Erzeuger
│   ├── luftListe            # Lüftung
│   ├── rltListe             # RLT-Anlagen
│   ├── kStrListe            # Kälte-Systeme
│   ├── pvListe              # Photovoltaik
│   ├── batterienListe       # Batteriespeicher
│   └── ...
├── bilderStreamsListe       # Bilder/Fotos
├── massnahmenListe          # Sanierungsmaßnahmen
├── settings                 # Projekt-Einstellungen
└── hdr (Header)             # Projekt-Metadaten
```

---

## 📊 Status: Dokumentierte Kategorien

| Kategorie | Status | Items | Priorität |
|-----------|--------|-------|-----------|
| **Projekt-Metadaten** | ✅ Dokumentiert | - | Hoch |
| **Bauteile (tflListe)** | ✅ Dokumentiert | 74 | Hoch |
| **Konstruktionen** | ✅ Dokumentiert | 6 | Hoch |
| **Zonen/Geschosse** | ✅ Dokumentiert | 4 | Hoch |
| **Energieträger** | ✅ Dokumentiert | 2 | Mittel |
| **Heizung** | ✅ Dokumentiert | 1 | Mittel |
| **Warmwasser** | ✅ Dokumentiert | 1 | Mittel |
| **Lüftung** | ✅ Dokumentiert | 1 | Mittel |
| **PV-Anlagen** | ⏳ Ausstehend | 1 | Niedrig |
| **Batteriespeicher** | ⏳ Ausstehend | 1 | Niedrig |
| **Maßnahmen** | ⏳ Ausstehend | ? | Niedrig |

---

## 🔍 Kategorie 1: Projekt-Metadaten

### XML-Pfad
```
/Projekt
```

### Attribute
| Attribut | Typ | Beispiel | Beschreibung |
|----------|-----|----------|--------------|
| `GUID` | String | `{D61C47A5-E6B0-46AD-94B0-E2877B201ED4}` | Eindeutige Projekt-ID |
| `XSDVersion` | String | `2025-12-11` | Schema-Version |

### Kinder-Elemente
| Element | Typ | Beispiel | Beschreibung |
|---------|-----|----------|--------------|
| `createProgVer` | String | `14.1.9` | EVEBI-Version bei Erstellung |
| `programmVersion` | String | `14.1.9` | Aktuelle EVEBI-Version |

### Projektname
**Pfad:** `/Projekt/eing/weListe/item[1]/name`

**Beispiel:**
```xml
<weListe GUID="{...}">
  <item GUID="{...}">
    <name auto="false" man="Gebäude" calc="">Gebäude</name>
  </item>
</weListe>
```

**Parser-Code:**
```python
project_name = 'Unbekanntes Projekt'
eing = root.find('eing')
if eing is not None:
    we_liste = eing.find('weListe')
    if we_liste is not None:
        first_we = we_liste.find('item')
        if first_we is not None:
            name_elem = first_we.find('.//name')
            if name_elem is not None and name_elem.text:
                project_name = name_elem.text
```

---

## 🧱 Kategorie 2: Bauteile (tflListe)

### Übersicht
- **XML-Pfad:** `/Projekt/eing/tflListe`
- **Anzahl Items:** 74 (im Beispiel-Projekt)
- **Beschreibung:** Teilflächen = Bauteile (Wände, Dächer, Böden, Fenster, Türen)

### Item-Struktur

#### Attribute
| Attribut | Typ | Beispiel | Beschreibung |
|----------|-----|----------|--------------|
| `GUID` | String | `{EF26E269-5A36-4475-BB56-62AC05EF916E}` | Eindeutige Bauteil-ID |

#### Wichtige Kinder-Elemente

##### 1. Name
**Pfad:** `item/name`

**Attribute:**
- `auto`: Boolean (automatisch generiert?)
- `man`: String (manueller Wert)
- `calc`: String (berechneter Wert)

**Beispiel:**
```xml
<name auto="false" man="Zwischenwand Pos 005" calc="">Zwischenwand Pos 005</name>
```

**⭐ PosNo-Extraktion:**
- PosNo ist **im Namen kodiert**: "Zwischenwand Pos 005" → PosNo = "005"
- Regex: `Pos\s+(\d+)`

##### 2. Fläche (nettoA)
**Pfad:** `item/nettoA`

**Beispiel:**
```xml
<nettoA>15.49</nettoA>
```

**Einheit:** m²

##### 3. U-Wert
**Pfad:** `item/U`

**Attribute:**
- `auto`: Boolean
- `man`: String (manueller U-Wert)
- `calc`: String (berechneter U-Wert)
- `unit`: String (immer "W/(m²K)")

**Beispiel:**
```xml
<U auto="true" man="0.0000000" calc="1.2000000" unit="W/(m²K)">1.2000000</U>
```

**⭐ Wert-Extraktion:**
```python
u_value = u_elem.get('man', u_elem.get('calc', '0'))
```

##### 4. Orientierung
**Pfad:** `item/orientierung`

**Beispiel:**
```xml
<orientierung>270</orientierung>
```

**Einheit:** Grad (0-360°)
- 0° = Nord
- 90° = Ost
- 180° = Süd
- 270° = West

##### 5. Neigung
**Pfad:** `item/neigGrad`

**Beispiel:**
```xml
<neigGrad>90</neigGrad>
```

**Einheit:** Grad (0-90°)
- 0° = Horizontal (Boden/Decke)
- 90° = Vertikal (Wand)
- 45° = Dach

##### 6. Bauteil-Typ
**Ableitung aus Name:**
- Enthält "Wand" → `Wall`
- Enthält "Dach" → `Roof`
- Enthält "Boden" oder "Decke" → `Floor`
- Enthält "Fenster" → `Window`
- Enthält "Tür" → `Door`

### Vollständiges Beispiel

```xml
<item GUID="{653340EF-3D87-4FCB-A4BC-A75CE884CD39}">
  <name auto="false" man="Außenwand Nord Pos 001" calc="">Außenwand Nord Pos 001</name>
  <nettoA>15.49</nettoA>
  <U auto="true" man="0.0000000" calc="1.2000000" unit="W/(m²K)">1.2000000</U>
  <orientierung>0</orientierung>
  <neigGrad>90</neigGrad>
  <!-- ... viele weitere Felder ... -->
</item>
```

### Parser-Code

```python
def _extract_elements(eing: ET.Element) -> List[EVEBIElement]:
    elements = []
    tfl_liste = eing.find('tflListe')
    
    for item in tfl_liste:
        guid = item.get('GUID', '')
        name = item.findtext('.//name', 'Unbekanntes Bauteil')
        
        # Element-Typ aus Name
        element_type = 'Unknown'
        if 'Wand' in name:
            element_type = 'Wall'
        elif 'Dach' in name:
            element_type = 'Roof'
        elif 'Boden' in name or 'Decke' in name:
            element_type = 'Floor'
        elif 'Fenster' in name:
            element_type = 'Window'
        elif 'Tür' in name or 'Tuer' in name:
            element_type = 'Door'
        
        # PosNo aus Name
        posno = None
        if 'Pos' in name:
            parts = name.split('Pos')
            if len(parts) > 1:
                posno = parts[1].strip().split()[0]
        
        # Fläche
        area = None
        netto_a = item.findtext('.//nettoA', None)
        if netto_a:
            area = float(netto_a)
        
        # U-Wert
        u_value = None
        u_elem = item.find('.//U')
        if u_elem is not None:
            u_value = float(u_elem.get('man', u_elem.get('calc', '0')))
        
        # Orientierung
        orientation = None
        orient_text = item.findtext('.//orientierung', None)
        if orient_text:
            orientation = float(orient_text)
        
        # Neigung
        inclination = None
        neig_text = item.findtext('.//neigGrad', None)
        if neig_text:
            inclination = float(neig_text)
        
        elements.append(EVEBIElement(
            guid=guid,
            name=name,
            element_type=element_type,
            area=area,
            orientation=orientation,
            inclination=inclination,
            u_value=u_value,
            posno=posno
        ))
    
    return elements
```

---

## 🏗️ Kategorie 3: Konstruktionen (konstruktionenListe)

### Übersicht
- **XML-Pfad:** `/Projekt/eing/konstruktionenListe`
- **Anzahl Items:** 6 (im Beispiel-Projekt)
- **Beschreibung:** Bauteil-Konstruktionen (Schichtaufbauten, Materialien)

### Item-Struktur

#### Attribute
| Attribut | Typ | Beispiel | Beschreibung |
|----------|-----|----------|--------------|
| `GUID` | String | `{...}` | Eindeutige Konstruktions-ID |

#### Wichtige Kinder-Elemente

##### 1. Name
**Pfad:** `item/name`

**Beispiel:**
```xml
<name auto="false" man="Fliesen" calc="">Fliesen</name>
```

##### 2. U-Wert
**Pfad:** `item/U`

**Beispiel:**
```xml
<U auto="true" man="0.0000000" calc="0.8500000" unit="W/(m²K)">0.8500000</U>
```

##### 3. Lambda-Wert (Wärmeleitfähigkeit)
**Pfad:** `item/lambda`

**Beispiel:**
```xml
<lambda auto="false" man="0.8700000" calc="0.0000000" unit="W/(mK)">0.8700000</lambda>
```

**Einheit:** W/(mK)

##### 4. Dichte (rho)
**Pfad:** `item/rho`

**Beispiel:**
```xml
<rho auto="false" man="2000.0000000" calc="0.0000000" unit="kg/m³">2000.0000000</rho>
```

**Einheit:** kg/m³

### Parser-Code

```python
def _extract_constructions(eing: ET.Element) -> List[EVEBIConstruction]:
    constructions = []
    konstr_liste = eing.find('konstruktionenListe')
    
    for item in konstr_liste:
        guid = item.get('GUID', '')
        name = item.findtext('.//name', 'Unbekannte Konstruktion')
        
        # U-Wert
        u_elem = item.find('.//U')
        u_value = 0.0
        if u_elem is not None:
            u_value = float(u_elem.get('man', u_elem.get('calc', '0')))
        
        # Lambda-Wert
        lambda_elem = item.find('.//lambda')
        lambda_value = 0.0
        if lambda_elem is not None:
            lambda_value = float(lambda_elem.get('man', lambda_elem.get('calc', '0')))
        
        # Dichte
        density_elem = item.find('.//rho')
        density = 0.0
        if density_elem is not None:
            density = float(density_elem.get('man', density_elem.get('calc', '0')))
        
        constructions.append(EVEBIConstruction(
            guid=guid,
            name=name,
            u_value=u_value,
            lambda_value=lambda_value,
            density=density
        ))
    
    return constructions
```

---

## 🏠 Kategorie 4: Zonen/Geschosse (geschosseListe)

### Übersicht
- **XML-Pfad:** `/Projekt/eing/geschosseListe`
- **Anzahl Items:** 4 (im Beispiel-Projekt)
- **Beschreibung:** Thermische Zonen / Geschosse

### Item-Struktur

#### Attribute
| Attribut | Typ | Beispiel | Beschreibung |
|----------|-----|----------|--------------|
| `GUID` | String | `{...}` | Eindeutige Geschoss-ID |

#### Wichtige Kinder-Elemente

##### 1. Name
**Pfad:** `item/name`

**Beispiel:**
```xml
<name auto="false" man="Erdgeschoss" calc="">Erdgeschoss</name>
```

##### 2. Fläche
**Pfad:** `item/A`

**Beispiel:**
```xml
<A auto="true" man="80.0000040" calc="0.0000000" unit="m²">80.0000040</A>
```

**Einheit:** m²

##### 3. Volumen
**Pfad:** `item/V` (falls vorhanden)

**Beispiel:**
```xml
<V auto="true" man="200.0000000" calc="0.0000000" unit="m³">200.0000000</V>
```

**Einheit:** m³

### Parser-Code

```python
def _extract_zones(eing: ET.Element) -> List[EVEBIZone]:
    zones = []
    geschosse_liste = eing.find('geschosseListe')
    
    for item in geschosse_liste:
        guid = item.get('GUID', '')
        name = item.findtext('.//name', 'Unbekanntes Geschoss')
        
        # Fläche
        area = 0.0
        a_elem = item.find('.//A[@unit="m²"]')
        if a_elem is not None:
            area = float(a_elem.get('man', a_elem.get('calc', '0')))
        
        # Volumen
        volume = 0.0
        v_elem = item.find('.//V[@unit="m³"]')
        if v_elem is not None:
            volume = float(v_elem.get('man', v_elem.get('calc', '0')))
        
        zones.append(EVEBIZone(
            guid=guid,
            name=name,
            area=area,
            volume=volume
        ))
    
    return zones
```

---

## � Kategorie 5: Energieträger (ETraegerListe)

### Übersicht
- **XML-Pfad:** `/Projekt/eing/ETraegerListe`
- **Anzahl Items:** 2 (im Beispiel-Projekt)
- **Beschreibung:** Energieträger (Strom, Gas, Fernwärme, etc.)

### Item-Struktur

#### Wichtige Kinder-Elemente

##### 1. Name
**Pfad:** `item/name`

**Beispiel:**
```xml
<name auto="false" man="WP-Strom" calc="">WP-Strom</name>
```

##### 2. Einheit
**Pfad:** `item/Einheit`

**Beispiele:**
- `kWh` (Strom)
- `kWh(Hs)` (Gas, Heizwert)
- `kWh(Hi)` (Gas, Brennwert)

##### 3. Primärenergiefaktor
**Pfad:** `item/fP_n_erneuerbar`

**Attribute:**
- `auto`: Boolean
- `man`: String (manueller Wert)
- `calc`: String (berechneter Wert)
- `unit`: String (immer "-")

**Beispiel:**
```xml
<fP_n_erneuerbar auto="true" man="1.8000000" calc="1.8000000" unit="-">1.8000000</fP_n_erneuerbar>
```

**Typische Werte:**
- Strom (Netzstrom): 1.8
- Strom (WP): 1.8
- Erdgas: 1.1
- Fernwärme: 0.7

##### 4. CO2-Emissionen
**Pfad:** `item/CO2`

**Attribute:**
- `unit`: String (immer "g/kWh")

**Beispiel:**
```xml
<CO2 auto="true" man="0.0000000" calc="560.0000000" unit="g/kWh">560.0000000</CO2>
```

##### 5. Preis
**Pfad:** `item/PreisPE`

**Attribute:**
- `unit`: String (immer "€/Einheit")

**Beispiel:**
```xml
<PreisPE unit="€/Einheit">0.2800000</PreisPE>
```

##### 6. Umrechnungsfaktor
**Pfad:** `item/Umr`

**Beispiel:**
```xml
<Umr unit="-">1.0000000</Umr>
```

**Beschreibung:** Umrechnung zwischen verschiedenen Einheiten (z.B. Hs → Hi)

### Parser-Code

```python
@dataclass
class EVEBIEnergyCarrier:
    guid: str
    name: str
    unit: str
    primary_energy_factor: float
    co2_emissions: float  # g/kWh
    price: float  # €/Einheit
    conversion_factor: float

def _extract_energy_carriers(eing: ET.Element) -> List[EVEBIEnergyCarrier]:
    carriers = []
    etraeger_liste = eing.find('ETraegerListe')
    
    for item in etraeger_liste:
        guid = item.get('GUID', '')
        name = item.findtext('.//name', 'Unbekannter Energieträger')
        unit = item.findtext('.//Einheit', 'kWh')
        
        # Primärenergiefaktor
        fp_elem = item.find('.//fP_n_erneuerbar')
        fp = 0.0
        if fp_elem is not None:
            fp = float(fp_elem.get('man', fp_elem.get('calc', '0')))
        
        # CO2
        co2_elem = item.find('.//CO2')
        co2 = 0.0
        if co2_elem is not None:
            co2 = float(co2_elem.get('man', co2_elem.get('calc', '0')))
        
        # Preis
        preis_elem = item.find('.//PreisPE')
        preis = 0.0
        if preis_elem is not None:
            preis = float(preis_elem.text or '0')
        
        # Umrechnungsfaktor
        umr_elem = item.find('.//Umr')
        umr = 1.0
        if umr_elem is not None:
            umr = float(umr_elem.text or '1')
        
        carriers.append(EVEBIEnergyCarrier(
            guid=guid,
            name=name,
            unit=unit,
            primary_energy_factor=fp,
            co2_emissions=co2,
            price=preis,
            conversion_factor=umr
        ))
    
    return carriers
```

---

## 🔥 Kategorie 6: Heizung

### Übersicht
- **Heizungs-Erzeuger:** `/Projekt/eing/hzErzListe`
- **Heizungs-Übergabe:** `/Projekt/eing/hzListe`

### 6.1 Heizungs-Erzeuger (hzErzListe)

#### Wichtige Kinder-Elemente

##### 1. Name
**Beispiel:** "Gas-Niedertemperaturkessel"

##### 2. Art
**Pfad:** `item/art`

**Mögliche Werte:**
- `HZ_ZENTRALHEIZUNG` - Zentralheizung
- `HZ_ETAGENHEIZUNG` - Etagenheizung
- `HZ_EINZELOFEN` - Einzelofen

##### 3. Nennleistung
**Pfad:** `item/leistung`

**Attribute:**
- `unit`: String (immer "kW")

**Beispiel:**
```xml
<leistung auto="true" man="15.0000000" calc="0.0000000" unit="kW">15.0000000</leistung>
```

##### 4. Wirkungsgrad
**Pfad:** `item/wirkungsgrad`

**Beispiel:**
```xml
<wirkungsgrad auto="true" man="0.8500000" calc="0.0000000" unit="-">0.8500000</wirkungsgrad>
```

##### 5. Baujahr
**Pfad:** `item/baujahr`

**Beispiel:**
```xml
<baujahr>2026</baujahr>
```

### 6.2 Heizungs-Übergabe (hzListe)

#### Wichtige Kinder-Elemente

##### 1. Name
**Beispiel:** "Heizkörper"

##### 2. Typ
**Pfad:** `item/typ`

**Mögliche Werte:**
- `HK` - Heizkörper
- `FBH` - Fußbodenheizung
- `LUFT` - Luftheizung

---

## 💧 Kategorie 7: Warmwasser

### Übersicht
- **Warmwasser-Erzeuger:** `/Projekt/eing/twErzListe`
- **Warmwasser-System:** `/Projekt/eing/twListe`

### 7.1 Warmwasser-Erzeuger (twErzListe)

#### Wichtige Kinder-Elemente

##### 1. Name
**Beispiel:** "Gas-Niedertemperaturkessel (Kombibereiter)"

##### 2. Art
**Pfad:** `item/art`

**Mögliche Werte:**
- `WT_HZG` - Kombibereiter (Heizung + Warmwasser)
- `WT_ZENTRAL` - Zentrale Warmwasserbereitung
- `WT_DEZENTRAL` - Dezentrale Warmwasserbereitung

##### 3. Speichervolumen
**Pfad:** `item/volumen`

**Attribute:**
- `unit`: String (immer "L")

**Beispiel:**
```xml
<volumen auto="true" man="300.0000000" calc="0.0000000" unit="L">300.0000000</volumen>
```

##### 4. Baujahr
**Pfad:** `item/baujahr`

### 7.2 Warmwasser-System (twListe)

#### Wichtige Kinder-Elemente

##### 1. Name
**Beispiel:** "zentrale Warmwasserversorgung"

##### 2. Zirkulation
**Pfad:** `item/zirBetrieb`

**Werte:**
- `0` - Keine Zirkulation
- `1` - Mit Zirkulation

**Beispiel:**
```xml
<zirBetrieb>0.0000000</zirBetrieb>
```

---

## 💨 Kategorie 8: Lüftung

### Übersicht
- **Lüftungs-System:** `/Projekt/eing/luftListe`
- **RLT-Anlagen:** `/Projekt/eing/rltListe`

### 8.1 Lüftungs-System (luftListe)

#### Wichtige Kinder-Elemente

##### 1. Name
**Beispiel:** "Fensterlüftung"

##### 2. Art
**Pfad:** `item/art`

**Mögliche Werte:**
- `LA_FREI` - Freie Lüftung (Fenster)
- `LA_ZENTRAL` - Zentrale Lüftungsanlage
- `LA_DEZENTRAL` - Dezentrale Lüftungsanlage

##### 3. Luftwechselrate
**Pfad:** `item/luftWechsel`

**Attribute:**
- `unit`: String (immer "1/h")

**Beispiel:**
```xml
<luftWechsel auto="true" man="0.5000000" calc="0.0000000" unit="1/h">0.5000000</luftWechsel>
```

##### 4. Wärmerückgewinnung (WRG)
**Pfad:** `item/wrg`

**Werte:**
- `0` - Keine WRG
- `1` - Mit WRG

##### 5. WRG-Grad
**Pfad:** `item/wrgGrad`

**Beispiel:**
```xml
<wrgGrad auto="true" man="0.8000000" calc="0.0000000" unit="-">0.8000000</wrgGrad>
```

**Typische Werte:** 0.75 - 0.95 (75% - 95%)

### 8.2 RLT-Anlagen (rltListe)

**Beschreibung:** Raumlufttechnische Anlagen (komplexe Lüftungsanlagen mit Heizung/Kühlung)

**Hinweis:** Im Beispiel-Projekt nicht vorhanden (Fensterlüftung)

---

## 📝 Nächste Schritte

### Ausstehende Kategorien (Niedrige Priorität)

1. **⏳ PV-Anlagen (pvListe)** - Niedrig
   - Photovoltaik-Module
   - Leistung, Ausrichtung

2. **⏳ Batteriespeicher (batterienListe)** - Niedrig
   - Speicherkapazität
   - Lade-/Entladeleistung

3. **⏳ Maßnahmen (massnahmenListe)** - Niedrig
   - Sanierungsmaßnahmen
   - Kosten, Förderung

---

## 🤝 Mitarbeit

**Dokumentations-Workflow:**
1. Kategorie auswählen (siehe "Nächste Schritte")
2. XML-Struktur analysieren (Python-Script)
3. Dokumentation erweitern (diese Datei)
4. Parser-Code anpassen
5. Testen mit Real-World Daten

**Kontakt:** GitHub Issues oder Discussions

---

**Letzte Aktualisierung:** 1. April 2026  
**Version:** 2.0 (Kategorien 1-8 dokumentiert, 8 von 11 Kategorien vollständig)
