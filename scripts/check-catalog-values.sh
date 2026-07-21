#!/usr/bin/env bash
#
# check-catalog-values.sh — Guerteln plus Hosentraeger beim Rechtsrisiko.
#
# Lehnt jeden Commit ab, der Dateien unter catalog/values/ oder catalog-private/
# in den Index bringt. Diese Verzeichnisse enthalten Normzahlenwerte aus
# lizenzierten Quellen (DIN/Beuth) und duerfen NIE im oeffentlichen Repo landen.
#
# Die .gitignore allein reicht nicht: sie greift nur fuer ungetrackte Dateien.
# Wer eine Datei mit `git add -f` erzwingt oder sie per `git mv` aus einem
# getrackten Pfad hineinschiebt, umgeht sie lautlos — genau so waeren die
# 605 KB norm-abgeleiteten Dateien fast wieder im Public-Stand gelandet.
#
# Einsatz:
#   - Pre-Commit-Hook:  ln -sf ../../scripts/check-catalog-values.sh .git/hooks/pre-commit
#   - CI:               bash scripts/check-catalog-values.sh --all
#
# Exit 0 = sauber, Exit 1 = Fund.

set -euo pipefail

GESPERRT='^(catalog/values/|catalog-private/)'
MODUS="${1:-}"

if [ "$MODUS" = "--all" ]; then
  # CI-Modus: gesamten getrackten Baum pruefen, nicht nur den Index
  BEFUND=$(git ls-files | grep -E "$GESPERRT" || true)
  KONTEXT="im getrackten Baum"
else
  # Hook-Modus: nur was gerade committet werden soll
  BEFUND=$(git diff --cached --name-only --diff-filter=ACMR | grep -E "$GESPERRT" || true)
  KONTEXT="im Commit"
fi

if [ -n "$BEFUND" ]; then
  echo "FEHLER: geschuetzte Katalog-Dateien $KONTEXT gefunden." >&2
  echo "" >&2
  echo "$BEFUND" | sed 's/^/  /' >&2
  echo "" >&2
  echo "catalog/values/ und catalog-private/ enthalten urheberrechtlich" >&2
  echo "geschuetzte Normzahlenwerte (DIN/Beuth) und gehoeren nicht ins Repo." >&2
  echo "" >&2
  echo "Aus dem Index nehmen, Dateien bleiben auf der Platte:" >&2
  echo "  git rm -r --cached <pfad>" >&2
  exit 1
fi

echo "[check-catalog-values] OK — keine geschuetzten Katalog-Dateien $KONTEXT."
exit 0
