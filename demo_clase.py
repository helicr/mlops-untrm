"""
╔══════════════════════════════════════════════════════════════╗
║         DEMO INTERACTIVA — MLOps Pipeline Paso a Paso       ║
║         Ejecutar desde la raíz del proyecto                 ║
║         python demo_clase.py                                ║
╚══════════════════════════════════════════════════════════════╝
"""

import subprocess
import sys
import json
import os
from pathlib import Path
from datetime import datetime

# Forzar UTF-8 en stdout/stderr para Windows (evita UnicodeEncodeError con cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT   = Path(__file__).resolve().parent
PYTHON = r"C:\bk\software\anaconda3\envs\mlops-ciclo-vida\python.exe"

# ── Colores ANSI ───────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
AZUL   = "\033[94m"
VERDE  = "\033[92m"
ROJO   = "\033[91m"
AMARI  = "\033[93m"
CYAN   = "\033[96m"
GRIS   = "\033[90m"

os.system("color")  # Activar colores ANSI en Windows


# ── Helpers ───────────────────────────────────────────────────────────────────

def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


def cabecera():
    limpiar()
    print(f"{AZUL}{BOLD}")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║         MLOps — Ciclo de Vida de un Modelo ML               ║")
    print("║         Demo Interactiva para Clase                         ║")
    print(f"║         {datetime.now().strftime('%Y-%m-%d  %H:%M')}                                    ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(RESET)


def separador():
    print(f"{GRIS}{'─' * 64}{RESET}")


def titulo_paso(num, total, nombre, descripcion):
    print(f"\n{AZUL}{BOLD}")
    print(f"┌──────────────────────────────────────────────────────────────┐")
    print(f"│  PASO {num}/{total}: {nombre:<54}│")
    print(f"└──────────────────────────────────────────────────────────────┘")
    print(f"{RESET}{AMARI}  {descripcion}{RESET}\n")


def mostrar_comando(cmd):
    print(f"{GRIS}  Comando:{RESET}")
    print(f"{CYAN}{BOLD}  $ {cmd}{RESET}\n")


def pausa(mensaje=None):
    separador()
    if mensaje:
        print(f"{AMARI}  ℹ  {mensaje}{RESET}")
    print(f"{VERDE}{BOLD}  → Pulsa ENTER para continuar al siguiente paso...{RESET}")
    input()


def ok(texto):
    print(f"  {VERDE}✓{RESET}  {texto}")


def info(texto):
    print(f"  {AZUL}→{RESET}  {texto}")


def advertencia(texto):
    print(f"  {AMARI}⚠{RESET}  {texto}")


def error(texto):
    print(f"  {ROJO}✗{RESET}  {texto}")


def mostrar_archivos(rutas):
    print(f"\n  {BOLD}Archivos generados:{RESET}")
    for ruta in rutas:
        p = ROOT / ruta
        if p.exists():
            size = p.stat().st_size
            ok(f"{ruta}  {GRIS}({size:,} bytes){RESET}")
        else:
            error(f"{ruta}  {GRIS}(no encontrado){RESET}")


def ejecutar(cmd, mostrar=True):
    if mostrar:
        mostrar_comando(cmd)
    separador()
    result = subprocess.run(cmd, shell=True, cwd=str(ROOT))
    separador()
    return result.returncode == 0


def mostrar_json(ruta, campos=None):
    p = ROOT / ruta
    if not p.exists():
        advertencia(f"Archivo no encontrado: {ruta}")
        return
    with open(p) as f:
        datos = json.load(f)
    print(f"\n  {BOLD}Contenido de {ruta}:{RESET}")
    if campos:
        for campo in campos:
            val = datos
            for k in campo.split("."):
                val = val.get(k, "—") if isinstance(val, dict) else "—"
            print(f"    {AZUL}{campo}{RESET}: {BOLD}{val}{RESET}")
    else:
        print(json.dumps(datos, indent=4, ensure_ascii=False)[:800])


# ══════════════════════════════════════════════════════════════════════════════
#  INTRODUCCIÓN
# ══════════════════════════════════════════════════════════════════════════════

def intro():
    cabecera()
    print(f"  {BOLD}¿Qué vamos a hacer?{RESET}")
    print()
    print("  Ejecutar el pipeline MLOps completo script a script,")
    print("  observando qué produce cada etapa y cómo se encadenan.")
    print()
    print(f"  {BOLD}Flujo del pipeline:{RESET}")
    print()
    print(f"  {AZUL}[2] Datos{RESET} → {CYAN}[3] Features{RESET} → {AMARI}[4] Entrenamiento{RESET} → "
          f"{VERDE}[5] Evaluación{RESET}")
    print(f"       ↓")
    print(f"  {VERDE}[Tests]{RESET} → {AZUL}[6] API{RESET} → {CYAN}[7] Monitoreo{RESET}")
    print()
    separador()
    print(f"\n  {BOLD}Dataset:{RESET}   California Housing (sklearn)  — 20,640 viviendas")
    print(f"  {BOLD}Modelo:{RESET}    GradientBoostingRegressor")
    print(f"  {BOLD}Objetivo:{RESET}  RMSE < 0.5  |  R² > 0.80")
    print()
    pausa("Comenzamos con la Etapa 2: Preparación de Datos.")


# ══════════════════════════════════════════════════════════════════════════════
#  PASO 1 — PREPARACIÓN DE DATOS
# ══════════════════════════════════════════════════════════════════════════════

def paso_datos():
    cabecera()
    titulo_paso(1, 7, "Preparación de Datos", "src/data/preparar_datos.py")

    print(f"  {BOLD}¿Qué hace este script?{RESET}")
    print("  1. Descarga California Housing desde sklearn")
    print("  2. Valida calidad: nulos, duplicados, columnas")
    print("  3. Limpia outliers extremos (Z-score > 3.0)")
    print("  4. Divide en Train 80% / Test 20% (semilla=42)")
    print()

    ok_paso = ejecutar(f"{PYTHON} src/data/preparar_datos.py")

    if ok_paso:
        mostrar_archivos([
            "data/raw/housing_raw.csv",
            "data/processed/housing_procesado.csv",
            "data/processed/train.csv",
            "data/processed/test.csv",
        ])
        print()
        ok("Sin nulos, sin duplicados, split reproducible con semilla fija")
        advertencia("Los datos crudos (housing_raw.csv) NUNCA se modifican")

    pausa("Observa los CSV generados. Train tiene ~15,835 filas. Test ~3,959.")


# ══════════════════════════════════════════════════════════════════════════════
#  PASO 2 — INGENIERÍA DE FEATURES
# ══════════════════════════════════════════════════════════════════════════════

def paso_features():
    cabecera()
    titulo_paso(2, 7, "Ingeniería de Features", "src/features/ingenieria_features.py")

    print(f"  {BOLD}¿Qué hace este script?{RESET}")
    print("  1. Crea 5 features derivadas (de 8 a 13 columnas):")
    print(f"     {CYAN}rooms_per_person{RESET}   AveRooms / AveOccup")
    print(f"     {CYAN}income_per_room{RESET}    MedInc / AveRooms")
    print(f"     {CYAN}bedroom_ratio{RESET}      AveBedrms / AveRooms")
    print(f"     {CYAN}dist_sacramento{RESET}    distancia euclidiana a Sacramento")
    print(f"     {CYAN}dist_los_angeles{RESET}   distancia euclidiana a Los Ángeles")
    print()
    print(f"  2. {ROJO}fit(){RESET} del StandardScaler SOLO en train  {GRIS}← evita data leakage{RESET}")
    print(f"  3. {VERDE}transform(){RESET} aplicado a train Y test por igual")
    print(f"  4. Guarda {BOLD}scaler.pkl{RESET} para usarlo en la API")
    print()

    ejecutar(f"{PYTHON} src/features/ingenieria_features.py")

    mostrar_archivos([
        "data/processed/train.csv",
        "data/processed/test.csv",
        "experiments/scaler.pkl",
    ])
    print()
    advertencia("Training-Serving Parity: el scaler de producción es ESTE mismo .pkl")

    pausa("Abre train.csv y comprueba que ahora tiene 13 columnas en lugar de 8.")


# ══════════════════════════════════════════════════════════════════════════════
#  PASO 3 — ENTRENAMIENTO
# ══════════════════════════════════════════════════════════════════════════════

def paso_entrenamiento():
    cabecera()
    titulo_paso(3, 7, "Entrenamiento del Modelo", "src/models/entrenar.py")

    print(f"  {BOLD}¿Qué hace este script?{RESET}")
    print("  1. Lee algoritmo e hiperparámetros desde config/config.yaml")
    print("  2. Entrena el modelo con los datos de train")
    print("  3. Registra el experimento en MLflow:")
    print(f"     {CYAN}parámetros{RESET} · {CYAN}métricas{RESET} · {CYAN}artefacto del modelo{RESET}")
    print("  4. Muestra feature importance (qué variables importan más)")
    print("  5. Guarda modelo_produccion.pkl")
    print()

    ejecutar(f"{PYTHON} src/models/entrenar.py")

    mostrar_archivos([
        "experiments/modelo_produccion.pkl",
    ])
    print()
    info("Para ver los experimentos en MLflow UI ejecuta en otra terminal:")
    print(f"  {CYAN}  mlflow ui --backend-store-uri experiments/{RESET}")
    print(f"  {CYAN}  → http://localhost:5000{RESET}")

    pausa("Observa el feature importance en los logs. ¿Qué variable importa más?")


# ══════════════════════════════════════════════════════════════════════════════
#  PASO 4 — EVALUACIÓN
# ══════════════════════════════════════════════════════════════════════════════

def paso_evaluacion():
    cabecera()
    titulo_paso(4, 7, "Evaluación y Gate de Calidad", "src/models/evaluar.py")

    print(f"  {BOLD}¿Qué hace este script?{RESET}")
    print("  1. Carga el modelo y lo evalúa en TEST SET (datos nunca vistos)")
    print("  2. Calcula RMSE, MAE y R²")
    print("  3. Verifica el gate de calidad definido en config.yaml:")
    print(f"     {VERDE}RMSE < 0.50{RESET}  — error de predicción aceptable")
    print(f"     {VERDE}R²   > 0.80{RESET}  — el modelo explica el 80% de la varianza")
    print()
    print(f"  {ROJO}Si NO aprueba → sale con código de error 1{RESET}")
    print(f"  {ROJO}              → en CI/CD el despliegue se cancela{RESET}")
    print()

    ok_eval = ejecutar(f"{PYTHON} src/models/evaluar.py")

    mostrar_archivos(["experiments/reporte_evaluacion.json"])
    mostrar_json("experiments/reporte_evaluacion.json",
                 ["metricas.rmse", "metricas.r2", "aprobado"])
    print()
    if ok_eval:
        ok("Modelo APROBADO — listo para producción")
    else:
        error("Modelo RECHAZADO — revisa los datos o el algoritmo")

    pausa("Este gate de calidad es lo que bloquea el despliegue en GitHub Actions si el modelo es malo.")


# ══════════════════════════════════════════════════════════════════════════════
#  PASO 5 — TESTS
# ══════════════════════════════════════════════════════════════════════════════

def paso_tests():
    cabecera()
    titulo_paso(5, 7, "Tests Automatizados", "pytest tests/ -v")

    print(f"  {BOLD}¿Qué verifican los tests?{RESET}")
    print()
    print(f"  {AZUL}tests/test_datos.py{RESET}")
    print("  · Los datos se cargan correctamente")
    print("  · La validación rechaza datos malos (nulos, columnas faltantes)")
    print("  · La limpieza elimina duplicados e imputa nulos")
    print()
    print(f"  {AZUL}tests/test_modelo.py{RESET}")
    print("  · El modelo genera predicciones sin errores")
    print("  · Las predicciones son números positivos")
    print(f"  · RMSE < 0.50  |  R² > 0.80  {GRIS}(mismo gate que evaluar.py){RESET}")
    print("  · Feature engineering añade las 5 columnas nuevas")
    print()

    ejecutar(f"{PYTHON} -m pytest tests/ -v")

    pausa("En GitHub Actions estos tests se ejecutan en CADA push. Si fallan, el pipeline se detiene.")


# ══════════════════════════════════════════════════════════════════════════════
#  PASO 6 — API
# ══════════════════════════════════════════════════════════════════════════════

def paso_api():
    cabecera()
    titulo_paso(6, 7, "Serving — API REST", "uvicorn src.serving.api:app --reload --port 8000")

    print(f"  {BOLD}¿Qué hace la API?{RESET}")
    print("  1. Carga modelo_produccion.pkl y scaler.pkl en memoria")
    print("  2. Aplica las mismas transformaciones que el Paso 2")
    print(f"     {GRIS}(training-serving parity){RESET}")
    print("  3. Expone los siguientes endpoints:")
    print()
    print(f"  {CYAN}  GET  http://localhost:8000/{RESET}               health check")
    print(f"  {CYAN}  GET  http://localhost:8000/ui{RESET}              Web UI para negocio")
    print(f"  {CYAN}  GET  http://localhost:8000/docs{RESET}            Swagger interactivo")
    print(f"  {CYAN}  POST http://localhost:8000/v1/predecir{RESET}     predicción")
    print()

    separador()
    print(f"\n  {AMARI}{BOLD}Abre una SEGUNDA terminal y ejecuta:{RESET}")
    print()
    print(f"  {CYAN}conda activate mlops-ciclo-vida{RESET}")
    print(f"  {CYAN}cd {ROOT}{RESET}")
    print(f"  {CYAN}uvicorn src.serving.api:app --reload --port 8000{RESET}")
    print()
    print(f"  {AMARI}{BOLD}Luego abre en el navegador:{RESET}")
    print(f"  {CYAN}  http://localhost:8000/ui{RESET}")
    print(f"  {CYAN}  http://localhost:8000/docs{RESET}")
    print()
    separador()
    print(f"\n  {BOLD}Prueba de predicción (en otra terminal):{RESET}")
    print(f"""
  {CYAN}curl -X POST "http://localhost:8000/v1/predecir" ^
    -H "Content-Type: application/json" ^
    -d "{{\\"MedInc\\": 8.0, \\"HouseAge\\": 10, \\"AveRooms\\": 7.0,
         \\"AveBedrms\\": 1.0, \\"Population\\": 800, \\"AveOccup\\": 2.5,
         \\"Latitude\\": 34.0, \\"Longitude\\": -118.2}}"{RESET}
""")
    print(f"  {BOLD}Respuesta esperada:{RESET}")
    print(f"""  {VERDE}{{
    "prediccion_normalizada": 3.45,
    "precio_estimado_usd": 345000.0,
    "unidad": "USD"
  }}{RESET}""")

    pausa("Prueba distintos valores en el formulario /ui. ¿Qué pasa con MedInc alto vs bajo?")


# ══════════════════════════════════════════════════════════════════════════════
#  PASO 7 — MONITOREO
# ══════════════════════════════════════════════════════════════════════════════

def paso_monitoreo():
    cabecera()
    titulo_paso(7, 7, "Monitoreo — Detección de Drift", "src/monitoring/monitor.py")

    print(f"  {BOLD}¿Qué hace este script?{RESET}")
    print()
    print(f"  {AZUL}Data Drift — PSI (Population Stability Index){RESET}")
    print("  Compara la distribución de los datos de producción")
    print("  contra los datos de entrenamiento por cada feature.")
    print()
    print(f"  {VERDE}  PSI < 0.10{RESET}  Sin cambio          → modelo estable")
    print(f"  {AMARI}  PSI < 0.20{RESET}  Cambio moderado     → vigilar")
    print(f"  {ROJO}  PSI ≥ 0.20{RESET}  Drift significativo → re-entrenar")
    print()
    print(f"  {AZUL}Concept Drift — Degradación del RMSE{RESET}")
    print("  Si el RMSE actual sube más de un 10% sobre el original")
    print("  → el modelo ya no predice bien en producción")
    print()

    ejecutar(f"{PYTHON} src/monitoring/monitor.py")

    mostrar_archivos(["experiments/reporte_monitoreo.json"])
    mostrar_json("experiments/reporte_monitoreo.json",
                 ["requiere_reentrenamiento", "accion_recomendada"])

    pausa("Si requiere_reentrenamiento es true → el ciclo MLOps vuelve a empezar desde el Paso 1.")


# ══════════════════════════════════════════════════════════════════════════════
#  CIERRE
# ══════════════════════════════════════════════════════════════════════════════

def cierre():
    cabecera()
    print(f"  {VERDE}{BOLD}✅  PIPELINE COMPLETO{RESET}")
    print()
    print("  Hemos ejecutado las 7 etapas del ciclo MLOps:")
    print()
    print(f"  {VERDE}✓{RESET}  Etapa 2 — Preparación de datos")
    print(f"  {VERDE}✓{RESET}  Etapa 3 — Ingeniería de features")
    print(f"  {VERDE}✓{RESET}  Etapa 4 — Entrenamiento con MLflow")
    print(f"  {VERDE}✓{RESET}  Etapa 5 — Evaluación y gate de calidad")
    print(f"  {VERDE}✓{RESET}  Tests automatizados")
    print(f"  {VERDE}✓{RESET}  Etapa 6 — API REST en producción")
    print(f"  {VERDE}✓{RESET}  Etapa 7 — Monitoreo de drift")
    print()
    separador()
    print()
    print(f"  {BOLD}Archivos generados durante la sesión:{RESET}")
    mostrar_archivos([
        "data/raw/housing_raw.csv",
        "data/processed/train.csv",
        "data/processed/test.csv",
        "experiments/scaler.pkl",
        "experiments/modelo_produccion.pkl",
        "experiments/reporte_evaluacion.json",
        "experiments/reporte_monitoreo.json",
    ])
    print()
    separador()
    print()
    print(f"  {BOLD}En GitHub Actions este mismo flujo se ejecuta{RESET}")
    print(f"  automáticamente en cada {CYAN}git push{RESET} a master.")
    print()
    print(f"  {GRIS}Ver en: https://github.com/helicr/mlops-untrm/actions{RESET}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

PASOS = [
    ("intro",            intro),
    ("datos",            paso_datos),
    ("features",         paso_features),
    ("entrenamiento",    paso_entrenamiento),
    ("evaluacion",       paso_evaluacion),
    ("tests",            paso_tests),
    ("api",              paso_api),
    ("monitoreo",        paso_monitoreo),
    ("cierre",           cierre),
]


def main():
    # Permitir empezar desde un paso concreto
    inicio = 0
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        for i, (nombre, _) in enumerate(PASOS):
            if nombre == arg:
                inicio = i
                break

    for nombre, fn in PASOS[inicio:]:
        fn()

    print(f"\n  {VERDE}{BOLD}Demo finalizada.{RESET}\n")


if __name__ == "__main__":
    main()
