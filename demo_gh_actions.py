"""
============================================================
DEMO — CI/CD con GitHub Actions
Ciclo de Vida MLOps · California Housing Price Predictor
============================================================
Ejecutar:
  python demo_gh_actions.py
============================================================
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

ROOT   = Path(__file__).resolve().parent
PYTHON = r"C:\bk\software\anaconda3\envs\mlops-ciclo-vida\python.exe"
WORKFLOW = ROOT / ".github" / "workflows" / "ci_cd.yaml"

# ── Colores consola ────────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
AZUL    = "\033[94m"
VERDE   = "\033[92m"
NARANJA = "\033[93m"
ROJO    = "\033[91m"
CYAN    = "\033[96m"
GRIS    = "\033[90m"
MORADO  = "\033[95m"


def cls():
    os.system("cls" if os.name == "nt" else "clear")


def cabecera():
    print(f"{AZUL}{BOLD}")
    print("=" * 60)
    print("   DEMO -- CI/CD CON GITHUB ACTIONS")
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


def ok(msg):     print(f"{VERDE}  OK   {msg}{RESET}")
def info(msg):   print(f"{CYAN}  >>  {msg}{RESET}")
def warn(msg):   print(f"{NARANJA}  **  {msg}{RESET}")
def err(msg):    print(f"{ROJO}  !!  {msg}{RESET}")
def titulo(msg): print(f"{MORADO}{BOLD}  {msg}{RESET}")


def pausa():
    print(f"\n{GRIS}  Pulsa ENTER para volver al menu...{RESET}")
    input()


def ejecutar(cmd, mostrar_output=True, timeout=120):
    resultado = subprocess.run(
        cmd, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
        timeout=timeout
    )
    if mostrar_output and resultado.stdout:
        enc = sys.stdout.encoding or "utf-8"
        for linea in resultado.stdout.splitlines():
            linea_strip = linea.strip()
            if not linea_strip:
                continue
            linea_strip = linea_strip.encode(enc, errors="replace").decode(enc)
            if "PASSED" in linea or "passed" in linea:
                print(f"  {VERDE}{linea_strip}{RESET}")
            elif "FAILED" in linea or "ERROR" in linea or "error" in linea.lower():
                print(f"  {ROJO}{linea_strip}{RESET}")
            elif "WARNING" in linea or "warning" in linea.lower():
                print(f"  {NARANJA}{linea_strip}{RESET}")
            elif linea_strip.startswith("test_") or "::" in linea_strip:
                print(f"  {CYAN}{linea_strip}{RESET}")
            else:
                print(f"  {GRIS}{linea_strip}{RESET}")
    return resultado.returncode, resultado.stdout


# ══════════════════════════════════════════════════════════════════════════════
#  PASOS DE LA DEMO
# ══════════════════════════════════════════════════════════════════════════════

def paso1_workflow_yaml():
    cls(); cabecera()
    separador("PASO 1 · El Workflow de GitHub Actions")

    titulo("Fichero: .github/workflows/ci_cd.yaml")
    print(f"""
  {CYAN}Triggers (cuando se activa){RESET}
    push a develop   ->  Solo CI  (tests + calidad)
    push a master    ->  CI + ML + Docker build/push
    PR a master      ->  CI + ML  (sin Docker)
    cron lunes 2am   ->  ML + monitoreo drift (semanal)

  {CYAN}Jobs definidos{RESET}
    1. ci              Tests pytest + flake8 (siempre)
    2. monitoreo       Detectar drift (solo cron)
    3. entrenar-evaluar  Datos -> Features -> Entrenar -> Gate
    4. despliegue      Build + Push imagen a ghcr.io (solo master)

  {CYAN}Regla clave{RESET}
    El job 4 (Docker) tiene:
      needs: entrenar-evaluar
      if: github.ref == 'refs/heads/master'

    Si evaluar.py hace sys.exit(1) -> job 3 falla
    -> job 4 nunca se ejecuta
    -> Docker NO se reconstruye
    -> modelo rechazado NO llega a produccion
    """)

    separador("Estructura del fichero YAML")
    if WORKFLOW.exists():
        enc = sys.stdout.encoding or "utf-8"
        def _s(t):  # sanear para cp1252
            return t.encode(enc, errors="replace").decode(enc)

        lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
        in_job = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("jobs:"):
                in_job = True
            if not in_job:
                continue
            if stripped.startswith("#"):
                print(f"  {GRIS}{_s(stripped)}{RESET}")
            elif stripped.endswith(":") and not stripped.startswith("-"):
                indent = len(line) - len(line.lstrip())
                if indent <= 4:
                    print(f"  {CYAN}{BOLD}{_s(line.rstrip())}{RESET}")
                elif indent <= 8:
                    print(f"  {NARANJA}{_s(line.rstrip())}{RESET}")
            elif any(k in stripped for k in ["needs:", "if:", "runs-on:", "on:"]):
                print(f"  {VERDE}{_s(line.rstrip())}{RESET}")
        ok("Workflow completo en: .github/workflows/ci_cd.yaml")
    else:
        warn("Fichero de workflow no encontrado.")

    pausa()


def paso2_tests_locales():
    cls(); cabecera()
    separador("PASO 2 · Tests Locales (Job CI de GitHub Actions)")

    titulo("Por que los tests son la primera barrera:")
    print(f"""
  {CYAN}En GH Actions:{RESET}  pytest tests/ -v --tb=short
  {CYAN}Si fallan:{RESET}      el pipeline se detiene — nada mas se ejecuta
  {CYAN}Que cubren:{RESET}
    test_datos.py   -> calidad del dataset, splits, sin nulos
    test_modelo.py  -> modelo carga, predice, metricas minimas
    """)

    # Mostrar los tests disponibles
    for tf in sorted((ROOT / "tests").glob("test_*.py")):
        import ast
        try:
            tree = ast.parse(tf.read_text(encoding="utf-8", errors="replace"))
            funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                     and n.name.startswith("test_")]
            print(f"  {MORADO}{tf.name}{RESET}  ({len(funcs)} tests)")
            for fn in funcs:
                print(f"    {GRIS}  {fn}{RESET}")
        except Exception:
            print(f"  {MORADO}{tf.name}{RESET}")
    print()

    info("Ejecutando: pytest tests/ -v --tb=short")
    print()
    inicio = time.time()
    code, out = ejecutar(f'"{PYTHON}" -m pytest tests/ -v --tb=short')
    duracion = time.time() - inicio

    print()
    if code == 0:
        passed = out.count(" PASSED")
        ok(f"{passed} tests pasados en {duracion:.1f}s")
        ok("Job CI aprobado — pipeline continuaria al siguiente job")
    else:
        failed = out.count(" FAILED")
        err(f"{failed} tests fallidos")
        err("Job CI fallido — pipeline DETENIDO aqui")

    pausa()


def paso3_calidad_codigo():
    cls(); cabecera()
    separador("PASO 3 · Calidad de Codigo (flake8)")

    titulo("Por que la calidad de codigo importa en MLOps:")
    print(f"""
  {CYAN}En GH Actions:{RESET}  flake8 src/ --max-line-length=100
  {CYAN}Que detecta:{RESET}
    E1xx  Indentacion incorrecta
    E2xx  Espacios en blanco
    E3xx  Lineas en blanco
    E7xx  Sentencias incorrectas
    W     Advertencias de estilo
  {CYAN}Por que importa:{RESET}
    Codigo legible = mantenible por todo el equipo
    En ML: los notebooks son exploracion, src/ es produccion
    """)

    info("Ejecutando: flake8 src/ --max-line-length=100 --ignore=E501,W503")
    print()
    code, out = ejecutar(
        f'"{PYTHON}" -m flake8 src/ --max-line-length=100 --ignore=E501,W503,W291,W293,E221,E241,F841'
    )

    print()
    if code == 0:
        ok("Codigo limpio — sin errores de estilo")
        ok("Gate de calidad de codigo superado")
    else:
        n = len([l for l in out.splitlines() if l.strip()])
        warn(f"{n} avisos de estilo encontrados")
        info("En CI/CD se puede configurar como warning (no bloquea) o error (bloquea)")

    pausa()


def paso4_simular_push_develop():
    cls(); cabecera()
    separador("PASO 4 · Simular push a develop")

    titulo("Que ocurre al hacer git push a develop:")
    print(f"""
  {CYAN}Trigger:{RESET}   on: push: branches: [develop]
  {CYAN}Jobs:{RESET}      SOLO el job 'ci'
  {CYAN}Que NO pasa:{RESET}
    - NO se re-entrena el modelo
    - NO se construye Docker
    - Solo se valida que el codigo funciona
  {CYAN}Razon:{RESET}
    develop es la rama de trabajo diario
    Re-entrenar en cada push seria muy costoso
    El modelo nuevo solo se genera al hacer PR/merge a master
    """)

    separador("Ejecutando job CI (tests + flake8)")
    print()

    pasos_ci = [
        ("pytest tests/ -v --tb=short",
         f'"{PYTHON}" -m pytest tests/ -v --tb=short'),
        ("flake8 src/ --max-line-length=100",
         f'"{PYTHON}" -m flake8 src/ --max-line-length=100 --ignore=E501,W503,W291,W293,E221,E241,F841'),
    ]

    todos_ok = True
    for nombre, cmd in pasos_ci:
        info(f"Paso: {nombre}")
        code, out = ejecutar(cmd, mostrar_output=False)
        if code == 0:
            ok(f"Superado")
        else:
            err(f"Fallido — pipeline detenido")
            todos_ok = False
        print()

    separador("Resultado del push a develop")
    if todos_ok:
        print(f"  {VERDE}{BOLD}  PUSH A DEVELOP: OK{RESET}")
        print(f"  {GRIS}  Jobs ejecutados:   ci{RESET}")
        print(f"  {GRIS}  Jobs omitidos:     entrenar-evaluar, despliegue{RESET}")
        print()
        print(f"  {NARANJA}Siguiente paso normal:{RESET} abrir Pull Request a master")
        print(f"  {NARANJA}Eso activara el job entrenar-evaluar.{RESET}")
    else:
        print(f"  {ROJO}{BOLD}  PUSH BLOQUEADO — corrige los tests{RESET}")

    pausa()


def paso5_simular_push_master():
    cls(); cabecera()
    separador("PASO 5 · Simular push a master (pipeline completo)")

    titulo("Que ocurre al hacer merge/push a master:")
    print(f"""
  {CYAN}Jobs en orden:{RESET}
    1. ci              Tests + flake8      (en paralelo, ~30s)
    2. entrenar-evaluar  Pipeline ML         (~2 min en GH)
    3. despliegue      Build + Push Docker  (~5 min en GH)

  {CYAN}Gate obligatorio:{RESET}
    Si RMSE >= 0.5 o R² <= 0.80 -> evaluar.py hace sys.exit(1)
    -> job 2 falla -> job 3 no arranca -> Docker no se actualiza
    """)

    separador("Job 1/3 — CI (tests + calidad)")
    print()

    code_ci, _ = ejecutar(
        f'"{PYTHON}" -m pytest tests/ -v --tb=short', mostrar_output=False
    )
    code_fl, _ = ejecutar(
        f'"{PYTHON}" -m flake8 src/ --max-line-length=100 --ignore=E501,W503,W291,W293,E221,E241,F841',
        mostrar_output=False
    )
    job1_ok = (code_ci == 0 and code_fl == 0)

    color = VERDE if job1_ok else ROJO
    estado = "APROBADO" if job1_ok else "FALLIDO"
    print(f"  {color}{BOLD}  Job ci: {estado}{RESET}")
    if not job1_ok:
        err("Pipeline detenido en CI — jobs 2 y 3 no se ejecutan")
        pausa()
        return

    print()
    separador("Job 2/3 — ML (datos -> features -> entrenar -> gate)")
    print()

    pasos_ml = [
        ("Preparar datos",       f'"{PYTHON}" -m src.data.preparar_datos'),
        ("Ingenieria features",  f'"{PYTHON}" -m src.features.ingenieria_features'),
        ("Entrenar modelo",      f'"{PYTHON}" -m src.models.entrenar'),
        ("Evaluar — gate calidad", f'"{PYTHON}" -m src.models.evaluar'),
    ]

    job2_ok = True
    for nombre, cmd in pasos_ml:
        info(f"Step: {nombre}")
        inicio = time.time()
        code, out = ejecutar(cmd, mostrar_output=False, timeout=180)
        duracion = time.time() - inicio
        if code == 0:
            ok(f"OK  ({duracion:.1f}s)")
        else:
            err(f"FALLIDO ({duracion:.1f}s) — pipeline detenido")
            # Mostrar las ultimas lineas del error
            for linea in out.splitlines()[-5:]:
                if linea.strip():
                    print(f"    {ROJO}{linea.strip()}{RESET}")
            job2_ok = False
            break
        print()

    if job2_ok:
        # Mostrar resultado del gate
        import json as _json
        reporte_path = ROOT / "experiments" / "reporte_evaluacion.json"
        if reporte_path.exists():
            reporte = _json.loads(reporte_path.read_text())
            m = reporte["metricas"]
            print(f"  {VERDE}{BOLD}  Job entrenar-evaluar: APROBADO{RESET}")
            print(f"  {CYAN}  RMSE = {m['rmse']:.4f}  R2 = {m['r2']:.4f}{RESET}")
    else:
        print(f"  {ROJO}{BOLD}  Job entrenar-evaluar: FALLIDO{RESET}")
        err("Job despliegue NO se ejecutara — modelo no aprobado")
        pausa()
        return

    print()
    separador("Job 3/3 — Despliegue (build Docker local)")
    print()

    info("En GitHub Actions: docker build + push a ghcr.io")
    info("En local demo: docker build --no-push")
    print()

    code_docker, out_docker = ejecutar(
        "docker build -t mlops-ciclo-vida-api:demo-ci . --quiet",
        mostrar_output=False,
        timeout=300
    )

    if code_docker == 0:
        ok("Imagen Docker construida correctamente")
        ok("En GH Actions se haria push a ghcr.io con tag latest + SHA")
        print()
        print(f"  {GRIS}  Imagen resultado:  mlops-ciclo-vida-api:demo-ci{RESET}")
        print(f"  {GRIS}  En produccion:     ghcr.io/<owner>/mlops-api-viviendas:latest{RESET}")
    else:
        warn("Build Docker fallo (puede ser que Docker Desktop no este activo)")
        warn("En GH Actions esto bloquearia el despliegue")

    print()
    separador("Resumen del pipeline master")
    print(f"  {VERDE}OK{RESET}  Job 1  ci               (tests + flake8)")
    print(f"  {VERDE}OK{RESET}  Job 2  entrenar-evaluar  (pipeline ML + gate)")
    estado_d = f"{VERDE}OK{RESET}" if code_docker == 0 else f"{NARANJA}**{RESET}"
    print(f"  {estado_d}  Job 3  despliegue        (Docker build/push)")
    print()
    print(f"  {NARANJA}Modelo en produccion disponible via:{RESET}")
    print(f"  {NARANJA}  docker pull ghcr.io/<owner>/mlops-api-viviendas:latest{RESET}")

    pausa()


def paso6_flujo_completo():
    cls(); cabecera()
    separador("PASO 6 · Flujo Completo del Ciclo de Vida")

    titulo("Del codigo al modelo en produccion:")
    print(f"""
  {BOLD}DESARROLLADOR{RESET}
       |
       |  git push origin develop
       v
  {CYAN}[ develop ] -----------------------------------------{RESET}
       |
       |  GitHub Actions activa:
       |
       +--> {VERDE}Job: ci{RESET}
       |      pytest tests/         <- test_datos, test_modelo
       |      flake8 src/           <- calidad de codigo
       |
       |  Si falla -> notificacion al desarrollador
       |  Si pasa  -> PR a master disponible
       |
  {MORADO}[ Pull Request develop -> master ]{RESET}
       |
       +--> {VERDE}Job: ci{RESET}             (mismo que develop)
       +--> {VERDE}Job: entrenar-evaluar{RESET}
              preparar_datos.py
              ingenieria_features.py
              entrenar.py
              evaluar.py  <- RMSE < 0.5 AND R2 > 0.80
                          <- sys.exit(1) si NO aprueba

       Reviewer ve el reporte de evaluacion en GH Actions
       Si todo OK -> aprueba el PR
       |
  {NARANJA}[ master ] -------------------------------------------{RESET}
       |
       |  git merge (push a master)
       v
       +--> {VERDE}Job: ci{RESET}
       +--> {VERDE}Job: entrenar-evaluar{RESET}
       +--> {VERDE}Job: despliegue{RESET}
              docker build
              docker push ghcr.io/<owner>/mlops-api-viviendas:latest
              docker push ghcr.io/<owner>/mlops-api-viviendas:<sha>
       |
       v
  {VERDE}{BOLD}[ PRODUCCION ]{RESET}
       docker pull ghcr.io/.../mlops-api-viviendas:latest
       docker compose up -d
       http://servidor:8000/v1/predecir
    """)

    separador("Trigger automatico semanal")
    print(f"""
  {CYAN}cron: "0 2 * * 1"  (lunes a las 2am UTC){RESET}

  +--> Job: ci
  +--> Job: monitoreo
  |      monitor.py  -> calcula PSI por feature
  |      Si drift detectado -> activa entrenar-evaluar
  +--> Job: entrenar-evaluar  (si hay drift)
  +--> Job: despliegue        (si modelo aprobado)

  {NARANJA}El sistema se re-entrena solo cuando los datos cambian.{RESET}
  {NARANJA}Sin intervencion humana si el modelo pasa el gate.{RESET}
    """)

    separador("Que aporta GH Actions vs ejecutar manualmente")
    ventajas = [
        ("Reproducibilidad",  "mismo entorno en cada ejecucion (ubuntu-latest)"),
        ("Trazabilidad",      "cada run vinculado a un commit SHA"),
        ("Automatizacion",    "re-entrenamiento sin intervencion humana"),
        ("Gates de calidad",  "imposible desplegar un modelo que no aprueba"),
        ("Auditoria",         "log completo de cada pipeline en GitHub"),
        ("Artefactos",        "modelo.pkl guardado 30 dias por commit"),
    ]
    for nombre, desc in ventajas:
        print(f"  {VERDE}OK{RESET}  {CYAN}{nombre:<18}{RESET}  {desc}")

    pausa()


def paso7_demo_completa():
    for paso in [paso1_workflow_yaml, paso2_tests_locales, paso3_calidad_codigo,
                 paso4_simular_push_develop, paso5_simular_push_master,
                 paso6_flujo_completo]:
        paso()


# ══════════════════════════════════════════════════════════════════════════════
#  MENU PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def menu():
    opciones = {
        "1": ("Ver el workflow YAML           (triggers, jobs, condiciones)",  paso1_workflow_yaml),
        "2": ("Tests locales                  (pytest — job CI)",               paso2_tests_locales),
        "3": ("Calidad de codigo              (flake8 — job CI)",               paso3_calidad_codigo),
        "4": ("Simular push a develop         (solo CI, sin ML)",               paso4_simular_push_develop),
        "5": ("Simular push a master          (CI + ML + Docker)",              paso5_simular_push_master),
        "6": ("Flujo completo explicado       (diagrama develop->master->prod)", paso6_flujo_completo),
        "7": (f"{BOLD}Demo completa (pasos 1 a 6){RESET}",                     paso7_demo_completa),
        "0": ("Salir",                                                           None),
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
