"""Aggregates the per-module JaCoCo reports into one table.

Gradle writes one report per module and no total. This sums them, and prints
the modules separately because the average hides the split: the feature modules
hold the logic and sit near 70%, while the app shell is Compose UI that unit
tests cannot reach.
"""

from __future__ import annotations

import pathlib
import sys
import xml.etree.ElementTree as ET

RAIZ = pathlib.Path(__file__).resolve().parent.parent / "android"
TIPOS = ("INSTRUCTION", "BRANCH", "LINE")


def main() -> int:
    informes = sorted(RAIZ.rglob("reports/jacoco/coverageReport/coverageReport.xml"))
    if not informes:
        print("No reports found. Run ./gradlew coverageReport first.", file=sys.stderr)
        return 1

    total = {t: [0, 0] for t in TIPOS}
    filas = []

    for f in informes:
        modulo = str(f.relative_to(RAIZ)).split("/build/")[0]
        raiz = ET.parse(f).getroot()
        propio = {}
        for contador in raiz.findall("counter"):
            tipo = contador.get("type")
            if tipo not in TIPOS:
                continue
            cubierto = int(contador.get("covered", 0))
            perdido = int(contador.get("missed", 0))
            total[tipo][0] += cubierto
            total[tipo][1] += cubierto + perdido
            propio[tipo] = (cubierto, cubierto + perdido)
        if "LINE" in propio:
            cubierto, n = propio["LINE"]
            filas.append((modulo, cubierto / n * 100 if n else 0.0, cubierto, n))

    ancho = max(len(m) for m, *_ in filas)
    print(f"\n  {'module'.ljust(ancho)}   lines")
    for modulo, pct, cubierto, n in sorted(filas, key=lambda x: -x[1]):
        print(f"  {modulo.ljust(ancho)}  {pct:5.1f}%  ({cubierto}/{n})")

    print()
    for tipo in TIPOS:
        cubierto, n = total[tipo]
        if n:
            print(f"  TOTAL {tipo.ljust(12)} {cubierto / n * 100:5.1f}%  ({cubierto}/{n})")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
