"""
============================================================
ETAPA 4: ENTRENAMIENTO DEL MODELO
============================================================
Responsabilidades:
  - Entrenar el modelo con los parámetros definidos en config
  - Registrar el experimento (parámetros, métricas, artefactos)
  - Guardar el modelo entrenado

Por qué importa el tracking en MLOps:
  - Permite comparar experimentos y saber qué cambios mejoran el modelo
  - Da trazabilidad: ¿con qué datos y parámetros se entrenó este modelo?
  - MLflow es la herramienta estándar para esto (también existen W&B, Comet, etc.)

Nota: Este ejemplo usa MLflow de forma opcional (si no está instalado,
      se guarda el experimento en un JSON local como alternativa).
============================================================
"""

import sys
import json
import pickle
import logging
import numpy as np
import pandas as pd
import yaml
from datetime import datetime
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def cargar_config() -> dict:
    with open(ROOT / "config" / "config.yaml") as f:
        return yaml.safe_load(f)


# ---- SELECCIÓN DE ALGORITMO ----

def obtener_modelo(cfg: dict):
    """
    Instancia el modelo según la configuración.
    Cambiar el algoritmo en config.yaml cambia el modelo sin tocar código.
    """
    algoritmo = cfg["modelo"]["algoritmo"]
    params = cfg["modelo"]["hiperparametros"].get(algoritmo, {})

    constructores = {
        "random_forest": lambda p: RandomForestRegressor(**p),
        "gradient_boosting": lambda p: GradientBoostingRegressor(**p),
        "linear_regression": lambda p: LinearRegression(**{
            k: v for k, v in p.items()
            if k in LinearRegression().get_params()
        })
    }

    if algoritmo not in constructores:
        raise ValueError(f"Algoritmo desconocido: '{algoritmo}'. "
                         f"Opciones: {list(constructores.keys())}")

    log.info("  Algoritmo: %s | Parámetros: %s", algoritmo, params)
    return constructores[algoritmo](params)


# ---- CÁLCULO DE MÉTRICAS ----

def calcular_metricas(y_real: np.ndarray, y_pred: np.ndarray) -> dict:
    """Calcula las métricas estándar de regresión."""
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_real, y_pred))),
        "mae": float(mean_absolute_error(y_real, y_pred)),
        "r2": float(r2_score(y_real, y_pred)),
        "mse": float(mean_squared_error(y_real, y_pred))
    }


# ---- REGISTRO DEL EXPERIMENTO ----

def registrar_experimento(
    cfg: dict,
    params: dict,
    metricas_train: dict,
    metricas_val: dict,
    ruta_modelo: Path
) -> str:
    """
    Registra el experimento con sus parámetros y métricas.

    En MLOps es fundamental registrar CADA experimento para poder:
      1. Comparar qué configuración funcionó mejor
      2. Reproducir cualquier resultado histórico
      3. Auditar el proceso de desarrollo

    Usamos MLflow si está disponible; si no, guardamos en JSON local.
    """
    experimento_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Intentar usar MLflow
    try:
        import warnings as _w
        import logging as _lg
        _w.filterwarnings("ignore", category=FutureWarning, module="mlflow")
        import mlflow
        import mlflow.sklearn
        _lg.getLogger("mlflow.models.model").setLevel(_lg.ERROR)
        _lg.getLogger("mlflow.sklearn").setLevel(_lg.ERROR)

        ruta_experiments = ROOT / cfg["experimentos"]["ruta"]
        uri = ruta_experiments.resolve().as_uri()
        mlflow.set_tracking_uri(uri)
        mlflow.set_experiment(cfg["experimentos"]["nombre_experimento"])

        with mlflow.start_run(run_name=f"run_{experimento_id}"):
            # Registrar parámetros
            for k, v in params.items():
                mlflow.log_param(k, v)

            # Registrar métricas de train
            for k, v in metricas_train.items():
                mlflow.log_metric(f"train_{k}", v)

            # Registrar métricas de validación
            for k, v in metricas_val.items():
                mlflow.log_metric(f"val_{k}", v)

            # Registrar el artefacto del modelo
            with open(ruta_modelo, "rb") as f_modelo:
                mlflow.sklearn.log_model(pickle.load(f_modelo), "modelo")

        log.info("  ✓ Experimento registrado en MLflow (ID: %s)", experimento_id)

    except ImportError:
        # Fallback: guardar en JSON si MLflow no está instalado
        registro = {
            "id": experimento_id,
            "timestamp": datetime.now().isoformat(),
            "algoritmo": cfg["modelo"]["algoritmo"],
            "parametros": params,
            "metricas_train": metricas_train,
            "metricas_validacion": metricas_val,
            "ruta_modelo": str(ruta_modelo)
        }
        ruta_log = ROOT / cfg["experimentos"]["ruta"] / "experimentos.jsonl"
        ruta_log.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta_log, "a") as f:
            f.write(json.dumps(registro) + "\n")
        log.info("  ✓ Experimento guardado en JSON (MLflow no disponible)")

    return experimento_id


# ---- ENTRENAMIENTO ----

def entrenar(
    train_df: pd.DataFrame | None = None,
    cfg: dict | None = None
) -> tuple[object, dict]:
    """Entrena el modelo y registra el experimento."""
    if cfg is None:
        cfg = cargar_config()

    if train_df is None:
        train_df = pd.read_csv(ROOT / cfg["datos"]["ruta_train"])

    log.info("=" * 60)
    log.info("ETAPA 4: ENTRENAMIENTO DEL MODELO")
    log.info("=" * 60)

    target = cfg["datos"]["variable_objetivo"]
    X_train = train_df.drop(columns=[target])
    y_train = train_df[target]

    log.info("  ✓ Datos de entrenamiento: %d muestras × %d features",
             len(X_train), len(X_train.columns))

    # Instanciar y entrenar el modelo
    modelo = obtener_modelo(cfg)
    log.info("▶ Entrenando modelo...")
    modelo.fit(X_train, y_train)

    # Métricas en train (para detectar si hay underfitting)
    y_pred_train = modelo.predict(X_train)
    metricas_train = calcular_metricas(y_train.values, y_pred_train)
    log.info("  Métricas TRAIN → RMSE: %.4f | MAE: %.4f | R²: %.4f",
             metricas_train["rmse"], metricas_train["mae"], metricas_train["r2"])

    # Guardar el modelo entrenado
    ruta_modelo = ROOT / cfg["modelo"]["ruta_modelo"]
    ruta_modelo.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_modelo, "wb") as f:
        pickle.dump(modelo, f)
    log.info("  ✓ Modelo guardado en: %s", ruta_modelo)

    # Importancia de features (si el modelo lo soporta)
    if hasattr(modelo, "feature_importances_"):
        importancias = pd.Series(
            modelo.feature_importances_, index=X_train.columns
        ).sort_values(ascending=False)
        log.info("  Top 5 features más importantes:")
        for feat, imp in importancias.head(5).items():
            log.info("    %-25s %.4f", feat, imp)

    # Registrar experimento
    params = {
        "algoritmo": cfg["modelo"]["algoritmo"],
        "n_features": len(X_train.columns),
        "n_muestras_train": len(X_train),
        **cfg["modelo"]["hiperparametros"].get(cfg["modelo"]["algoritmo"], {})
    }
    registrar_experimento(cfg, params, metricas_train, {}, ruta_modelo)

    log.info("✅ Etapa 4 completada exitosamente\n")
    return modelo, metricas_train


if __name__ == "__main__":
    entrenar()
