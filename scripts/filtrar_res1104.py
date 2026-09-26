"""
Descarga el CSV oficial "Precios EESS desde Diciembre 2024" (Res. 1104, Secretaría de Energía),
se queda con el último período declarado, la localidad y el canal pedidos, y lo guarda chico
para que Google Apps Script lo pueda leer (el original pesa ~128 MB; Apps Script admite 50 MB).
Parámetros por variables de entorno (se definen en el workflow, no en este archivo).
"""
import csv
import io
import os
import sys
import unicodedata
import urllib.request

URL = os.environ["URL_CSV"]
LOCALIDAD = os.environ["LOCALIDAD"]
CANAL = os.environ["CANAL"]
SALIDA = os.environ["SALIDA"]
COLUMNAS = ["periodo", "fecha", "localidad", "operador", "direccion", "bandera", "producto",
            "precio_surtidor", "precio_con_impuestos"]


def normalizar(s):
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


def main():
    loc, canal = normalizar(LOCALIDAD), normalizar(CANAL)
    filas, periodo_max, total = [], "", 0
    with urllib.request.urlopen(URL, timeout=600) as resp:
        lector = csv.DictReader(io.TextIOWrapper(resp, encoding="utf-8-sig", newline=""))
        faltan = [c for c in COLUMNAS if c not in (lector.fieldnames or [])]
        if faltan:
            sys.exit("Cambió el formato del CSV oficial. Faltan columnas: " + ", ".join(faltan))
        for r in lector:
            total += 1
            if normalizar(r["localidad"]) != loc or normalizar(r["canal_de_comercializacion"]) != canal:
                continue
            p = r["periodo"]
            if p > periodo_max:
                periodo_max, filas = p, []
            if p == periodo_max:
                filas.append({c: r[c] for c in COLUMNAS})
    if not filas:
        sys.exit("No se encontraron filas para " + LOCALIDAD)
    os.makedirs(os.path.dirname(SALIDA) or ".", exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas)
    print(f"Leídas {total} filas. Período {periodo_max}: {len(filas)} filas de {LOCALIDAD} -> {SALIDA}")


if __name__ == "__main__":
    main()
