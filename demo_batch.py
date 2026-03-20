"""
============================================================
DEMO — Inferencia Batch con Docker
Ciclo de Vida MLOps · California Housing Price Predictor
============================================================
Ejecutar:
  python demo_batch.py
============================================================
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from glob import glob

ROOT       = Path(__file__).resolve().parent
PYTHON     = r"C:\bk\software\anaconda3\envs\mlops-ciclo-vida\python.exe"
IMAGEN     = "mlops-ciclo-vida-api"
INPUT_CSV  = "data/nuevas_viviendas.csv"
OUTPUT_CSV = "output/predicciones_batch.csv"
OUTPUT_DIR = ROOT / "output"

# ── Colores consola ────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
AZUL   = "\033[94m"
VERDE  = "\033[92m"
NARANJA= "\033[93m"
ROJO   = "\033[91m"
CYAN   = "\033[96m"
GRIS   = "\033[90m"


def cls():
    os.system("cls" if os.name == "nt" else "clear")


def cabecera():
    print(f"{AZUL}{BOLD}")
    print("=" * 60)
    print("   DEMO -- INFERENCIA BATCH CON DOCKER")
    print("   Ciclo de Vida MLOps | California Housing")
    print("=" * 60)
    print(RESET)


def separador(titulo=""):
    ancho = 60
    if titulo:
        pad = (ancho - len(titulo) - 2) // 2
        print(f"\n{AZUL}{'─' * pad} {titulo} {'─' * pad}{RESET}\n")
    else:
        print(f"{GRIS}{'─' * ancho}{RESET}")


def ok(msg):    print(f"{VERDE}  OK   {msg}{RESET}")
def info(msg):  print(f"{CYAN}  >>  {msg}{RESET}")
def warn(msg):  print(f"{NARANJA}  **  {msg}{RESET}")
def error(msg): print(f"{ROJO}  !!  {msg}{RESET}")


def pausa():
    print(f"\n{GRIS}  Pulsa ENTER para volver al menú...{RESET}")
    input()


def ejecutar(cmd, mostrar_output=True):
    """Ejecuta un comando y muestra el output en tiempo real."""
    resultado = subprocess.run(
        cmd, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace"
    )
    if mostrar_output and resultado.stdout:
        print(resultado.stdout)
    return resultado.returncode, resultado.stdout


# ══════════════════════════════════════════════════════════════════════════════
#  PASOS DE LA DEMO
# ══════════════════════════════════════════════════════════════════════════════

def paso1_verificar_imagen():
    cls(); cabecera()
    separador("PASO 1 · Verificar imagen Docker")
    info("Comprobando que la imagen existe en el registro local...")
    print()

    code, out = ejecutar(f"docker images {IMAGEN} --format table", mostrar_output=False)

    if IMAGEN in out:
        ok(f"Imagen encontrada: {IMAGEN}")
        print()
        ejecutar(f'docker images {IMAGEN} --format "table {{{{.Repository}}}}\\t{{{{.Tag}}}}\\t{{{{.Size}}}}\\t{{{{.CreatedSince}}}}"')
    else:
        warn("Imagen no encontrada. Construyendo ahora...")
        print()
        ejecutar(f"docker build -t {IMAGEN} .")

    separador()
    info("Contenedor activo:")
    ejecutar(f'docker ps --filter name=mlops --format "table {{{{.Names}}}}\\t{{{{.Status}}}}\\t{{{{.Ports}}}}"')
    pausa()


def paso2_generar_entrada():
    cls(); cabecera()
    separador("PASO 2 · Generar fichero de entrada")
    info(f"Generando {INPUT_CSV} con 10 viviendas de ejemplo...")
    print()

    ejecutar(f'"{PYTHON}" data/generar_muestra_batch.py')

    ruta = ROOT / INPUT_CSV
    if ruta.exists():
        ok(f"Fichero creado: {ruta}")
        separador("Contenido del CSV de entrada")
        print(f"  {GRIS}{'Campo':<14} {'Descripción'}{RESET}")
        campos = {
            "MedInc":     "Ingreso mediano del bloque (x$10k)",
            "HouseAge":   "Edad media de las viviendas (años)",
            "AveRooms":   "Promedio de habitaciones",
            "AveBedrms":  "Promedio de dormitorios",
            "Population": "Población del bloque censal",
            "AveOccup":   "Promedio de ocupantes por vivienda",
            "Latitude":   "Latitud (California)",
            "Longitude":  "Longitud (California)",
        }
        for k, v in campos.items():
            print(f"  {CYAN}{k:<14}{RESET} {v}")
        print()
        separador("Primeras filas")
        with open(ruta) as f:
            for i, linea in enumerate(f):
                color = BOLD if i == 0 else RESET
                print(f"  {color}{linea.rstrip()}{RESET}")
    else:
        error("No se pudo crear el fichero de entrada.")

    pausa()


def paso3_ejecutar_inferencia():
    cls(); cabecera()
    separador("PASO 3 · Ejecutar inferencia batch dentro del contenedor")

    ruta_input = ROOT / INPUT_CSV
    if not ruta_input.exists():
        warn(f"Fichero de entrada no encontrado: {INPUT_CSV}")
        warn("Ejecuta primero el Paso 2.")
        pausa()
        return

    info("Lanzando contenedor Docker...")
    info(f"  Entrada  → {INPUT_CSV}")
    info(f"  Salida   → {OUTPUT_CSV}")
    print()

    OUTPUT_DIR.mkdir(exist_ok=True)

    cmd = (
        f"docker run --rm "
        f"-v {ROOT}\\data:/app/data "
        f"-v {ROOT}\\output:/app/output "
        f"-v {ROOT}\\experiments:/app/experiments "
        f"{IMAGEN} "
        f"python src/serving/batch_inference.py "
        f"--input {INPUT_CSV} "
        f"--output {OUTPUT_CSV}"
    )

    separador("Log de ejecución")
    code, out = ejecutar(cmd)

    if (ROOT / OUTPUT_CSV).exists():
        ok("Inferencia completada con éxito.")
    else:
        error("No se generó el fichero de salida. Revisa el log.")

    pausa()


def paso4_ver_predicciones():
    cls(); cabecera()
    separador("PASO 4 · Predicciones generadas")

    ruta = ROOT / OUTPUT_CSV
    if not ruta.exists():
        warn(f"Fichero no encontrado: {OUTPUT_CSV}")
        warn("Ejecuta primero el Paso 3.")
        pausa()
        return

    import csv
    with open(ruta, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    ok(f"Total de predicciones: {len(filas)}")
    print()

    # Cabecera tabla
    cols = ["MedInc", "HouseAge", "Latitude", "prediccion_normalizada", "precio_estimado_usd"]
    anchos = [8, 10, 10, 24, 22]
    cabecera_tabla = "  " + "".join(f"{c:<{a}}" for c, a in zip(cols, anchos))
    print(f"{BOLD}{AZUL}{cabecera_tabla}{RESET}")
    print(f"  {GRIS}{'─' * sum(anchos)}{RESET}")

    for fila in filas:
        precio = int(fila["precio_estimado_usd"])
        color = VERDE if precio > 300_000 else NARANJA if precio > 150_000 else ROJO
        valores = [
            fila["MedInc"], fila["HouseAge"], fila["Latitude"],
            fila["prediccion_normalizada"],
            f"{color}${precio:,}{RESET}"
        ]
        linea = "  " + "".join(
            f"{v:<{a}}" for v, a in zip(valores[:-1], anchos[:-1])
        ) + f"  {valores[-1]}"
        print(linea)

    print()
    separador("Leyenda")
    print(f"  {VERDE}[+]{RESET} > $300,000   {NARANJA}[~]{RESET} $150k-$300k   {ROJO}[-]{RESET} < $150,000")
    print(f"\n  {GRIS}Unidad: precio mediano del bloque censal (California 1990){RESET}")
    pausa()


def paso5_ver_reporte():
    cls(); cabecera()
    separador("PASO 5 · Reporte de ejecución")

    reportes = sorted(glob(str(ROOT / "output" / "reporte_batch_*.json")), reverse=True)
    if not reportes:
        warn("No hay reportes generados. Ejecuta primero el Paso 3.")
        pausa()
        return

    ruta = reportes[0]
    with open(ruta, encoding="utf-8") as f:
        r = json.load(f)

    ok(f"Reporte: {Path(ruta).name}")
    print()

    separador("Resumen de ejecución")
    datos = [
        ("Batch ID",              r.get("batch_id", "—")),
        ("Timestamp",             r.get("timestamp", "—")[:19].replace("T", " ")),
        ("Modelo",                r.get("modelo", "—")),
        ("Registros entrada",     f"{r.get('n_registros_entrada', 0):,}"),
        ("Registros procesados",  f"{r.get('n_registros_procesados', 0):,}"),
        ("Registros descartados", f"{r.get('n_registros_descartados', 0):,}"),
    ]
    for k, v in datos:
        print(f"  {CYAN}{k:<25}{RESET} {BOLD}{v}{RESET}")

    separador("Rendimiento")
    t = r.get("tiempos_ms", {})
    print(f"  {CYAN}{'Transformación':<25}{RESET} {t.get('transformacion', 0)} ms")
    print(f"  {CYAN}{'Predicción':<25}{RESET} {t.get('prediccion', 0)} ms")
    print(f"  {CYAN}{'Total':<25}{RESET} {BOLD}{t.get('total', 0)} ms{RESET}")
    print(f"  {CYAN}{'Throughput':<25}{RESET} {BOLD}{VERDE}{r.get('throughput_reg_seg', 0):,.0f} pred/s{RESET}")
    print(f"  {CYAN}{'Latencia/registro':<25}{RESET} {r.get('latencia_ms_registro', 0)} ms")

    separador("Distribución de predicciones (x$100k)")
    stats = r.get("estadisticas_predicciones", {})
    for k in ["min", "p25", "media", "p75", "max"]:
        val = stats.get(k, 0)
        barra = "|" * int(val * 4)
        print(f"  {CYAN}{k.upper():<8}{RESET} {val:.4f}  {AZUL}{barra}{RESET}")

    pausa()


def paso6_demo_completa():
    """Ejecuta todos los pasos en secuencia con pausas."""
    for paso in [paso1_verificar_imagen, paso2_generar_entrada,
                 paso3_ejecutar_inferencia, paso4_ver_predicciones,
                 paso5_ver_reporte]:
        paso()


# ══════════════════════════════════════════════════════════════════════════════
#  MENÚ PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def menu():
    opciones = {
        "1": ("Verificar imagen Docker",                paso1_verificar_imagen),
        "2": ("Generar fichero de entrada (CSV)",       paso2_generar_entrada),
        "3": ("Ejecutar inferencia batch (Docker)",     paso3_ejecutar_inferencia),
        "4": ("Ver predicciones generadas",             paso4_ver_predicciones),
        "5": ("Ver reporte de ejecución (JSON)",        paso5_ver_reporte),
        "6": (f"{BOLD}Demo completa (pasos 1→5){RESET}", paso6_demo_completa),
        "0": ("Salir",                                  None),
    }

    while True:
        cls(); cabecera()

        print(f"  {BOLD}Selecciona una opcion:{RESET}\n")
        for key, (desc, _) in opciones.items():
            if key == "6":
                print(f"  {NARANJA}  {key}.{RESET}  {desc}")
            elif key == "0":
                print(f"\n  {GRIS}  {key}.  {desc}{RESET}")
            else:
                print(f"  {CYAN}  {key}.{RESET}  {desc}")

        print()
        opcion = input(f"  {BOLD}>> Opcion: {RESET}").strip()

        if opcion == "0":
            cls()
            print(f"\n{VERDE}  Demo finalizada.{RESET}\n")
            sys.exit(0)

        if opcion in opciones:
            _, fn = opciones[opcion]
            fn()
        else:
            warn("Opción no válida.")
            pausa()


if __name__ == "__main__":
    # Habilitar colores y UTF-8 en Windows
    os.system("color")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    menu()
