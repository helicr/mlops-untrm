"""
============================================================
DEMO — Inferencia en Tiempo Real via API REST
Ciclo de Vida MLOps · California Housing Price Predictor
============================================================
Ejecutar:
  python demo_api.py
============================================================
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

API_URL    = "http://localhost:8000"
ENDPOINT   = f"{API_URL}/v1/predecir"
IMAGEN     = "mlops-ciclo-vida-api"

# ── Colores consola ────────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
AZUL    = "\033[94m"
VERDE   = "\033[92m"
NARANJA = "\033[93m"
ROJO    = "\033[91m"
CYAN    = "\033[96m"
GRIS    = "\033[90m"


def cls():
    os.system("cls" if os.name == "nt" else "clear")


def cabecera():
    print(f"{AZUL}{BOLD}")
    print("=" * 60)
    print("   DEMO -- INFERENCIA EN TIEMPO REAL VIA API REST")
    print("   Ciclo de Vida MLOps | California Housing")
    print("=" * 60)
    print(RESET)


def separador(titulo=""):
    ancho = 60
    if titulo:
        pad = (ancho - len(titulo) - 2) // 2
        print(f"\n{AZUL}{'-' * pad} {titulo} {'-' * pad}{RESET}\n")
    else:
        print(f"{GRIS}{'-' * ancho}{RESET}")


def ok(msg):    print(f"{VERDE}  OK   {msg}{RESET}")
def info(msg):  print(f"{CYAN}  >>  {msg}{RESET}")
def warn(msg):  print(f"{NARANJA}  **  {msg}{RESET}")
def err(msg):   print(f"{ROJO}  !!  {msg}{RESET}")


def pausa():
    print(f"\n{GRIS}  Pulsa ENTER para volver al menu...{RESET}")
    input()


# ── Helpers HTTP ───────────────────────────────────────────────────────────────

def get(path):
    try:
        req = urllib.request.Request(f"{API_URL}{path}")
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read()), r.status
    except urllib.error.URLError:
        return None, 0


def post_prediccion(datos: dict):
    body = json.dumps(datos).encode("utf-8")
    req  = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            latencia_ms = (time.perf_counter() - t0) * 1000
            return json.loads(r.read()), r.status, latencia_ms
    except urllib.error.HTTPError as e:
        latencia_ms = (time.perf_counter() - t0) * 1000
        return json.loads(e.read()), e.code, latencia_ms
    except urllib.error.URLError:
        return None, 0, 0


def api_activa():
    resp, status = get("/health")
    return status == 200


# ── Perfiles de viviendas para la demo ────────────────────────────────────────

PERFILES = [
    {
        "nombre":   "San Francisco · Barrio alto",
        "zona":     "SF Bay Area",
        "datos": {"MedInc": 8.50, "HouseAge": 15, "AveRooms": 6.5,
                  "AveBedrms": 1.1, "Population": 1200, "AveOccup": 2.8,
                  "Latitude": 37.78, "Longitude": -122.42},
    },
    {
        "nombre":   "Los Angeles · Zona media",
        "zona":     "LA Metro",
        "datos": {"MedInc": 6.20, "HouseAge": 25, "AveRooms": 5.8,
                  "AveBedrms": 1.2, "Population": 1800, "AveOccup": 3.1,
                  "Latitude": 34.05, "Longitude": -118.25},
    },
    {
        "nombre":   "San Diego · Costa",
        "zona":     "San Diego",
        "datos": {"MedInc": 4.80, "HouseAge": 20, "AveRooms": 5.2,
                  "AveBedrms": 1.1, "Population": 2200, "AveOccup": 3.4,
                  "Latitude": 32.72, "Longitude": -117.15},
    },
    {
        "nombre":   "Sacramento · Capital",
        "zona":     "Central Valley",
        "datos": {"MedInc": 3.50, "HouseAge": 35, "AveRooms": 4.8,
                  "AveBedrms": 1.0, "Population": 3100, "AveOccup": 3.8,
                  "Latitude": 38.58, "Longitude": -121.49},
    },
    {
        "nombre":   "Valle Central · Rural",
        "zona":     "Fresno Area",
        "datos": {"MedInc": 2.10, "HouseAge": 40, "AveRooms": 4.2,
                  "AveBedrms": 1.1, "Population": 2800, "AveOccup": 4.1,
                  "Latitude": 36.74, "Longitude": -119.77},
    },
]


# ══════════════════════════════════════════════════════════════════════════════
#  PASOS DE LA DEMO
# ══════════════════════════════════════════════════════════════════════════════

def paso1_verificar_api():
    cls(); cabecera()
    separador("PASO 1 · Estado de la API")

    info("Comprobando imagen Docker...")
    r = subprocess.run(
        f"docker images {IMAGEN} --format table",
        shell=True, capture_output=True, text=True
    )
    if IMAGEN in r.stdout:
        ok(f"Imagen encontrada: {IMAGEN}")
    else:
        warn(f"Imagen no encontrada: {IMAGEN}")

    print()
    info("Comprobando contenedor activo...")
    r2 = subprocess.run(
        "docker ps --filter name=mlops --format \"table {{.Names}}\\t{{.Status}}\\t{{.Ports}}\"",
        shell=True, capture_output=True, text=True
    )
    print(f"  {r2.stdout.strip()}")

    print()
    info(f"Llamando a {API_URL}/health ...")
    resp, status = get("/health")
    if status == 200:
        ok(f"API activa — status: {status}")
        print()
        for k, v in resp.items():
            print(f"  {CYAN}{k:<20}{RESET} {BOLD}{v}{RESET}")
    else:
        err("API no responde. Ejecuta el Paso 2 para levantarla.")

    pausa()


def paso2_levantar_api():
    cls(); cabecera()
    separador("PASO 2 · Levantar la API con Docker Compose")

    if api_activa():
        ok("La API ya esta activa. No es necesario levantarla.")
        pausa()
        return

    info("Ejecutando: docker compose up -d ...")
    print()
    subprocess.run("docker compose up -d", shell=True)
    print()

    info("Esperando a que la API arranque")
    for i in range(15):
        time.sleep(1)
        print(f"  {GRIS}  {i+1}s...{RESET}", end="\r")
        if api_activa():
            print()
            ok(f"API lista en {i+1} segundos.")
            break
    else:
        print()
        err("La API no respondio en 15s. Revisa los logs: docker compose logs -f api")

    pausa()


def paso3_health_check():
    cls(); cabecera()
    separador("PASO 3 · Health Check e Info del Modelo")

    # /health
    info(f"GET {API_URL}/health")
    resp, status = get("/health")
    print()
    if resp:
        print(f"  {BOLD}HTTP {status}{RESET}")
        print(f"  {json.dumps(resp, indent=4, ensure_ascii=False)}")
    else:
        err("Sin respuesta.")

    print()

    # /v1/info-modelo
    info(f"GET {API_URL}/v1/info-modelo")
    resp2, status2 = get("/v1/info-modelo")
    print()
    if resp2:
        print(f"  {BOLD}HTTP {status2}{RESET}")
        print(f"  {json.dumps(resp2, indent=4, ensure_ascii=False)}")
    else:
        err("Sin respuesta.")

    pausa()


def paso4_prediccion_individual():
    cls(); cabecera()
    separador("PASO 4 · Prediccion Individual (1 registro)")

    if not api_activa():
        err("API no activa. Ejecuta el Paso 2 primero.")
        pausa()
        return

    perfil = PERFILES[0]  # San Francisco
    datos  = perfil["datos"]

    info(f"Perfil: {perfil['nombre']}")
    print()

    separador("Request enviado")
    print(f"  {BOLD}POST {ENDPOINT}{RESET}")
    print(f"  {json.dumps(datos, indent=4)}")

    resp, status, latencia = post_prediccion(datos)
    print()

    separador("Response recibida")
    if status == 200:
        precio = int(resp["precio_estimado_usd"])
        print(f"  {BOLD}HTTP {status}{RESET}  {GRIS}({latencia:.1f} ms){RESET}")
        print()
        print(f"  {CYAN}prediccion_normalizada{RESET}   {BOLD}{resp['prediccion_normalizada']}{RESET}  (x$100k)")
        print(f"  {CYAN}precio_estimado_usd   {RESET}   {BOLD}{VERDE}${precio:,}{RESET}")
        print(f"  {CYAN}latencia              {RESET}   {BOLD}{latencia:.1f} ms{RESET}")
    else:
        err(f"Error HTTP {status}: {resp}")

    separador()
    info("Endpoints disponibles:")
    print(f"  {GRIS}  Interfaz web  →  {API_URL}/ui{RESET}")
    print(f"  {GRIS}  Swagger/Docs  →  {API_URL}/docs{RESET}")
    print(f"  {GRIS}  Health        →  {API_URL}/health{RESET}")

    pausa()


def paso5_predicciones_multiples():
    cls(); cabecera()
    separador("PASO 5 · Comparativa de Precios por Ciudad")

    if not api_activa():
        err("API no activa. Ejecuta el Paso 2 primero.")
        pausa()
        return

    info(f"Enviando {len(PERFILES)} solicitudes a {ENDPOINT}")
    print()

    resultados = []
    for perfil in PERFILES:
        resp, status, latencia = post_prediccion(perfil["datos"])
        if status == 200:
            resultados.append({
                "nombre":  perfil["nombre"],
                "medinc":  perfil["datos"]["MedInc"],
                "precio":  int(resp["precio_estimado_usd"]),
                "latencia": latencia,
            })
            ok(f"{perfil['nombre']:<35} ${resultados[-1]['precio']:>10,}   ({latencia:.0f} ms)")
        else:
            err(f"{perfil['nombre']} — Error {status}")

    if not resultados:
        pausa()
        return

    separador("Resumen")
    precios   = [r["precio"]  for r in resultados]
    latencias = [r["latencia"] for r in resultados]

    print(f"  {CYAN}{'Precio maximo':<25}{RESET} {VERDE}${max(precios):,}{RESET}  ({resultados[precios.index(max(precios))]['nombre']})")
    print(f"  {CYAN}{'Precio minimo':<25}{RESET} {ROJO}${min(precios):,}{RESET}  ({resultados[precios.index(min(precios))]['nombre']})")
    print(f"  {CYAN}{'Precio medio':<25}{RESET} ${sum(precios)//len(precios):,}")
    print()
    print(f"  {CYAN}{'Latencia media':<25}{RESET} {sum(latencias)/len(latencias):.1f} ms/request")
    print(f"  {CYAN}{'Latencia maxima':<25}{RESET} {max(latencias):.1f} ms")
    print()

    # Barra visual de precios
    separador("Distribucion de precios")
    max_p = max(precios)
    for r in resultados:
        barra_len = int(r["precio"] / max_p * 30)
        barra = "#" * barra_len
        color = VERDE if r["precio"] > 300_000 else NARANJA if r["precio"] > 150_000 else ROJO
        print(f"  {r['nombre']:<35} {color}{barra:<30}{RESET} ${r['precio']:,}")

    pausa()


def paso6_prueba_curl():
    cls(); cabecera()
    separador("PASO 6 · Equivalente con curl (para mostrar en clase)")

    info("Este es el comando curl equivalente a lo que hace la demo:")
    print()

    datos = PERFILES[0]["datos"]
    curl  = (
        f"curl -X POST \"{ENDPOINT}\" \\\n"
        f"     -H \"Content-Type: application/json\" \\\n"
        f"     -d '{json.dumps(datos)}'"
    )
    print(f"  {BOLD}{curl}{RESET}")
    print()

    info("Ejecutando la llamada...")
    print()

    resp, status, latencia = post_prediccion(datos)
    if status == 200:
        ok(f"HTTP {status}  ({latencia:.1f} ms)")
        print()
        print(f"  {json.dumps(resp, indent=4)}")
    else:
        err(f"Error {status}")

    separador()
    info("Tambien disponible en el navegador:")
    print(f"\n  {BOLD}{AZUL}  {API_URL}/ui    <- Interfaz web{RESET}")
    print(f"  {BOLD}{AZUL}  {API_URL}/docs  <- Swagger interactivo{RESET}\n")

    pausa()


def paso7_demo_completa():
    for paso in [paso1_verificar_api, paso2_levantar_api, paso3_health_check,
                 paso4_prediccion_individual, paso5_predicciones_multiples, paso6_prueba_curl]:
        paso()


# ══════════════════════════════════════════════════════════════════════════════
#  MENU PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def menu():
    opciones = {
        "1": ("Verificar estado de la API y Docker",          paso1_verificar_api),
        "2": ("Levantar la API  (docker compose up -d)",      paso2_levantar_api),
        "3": ("Health check e info del modelo",               paso3_health_check),
        "4": ("Prediccion individual  (1 vivienda)",          paso4_prediccion_individual),
        "5": ("Comparativa de precios por ciudad  (5 calls)", paso5_predicciones_multiples),
        "6": ("Mostrar equivalente curl",                     paso6_prueba_curl),
        "7": (f"{BOLD}Demo completa (pasos 1 a 6){RESET}",   paso7_demo_completa),
        "0": ("Salir",                                        None),
    }

    while True:
        cls(); cabecera()

        print(f"  {BOLD}Selecciona una opcion:{RESET}\n")
        for key, (desc, _) in opciones.items():
            if key == "7":
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
            warn("Opcion no valida.")
            pausa()


if __name__ == "__main__":
    os.system("color")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    menu()
