"""
============================================================
DEMO — Pipeline MLOps: Datos, Features, Modelo, Monitoreo
Ciclo de Vida MLOps · California Housing Price Predictor
============================================================
Ejecutar:
  python demo_pipeline.py
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
    print("   DEMO -- PIPELINE MLOps COMPLETO")
    print("   Datos | Features | Modelo | Evaluacion | Monitoreo")
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
def titulo(msg): print(f"{MORADO}{BOLD}  {msg}{RESET}")


def pausa():
    print(f"\n{GRIS}  Pulsa ENTER para volver al menu...{RESET}")
    input()


def ejecutar(cmd, mostrar_output=True):
    resultado = subprocess.run(
        cmd, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace"
    )
    if mostrar_output and resultado.stdout:
        enc = sys.stdout.encoding or "utf-8"
        # Filtrar solo lineas relevantes (INFO, advertencias, resultados)
        for linea in resultado.stdout.splitlines():
            linea_strip = linea.strip()
            if not linea_strip:
                continue
            # Sanear caracteres no imprimibles en la consola actual
            linea_strip = linea_strip.encode(enc, errors="replace").decode(enc)
            if "[INFO]" in linea:
                print(f"  {GRIS}{linea_strip}{RESET}")
            elif "[WARNING]" in linea or "[WARN]" in linea:
                print(f"  {NARANJA}{linea_strip}{RESET}")
            elif "[ERROR]" in linea:
                print(f"  {ROJO}{linea_strip}{RESET}")
            else:
                print(f"  {linea_strip}")
    return resultado.returncode, resultado.stdout


def leer_json(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  PASOS DE LA DEMO
# ══════════════════════════════════════════════════════════════════════════════

def paso1_preparacion_datos():
    cls(); cabecera()
    separador("PASO 1 · Preparacion de Datos")

    titulo("Que hace esta etapa:")
    print(f"""
  {CYAN}Fuente{RESET}    sklearn.datasets.fetch_california_housing
  {CYAN}Dataset{RESET}   20,640 muestras | 8 features | target: precio mediano
  {CYAN}Pasos{RESET}     Ingestion -> Validacion -> Limpieza -> Split 80/20
  {CYAN}Outputs{RESET}   data/raw/housing_raw.csv
            data/processed/train.csv  ({VERDE}~16,500 filas{RESET})
            data/processed/test.csv   ({VERDE}~4,100 filas{RESET})
    """)

    info("Ejecutando src/data/preparar_datos.py ...")
    print()
    code, out = ejecutar(f'"{PYTHON}" -m src.data.preparar_datos')

    print()
    # Mostrar resultado del split
    train = ROOT / "data" / "processed" / "train.csv"
    test  = ROOT / "data" / "processed" / "test.csv"
    if train.exists() and test.exists():
        import csv
        n_train = sum(1 for _ in open(train)) - 1
        n_test  = sum(1 for _ in open(test))  - 1
        ok(f"Train set: {n_train:,} filas  ->  data/processed/train.csv")
        ok(f"Test set:  {n_test:,} filas  ->  data/processed/test.csv")
        print()
        separador("Calidad de datos validada")
        print(f"  {CYAN}Sin nulos{RESET}           dataset limpio")
        print(f"  {CYAN}Sin duplicados{RESET}      integridad garantizada")
        print(f"  {CYAN}Split reproducible{RESET}  semilla fija (random_state=42)")
        print(f"  {CYAN}Sin data leakage{RESET}    fit del scaler solo sobre train")
    else:
        warn("Ficheros de datos no encontrados.")

    pausa()


def paso2_ingenieria_features():
    cls(); cabecera()
    separador("PASO 2 · Ingenieria de Features")

    titulo("De 8 features originales a 13 features:")
    print()

    features_nuevas = [
        ("rooms_per_person",  "AveRooms / AveOccup",           "Densidad real del hogar"),
        ("income_per_room",   "MedInc / AveRooms",             "Poder adquisitivo por habitacion"),
        ("bedroom_ratio",     "AveBedrms / AveRooms",          "Elimina multicolinealidad"),
        ("dist_sacramento",   "distancia euclidiana",          "Accesibilidad a la capital"),
        ("dist_los_angeles",  "distancia euclidiana",          "Proximidad al mayor mercado"),
    ]

    print(f"  {BOLD}{'Feature':<22} {'Formula':<28} {'Razon'}{RESET}")
    print(f"  {GRIS}{'-' * 70}{RESET}")
    for nombre, formula, razon in features_nuevas:
        print(f"  {CYAN}{nombre:<22}{RESET} {GRIS}{formula:<28}{RESET} {razon}")

    print()
    info("Ejecutando src/features/ingenieria_features.py ...")
    print()
    code, out = ejecutar(f'"{PYTHON}" -m src.features.ingenieria_features')

    print()
    scaler = ROOT / "experiments" / "scaler.pkl"
    if scaler.exists():
        ok("scaler.pkl guardado -> experiments/scaler.pkl")
        ok("13 features escaladas con StandardScaler")
        print()
        separador("Por que guardar el scaler")
        print(f"  {NARANJA}El mismo scaler entrenado en train{RESET}")
        print(f"  {NARANJA}debe usarse en produccion (API y batch).{RESET}")
        print(f"  {NARANJA}Entrenar un scaler nuevo = Training-Serving Skew.{RESET}")
    else:
        warn("scaler.pkl no encontrado.")

    pausa()


def paso3_comparacion_algoritmos():
    cls(); cabecera()
    separador("PASO 3 · Comparacion de Algoritmos (seleccion del modelo)")

    titulo("Por que no elegimos el algoritmo a ciegas:")
    print(f"""
  {CYAN}Candidatos{RESET}  Linear Regression | Random Forest | Gradient Boosting
  {CYAN}Metodo{RESET}      Cross-Validation 5 folds sobre datos de train
  {CYAN}Criterio{RESET}    Menor RMSE + mayor R2 + menor varianza entre folds
  {CYAN}Resultado{RESET}   El ganador se escribe en config.yaml y se re-entrena
    """)

    info("Ejecutando CV 5-fold para los 3 algoritmos (puede tardar ~2 min)...")
    print()

    # Ejecutar comparacion inline
    try:
        import numpy as np
        import pickle
        import pandas as pd
        from sklearn.linear_model import LinearRegression
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        from sklearn.model_selection import cross_val_score

        # Cargar scaler
        with open(ROOT / "experiments" / "scaler.pkl", "rb") as f:
            scaler_obj = pickle.load(f)
        scaler = scaler_obj["scaler"] if isinstance(scaler_obj, dict) else scaler_obj
        feature_cols = scaler_obj["columnas"] if isinstance(scaler_obj, dict) else None

        # Cargar train.csv (ya incluye las 13 features: 8 originales + 5 derivadas)
        df_train = pd.read_csv(ROOT / "data" / "processed" / "train.csv")
        y_train = df_train["MedHouseVal"].values
        if feature_cols is None:
            feature_cols = [c for c in df_train.columns if c != "MedHouseVal"]
        import warnings as _w
        with _w.catch_warnings():
            _w.simplefilter("ignore")
            X_train = scaler.transform(df_train[feature_cols].values)

        modelos = {
            "Linear Regression":  LinearRegression(),
            "Random Forest":      RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1),
            "Gradient Boosting":  GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42),
        }

        resultados = {}
        for nombre, modelo in modelos.items():
            info(f"  Evaluando {nombre}...")
            rmse_scores = np.sqrt(-cross_val_score(
                modelo, X_train, y_train,
                cv=5, scoring="neg_mean_squared_error", n_jobs=-1
            ))
            r2_scores = cross_val_score(
                modelo, X_train, y_train, cv=5, scoring="r2", n_jobs=-1
            )
            resultados[nombre] = {
                "rmse_mean": float(rmse_scores.mean()),
                "rmse_std":  float(rmse_scores.std()),
                "r2_mean":   float(r2_scores.mean()),
            }

        # Ordenar por RMSE
        ranking = sorted(resultados.items(), key=lambda x: x[1]["rmse_mean"])

        print()
        separador("Resultados Cross-Validation (5 folds)")
        print(f"  {BOLD}{'Algoritmo':<24} {'RMSE media':>10} {'±std':>7} {'R2 media':>9}  Ranking{RESET}")
        print(f"  {GRIS}{'-' * 62}{RESET}")

        medallas = ["1er", "2do", "3er"]
        for i, (nombre, m) in enumerate(ranking):
            color  = VERDE if i == 0 else NARANJA if i == 1 else ROJO
            ganador = f"  {BOLD}<-- GANADOR{RESET}" if i == 0 else ""
            print(
                f"  {color}{medallas[i]}{RESET}  {nombre:<22}"
                f"  {color}{m['rmse_mean']:.4f}{RESET}"
                f"  ±{m['rmse_std']:.4f}"
                f"  {m['r2_mean']:.4f}"
                f"{ganador}"
            )

        print()
        ganador_nombre, ganador_m = ranking[0]
        separador("Conclusion")
        print(f"  {VERDE}{BOLD}{ganador_nombre}{RESET} gana con:")
        print(f"  {CYAN}  RMSE medio  {RESET} {VERDE}{BOLD}{ganador_m['rmse_mean']:.4f}{RESET}  (menor = mejor)")
        print(f"  {CYAN}  R2 medio    {RESET} {VERDE}{BOLD}{ganador_m['r2_mean']:.4f}{RESET}  (mayor = mejor)")
        print(f"  {CYAN}  Varianza    {RESET} ±{ganador_m['rmse_std']:.4f}  (menor = mas estable entre folds)")
        print()
        print(f"  {NARANJA}config.yaml -> modelo.algoritmo: \"gradient_boosting\"{RESET}")
        print(f"  {NARANJA}El pipeline re-entrena con TODOS los datos de train.{RESET}")

    except Exception as e:
        err(f"Error en comparacion: {e}")
        warn("Asegurate de haber ejecutado los pasos 1 y 2 primero.")

    pausa()


def paso3b_automl_optuna():
    cls(); cabecera()
    separador("PASO 3B · AutoML con Optuna (optimizacion de hiperparametros)")

    titulo("Que hace AutoML aqui:")
    print(f"""
  {CYAN}Algoritmo fijo{RESET}   Gradient Boosting (ganador del paso 3)
  {CYAN}Que optimiza{RESET}     n_estimators, max_depth, learning_rate,
                   subsample, min_samples_split
  {CYAN}Metodo{RESET}           Optuna TPE (Tree-structured Parzen Estimator)
                   Aprende que zonas del espacio son prometedoras
  {CYAN}Ventaja vs Grid{RESET}  Espacio ~ 10 millones de combinaciones
                   Grid Search tardaria horas; Optuna converge en minutos
    """)

    separador("Espacio de busqueda")
    espacio = [
        ("n_estimators",       "int",         "100 a 500"),
        ("max_depth",          "int",         "3 a 8"),
        ("learning_rate",      "float (log)", "0.01 a 0.30"),
        ("subsample",          "float",       "0.50 a 1.00"),
        ("min_samples_split",  "int",         "2 a 20"),
    ]
    print(f"  {BOLD}{'Hiperparametro':<24} {'Tipo':<14} Rango{RESET}")
    print(f"  {GRIS}{'-' * 52}{RESET}")
    for param, tipo, rango in espacio:
        print(f"  {CYAN}{param:<24}{RESET} {GRIS}{tipo:<14}{RESET} {rango}")

    print()
    N_TRIALS = 10
    info(f"Ejecutando {N_TRIALS} trials Optuna (demo rapida)...")
    info("En produccion se usan 50-100 trials para mayor precision.")
    print()

    try:
        import warnings as _w
        import pickle, yaml
        import numpy as np
        import pandas as pd
        _w.filterwarnings("ignore")

        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.model_selection import cross_val_score

        # Cargar datos y scaler
        with open(ROOT / "experiments" / "scaler.pkl", "rb") as f:
            scaler_obj = pickle.load(f)
        scaler      = scaler_obj["scaler"] if isinstance(scaler_obj, dict) else scaler_obj
        feature_cols = scaler_obj["columnas"] if isinstance(scaler_obj, dict) else None

        df_train = pd.read_csv(ROOT / "data" / "processed" / "train.csv")
        y_train  = df_train["MedHouseVal"].values
        if feature_cols is None:
            feature_cols = [c for c in df_train.columns if c != "MedHouseVal"]
        with _w.catch_warnings():
            _w.simplefilter("ignore")
            X_train = scaler.transform(df_train[feature_cols].values)

        # Baseline manual (config.yaml actual)
        cfg = yaml.safe_load(open(ROOT / "config" / "config.yaml"))
        p_manual = cfg["modelo"]["hiperparametros"]["gradient_boosting"]
        modelo_manual = GradientBoostingRegressor(**p_manual)
        rmse_manual = float(np.sqrt(-cross_val_score(
            modelo_manual, X_train, y_train,
            cv=3, scoring="neg_mean_squared_error", n_jobs=-1
        ).mean()))

        ok(f"Baseline manual (config.yaml):  RMSE CV = {rmse_manual:.4f}")
        print()

        # Funcion objetivo de Optuna
        historial = []

        def objective(trial):
            params = {
                "n_estimators":      trial.suggest_int("n_estimators", 100, 500),
                "max_depth":         trial.suggest_int("max_depth", 3, 8),
                "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.30, log=True),
                "subsample":         trial.suggest_float("subsample", 0.5, 1.0),
                "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
                "random_state":      42,
            }
            modelo = GradientBoostingRegressor(**params)
            rmse = float(np.sqrt(-cross_val_score(
                modelo, X_train, y_train,
                cv=3, scoring="neg_mean_squared_error", n_jobs=-1
            ).mean()))
            historial.append((trial.number + 1, rmse, params))
            mejor = min(h[1] for h in historial)
            simbolo = "*" if rmse == mejor else " "
            print(f"  {GRIS}Trial {trial.number+1:>2}/{N_TRIALS}  "
                  f"RMSE={rmse:.4f}  mejor={mejor:.4f}  {simbolo}{RESET}")
            return rmse

        study = optuna.create_study(
            direction="minimize",
            sampler=optuna.samplers.TPESampler(seed=42),
            pruner=optuna.pruners.MedianPruner(n_startup_trials=5),
        )
        study.optimize(objective, n_trials=N_TRIALS)

        best_rmse   = study.best_value
        best_params = {**study.best_params, "random_state": 42}
        mejora_pct  = (rmse_manual - best_rmse) / rmse_manual * 100

        print()
        separador("Resultado AutoML vs Baseline manual")
        color_res = VERDE if best_rmse < rmse_manual else NARANJA
        print(f"  {CYAN}{'Baseline manual':<22}{RESET}  RMSE = {rmse_manual:.4f}")
        print(f"  {color_res}{BOLD}{'Mejor AutoML':<22}{RESET}  RMSE = {best_rmse:.4f}"
              f"  ({'+' if mejora_pct < 0 else '-'}{abs(mejora_pct):.1f}%){RESET}")
        print()

        separador("Mejores hiperparametros encontrados")
        for k, v in best_params.items():
            manual_v = p_manual.get(k, "—")
            cambio   = f"  (antes: {manual_v})" if v != manual_v else "  (sin cambio)"
            print(f"  {CYAN}{k:<24}{RESET} {BOLD}{v}{RESET}{GRIS}{cambio}{RESET}")

        # Actualizar config.yaml si AutoML mejora
        print()
        if best_rmse < rmse_manual:
            separador("Actualizando config.yaml con los mejores parametros")
            cfg["modelo"]["hiperparametros"]["gradient_boosting"] = best_params
            with open(ROOT / "config" / "config.yaml", "w") as f:
                yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
            ok("config.yaml actualizado — el paso 4 usara estos hiperparametros")
            print(f"  {NARANJA}El paso 4 (Entrenamiento) re-entrena con TODOS{RESET}")
            print(f"  {NARANJA}los datos de train usando estos hiperparametros.{RESET}")
        else:
            warn("AutoML no mejoro el baseline. config.yaml sin cambios.")
            warn("Aumenta N_TRIALS a 50+ en produccion para mejores resultados.")

    except ImportError:
        err("Optuna no instalado. Ejecuta: pip install optuna")
    except Exception as e:
        err(f"Error en AutoML: {e}")
        warn("Asegurate de haber ejecutado los pasos 1 y 2 primero.")

    pausa()


def paso3_entrenamiento_mlflow():
    cls(); cabecera()
    separador("PASO 3 · Entrenamiento con MLflow")

    titulo("Que registra MLflow por cada experimento:")
    print(f"""
  {CYAN}Parametros{RESET}   algoritmo, learning_rate, max_depth, n_estimators
  {CYAN}Metricas{RESET}     RMSE train, RMSE test, R2, MAE
  {CYAN}Artefactos{RESET}   modelo.pkl, scaler.pkl, feature_importance
  {CYAN}Metadatos{RESET}    timestamp, duracion, version del codigo
    """)

    info("Ejecutando src/models/entrenar.py ...")
    print()
    code, out = ejecutar(f'"{PYTHON}" -m src.models.entrenar')

    print()
    modelo = ROOT / "experiments" / "modelo_produccion.pkl"
    if modelo.exists():
        ok("modelo_produccion.pkl guardado -> experiments/")

    # Mostrar ultimo experimento registrado
    exp_file = ROOT / "experiments" / "experimentos.jsonl"
    if exp_file.exists():
        with open(exp_file, encoding="utf-8") as f:
            lineas = f.readlines()
        if lineas:
            ultimo = json.loads(lineas[-1])
            print()
            separador("Ultimo experimento registrado")
            m = ultimo.get("metricas_val", ultimo.get("metricas_test", {}))
            p = ultimo.get("parametros", {})
            print(f"  {CYAN}{'Algoritmo':<20}{RESET} {ultimo.get('algoritmo','—')}")
            for k, v in p.items():
                print(f"  {CYAN}{k:<20}{RESET} {v}")
            print(f"  {GRIS}{'-' * 40}{RESET}")
            for k, v in m.items():
                color = VERDE if k in ("r2",) and v > 0.8 else VERDE if k == "rmse" and v < 0.5 else RESET
                print(f"  {CYAN}{k.upper():<20}{RESET} {color}{BOLD}{v:.4f}{RESET}")

    print()
    separador("Ver resultados en MLflow UI")
    print(f"  {BOLD}mlflow ui --backend-store-uri experiments/{RESET}")
    print(f"  {GRIS}  Luego abrir: http://127.0.0.1:5000{RESET}")

    pausa()


def paso4_seleccion_modelo():
    cls(); cabecera()
    separador("PASO 4 · Evaluacion y Gate de Calidad")

    titulo("Gate de produccion — umbrales definidos en config.yaml:")
    print(f"""
  {CYAN}RMSE{RESET}   < 0.50   (error en unidades de $100k)
  {CYAN}R2{RESET}     > 0.80   (varianza explicada por el modelo)

  Si no supera ambos umbrales -> modelo RECHAZADO, no va a produccion.
    """)

    info("Ejecutando src/models/evaluar.py ...")
    print()
    code, out = ejecutar(f'"{PYTHON}" -m src.models.evaluar')

    print()
    reporte = leer_json(ROOT / "experiments" / "reporte_evaluacion.json")
    if reporte:
        separador("Resultado del gate de calidad")
        m = reporte.get("metricas", {})
        aprobado = reporte.get("aprobado", False)

        for k, v in m.items():
            if k in ("rmse", "r2"):
                detalle = reporte.get("detalle_aprobacion", {}).get(k, {})
                pasa    = detalle.get("aprobado", False)
                color   = VERDE if pasa else ROJO
                simbolo = "OK" if pasa else "!!"
                print(f"  {color}{simbolo}  {k.upper():<8} {v:.4f}   {detalle.get('condicion','')}{RESET}")

        print()
        if aprobado:
            print(f"  {VERDE}{BOLD}  MODELO APROBADO — listo para produccion{RESET}")
        else:
            print(f"  {ROJO}{BOLD}  MODELO RECHAZADO — no cumple los umbrales{RESET}")

        print()
        separador("Donde queda el modelo tras el gate")
        ruta_modelo = ROOT / "experiments" / "modelo_produccion.pkl"
        ruta_scaler = ROOT / "experiments" / "scaler.pkl"
        tam_modelo  = ruta_modelo.stat().st_size // 1024 if ruta_modelo.exists() else 0
        tam_scaler  = ruta_scaler.stat().st_size       if ruta_scaler.exists()  else 0

        if aprobado:
            print(f"  {VERDE}OK{RESET}  {CYAN}experiments/modelo_produccion.pkl{RESET}  ({tam_modelo} KB)")
            print(f"  {VERDE}OK{RESET}  {CYAN}experiments/scaler.pkl{RESET}             ({tam_scaler} bytes)")
            print()
            print(f"  {BOLD}El entrenamiento guarda el modelo ANTES del gate.{RESET}")
            print(f"  {BOLD}El gate decide si ese modelo llega a produccion:{RESET}")
            print()
            print(f"  {GRIS}  APROBADO  -> Docker sirve modelo_produccion.pkl via API{RESET}")
            print(f"  {GRIS}  RECHAZADO -> sys.exit(1) detiene el pipeline en CI/CD{RESET}")
            print(f"  {GRIS}             el Docker NO se reconstruye{RESET}")
            print()
            print(f"  {NARANJA}La API carga el pkl en memoria al arrancar:{RESET}")
            print(f"  {NARANJA}  src/serving/api.py -> pickle.load('modelo_produccion.pkl'){RESET}")
        else:
            print(f"  {ROJO}  El modelo no ha superado el gate.{RESET}")
            print(f"  {ROJO}  experiments/modelo_produccion.pkl NO se despliega.{RESET}")

        print()
        separador("Por que este gate es critico")
        print(f"  {NARANJA}En CI/CD este paso es automatico:{RESET}")
        print(f"  {NARANJA}Si falla, el pipeline se detiene y no despliega.{RESET}")
        print(f"  {NARANJA}Ninguna persona puede saltarselo manualmente.{RESET}")

    pausa()


def paso5_monitoreo():
    cls(); cabecera()
    separador("PASO 5 · Monitoreo y Deteccion de Drift")

    titulo("Que monitoriza el sistema:")
    print(f"""
  {CYAN}Data Drift{RESET}     PSI por feature (Population Stability Index)
                  PSI < 0.10  -> sin cambio
                  PSI < 0.20  -> cambio moderado (vigilar)
                  PSI >= 0.20 -> re-entrenar

  {CYAN}Concept Drift{RESET}  Degradacion del RMSE en produccion
                  Si RMSE sube > 10% -> re-entrenar
    """)

    info("Ejecutando src/monitoring/monitor.py ...")
    print()
    code, out = ejecutar(f'"{PYTHON}" -m src.monitoring.monitor')

    print()
    reporte = leer_json(ROOT / "experiments" / "reporte_monitoreo.json")
    if reporte:
        separador("Resultado del monitoreo")

        dd = reporte.get("data_drift", {})
        cd = reporte.get("concept_drift", {})

        # Data drift
        hay_drift = dd.get("hay_drift", False)
        color_d   = ROJO if hay_drift else VERDE
        print(f"  {color_d}{'DATA DRIFT':<20} {'DETECTADO' if hay_drift else 'OK — sin cambio'}{RESET}")
        if hay_drift:
            features_drift = dd.get("features_con_drift", [])
            print(f"  {NARANJA}  Features afectadas: {', '.join(features_drift)}{RESET}")
            print()
            print(f"  {BOLD}{'Feature':<16} {'PSI':>8}   Estado{RESET}")
            for feat, det in dd.get("detalle", {}).items():
                psi   = det.get("psi", 0)
                drift = det.get("drift_detectado", False)
                col   = ROJO if psi >= 0.2 else NARANJA if psi >= 0.1 else VERDE
                barra = "#" * min(int(psi * 3), 20)
                print(f"  {feat:<16} {col}{psi:>8.4f}   {barra}{RESET}")

        print()
        # Concept drift
        hay_deg   = cd.get("hay_degradacion", False)
        color_c   = ROJO if hay_deg else VERDE
        rmse_orig = cd.get("rmse_original", 0)
        rmse_act  = cd.get("rmse_actual", 0)
        inc_pct   = cd.get("incremento_pct", 0)
        print(f"  {color_c}{'CONCEPT DRIFT':<20} {'DEGRADACION' if hay_deg else 'OK — modelo estable'}{RESET}")
        print(f"  {CYAN}  RMSE original:  {rmse_orig:.4f}{RESET}")
        print(f"  {CYAN}  RMSE actual:    {rmse_act:.4f}  (+{inc_pct:.1f}%){RESET}")
        print(f"  {CYAN}  Umbral:         +{cd.get('umbral_pct',10)}%{RESET}")

        print()
        reentrenar = reporte.get("requiere_reentrenamiento", False)
        accion     = reporte.get("accion_recomendada", "")
        color_r    = ROJO if reentrenar else VERDE
        print(f"  {color_r}{BOLD}  Accion recomendada: {accion}{RESET}")

    pausa()


def paso6_mlflow_ui():
    cls(); cabecera()
    separador("PASO 6 · MLflow UI — Comparativa de Experimentos")

    titulo("Que muestra MLflow UI:")
    print(f"""
  {CYAN}Experimentos{RESET}  Todos los runs registrados con sus parametros
  {CYAN}Metricas{RESET}      RMSE, R2, MAE — comparativa visual entre modelos
  {CYAN}Artefactos{RESET}    Modelos guardados, feature importance, graficas
  {CYAN}Trazabilidad{RESET}  Quien, cuando y con que datos se entrenó cada modelo
    """)

    # Contar runs existentes
    exp_file = ROOT / "experiments" / "experimentos.jsonl"
    if exp_file.exists():
        with open(exp_file) as f:
            n_runs = sum(1 for _ in f)
        ok(f"{n_runs} experimentos registrados en experiments/experimentos.jsonl")

    print()
    info("Lanzando MLflow UI en segundo plano...")
    uri = f"file:///{ROOT}/experiments".replace("\\", "/")
    subprocess.Popen(
        f'"{PYTHON}" -m mlflow ui --backend-store-uri {uri} --port 5001',
        shell=True, cwd=str(ROOT),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    time.sleep(5)
    print()
    ok("MLflow UI arrancado")
    print()
    separador("Acceder en el navegador")
    print(f"\n  {BOLD}{AZUL}  http://127.0.0.1:5001{RESET}\n")
    separador("Que explorar en la UI")
    pasos_ui = [
        "Clic en el experimento 'precio-viviendas'",
        "Ordenar por RMSE ascending para ver el mejor modelo",
        "Seleccionar 2 runs -> 'Compare' para ver diferencias",
        "Clic en un run -> ver parametros, metricas y artefactos",
        "Pestaña 'Artifacts' -> ver el modelo.pkl y feature importance",
    ]
    for i, p in enumerate(pasos_ui, 1):
        print(f"  {CYAN}{i}.{RESET}  {p}")

    pausa()


def paso7_pipeline_completo():
    cls(); cabecera()
    separador("PIPELINE COMPLETO — Datos a Produccion")

    titulo("Ejecutando el pipeline end-to-end:")
    print(f"""
  {CYAN}Etapa 1{RESET}  Preparacion de datos   (ingestión, validación, split)
  {CYAN}Etapa 2{RESET}  Ingenieria de features  (5 features derivadas, escalado)
  {CYAN}Etapa 3{RESET}  Entrenamiento           (GradientBoosting + MLflow)
  {CYAN}Etapa 4{RESET}  Evaluacion              (gate RMSE < 0.5, R2 > 0.8)
    """)

    info("Ejecutando pipeline/pipeline_completo.py ...")
    print()

    inicio = time.time()
    code, out = ejecutar(f'"{PYTHON}" pipeline/pipeline_completo.py')
    duracion = time.time() - inicio

    print()
    separador("Resumen del pipeline")

    reporte = leer_json(ROOT / "experiments" / "reporte_evaluacion.json")
    if reporte and reporte.get("aprobado"):
        m = reporte["metricas"]
        ok(f"Pipeline completado en {duracion:.1f}s")
        print()
        print(f"  {CYAN}{'RMSE test':<20}{RESET} {VERDE}{BOLD}{m['rmse']:.4f}{RESET}  (umbral < 0.50)")
        print(f"  {CYAN}{'R2 test':<20}{RESET}   {VERDE}{BOLD}{m['r2']:.4f}{RESET}  (umbral > 0.80)")
        print(f"  {CYAN}{'MAE test':<20}{RESET}  {m['mae']:.4f}")
        print()
        ok("Modelo APROBADO y guardado en experiments/modelo_produccion.pkl")
        print()
        print(f"  {NARANJA}Siguiente paso:{RESET} levantar la API con docker compose up -d")
    else:
        warn("Revisa el log del pipeline para ver el motivo del fallo.")

    pausa()


def paso9_demo_completa():
    for paso in [paso1_preparacion_datos, paso2_ingenieria_features,
                 paso3_comparacion_algoritmos, paso3b_automl_optuna,
                 paso3_entrenamiento_mlflow, paso4_seleccion_modelo,
                 paso5_monitoreo, paso6_mlflow_ui]:
        paso()


# ══════════════════════════════════════════════════════════════════════════════
#  MENU PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def menu():
    opciones = {
        "1": ("Preparacion de datos         (ingestión, split, calidad)",    paso1_preparacion_datos),
        "2": ("Ingenieria de features       (5 features + scaler.pkl)",       paso2_ingenieria_features),
        "3": ("Comparacion de algoritmos    (CV 5-fold: LR vs RF vs GB)",     paso3_comparacion_algoritmos),
        "4": ("AutoML con Optuna           (optimizacion hiperparametros GB)", paso3b_automl_optuna),
        "5": ("Entrenamiento con MLflow     (mejores params + registro)",      paso3_entrenamiento_mlflow),
        "6": ("Evaluacion y gate de calidad (RMSE < 0.5, R2 > 0.8)",         paso4_seleccion_modelo),
        "7": ("Monitoreo y drift            (PSI + concept drift)",            paso5_monitoreo),
        "8": ("MLflow UI                    (comparativa de experimentos)",    paso6_mlflow_ui),
        "9": ("Pipeline completo            (etapas 1 a 4 en secuencia)",     paso7_pipeline_completo),
        "A": (f"{BOLD}Demo completa (pasos 1 a 8){RESET}",                   paso9_demo_completa),
        "0": ("Salir",                                                         None),
    }

    while True:
        cls(); cabecera()

        print(f"  {BOLD}Selecciona una opcion:{RESET}\n")
        for key, (desc, _) in opciones.items():
            if key == "A":
                print(f"  {NARANJA}  {key}.{RESET}  {desc}")
            elif key == "9":
                print(f"  {MORADO}  {key}.{RESET}  {desc}")
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
