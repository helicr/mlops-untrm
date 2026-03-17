"""
============================================================
ETAPA 5: EVALUACIÓN DEL MODELO
============================================================
Responsabilidades:
  - Evaluar el modelo en el conjunto de TEST (datos nunca vistos)
  - Verificar si cumple los umbrales de aprobación definidos en config
  - Generar reporte de evaluación
  - Decidir si el modelo está listo para producción (aprobado/rechazado)

Por qué importa en MLOps:
  - La evaluación en test simula el comportamiento en producción real
  - Los umbrales de aprobación son el "contrato" entre Data Science y negocio
  - Un modelo que no pasa la evaluación NO debe llegar a producción
  - Este paso puede ser manual (con revisión humana) o automático en CI/CD
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
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def cargar_config() -> dict:
    with open(ROOT / "config" / "config.yaml") as f:
        return yaml.safe_load(f)


# ---- EVALUACIÓN ----

def evaluar(
    modelo=None,
    test_df: pd.DataFrame | None = None,
    cfg: dict | None = None
) -> dict:
    """
    Evalúa el modelo en el conjunto de test y verifica si aprueba
    los umbrales definidos en config.yaml.

    Retorna un diccionario con:
      - metricas: RMSE, MAE, R², MSE
      - aprobado: True/False según los umbrales
      - detalle_aprobacion: qué métricas pasaron/fallaron
    """
    if cfg is None:
        cfg = cargar_config()

    if modelo is None:
        ruta_modelo = ROOT / cfg["modelo"]["ruta_modelo"]
        with open(ruta_modelo, "rb") as f:
            modelo = pickle.load(f)

    if test_df is None:
        test_df = pd.read_csv(ROOT / cfg["datos"]["ruta_test"])

    log.info("=" * 60)
    log.info("ETAPA 5: EVALUACIÓN DEL MODELO")
    log.info("=" * 60)

    target = cfg["datos"]["variable_objetivo"]
    X_test = test_df.drop(columns=[target])
    y_test = test_df[target]

    # Predicciones
    y_pred = modelo.predict(X_test)

    # Métricas
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))
    mse = float(mean_squared_error(y_test, y_pred))

    metricas = {"rmse": rmse, "mae": mae, "r2": r2, "mse": mse}

    log.info("  Métricas en TEST (datos nunca vistos por el modelo):")
    log.info("  ┌─────────────────────────────────┐")
    log.info("  │  RMSE : %8.4f                │", rmse)
    log.info("  │  MAE  : %8.4f                │", mae)
    log.info("  │  R²   : %8.4f                │", r2)
    log.info("  └─────────────────────────────────┘")

    # ---- VERIFICACIÓN DE UMBRALES ----
    umbrales = cfg["objetivo"]["umbral_aprobacion"]
    detalle_aprobacion = {}

    log.info("▶ Verificando umbrales de aprobación...")

    # Verificar RMSE
    rmse_ok = rmse < umbrales["rmse"]
    detalle_aprobacion["rmse"] = {
        "valor": rmse,
        "umbral": umbrales["rmse"],
        "aprobado": rmse_ok,
        "condicion": f"RMSE ({rmse:.4f}) < {umbrales['rmse']}"
    }
    estado = "✓" if rmse_ok else "✗"
    log.info("  %s RMSE: %.4f < %.4f (umbral) → %s",
             estado, rmse, umbrales["rmse"],
             "APROBADO" if rmse_ok else "RECHAZADO")

    # Verificar R²
    r2_ok = r2 > umbrales["r2"]
    detalle_aprobacion["r2"] = {
        "valor": r2,
        "umbral": umbrales["r2"],
        "aprobado": r2_ok,
        "condicion": f"R² ({r2:.4f}) > {umbrales['r2']}"
    }
    estado = "✓" if r2_ok else "✗"
    log.info("  %s R²:   %.4f > %.4f (umbral) → %s",
             estado, r2, umbrales["r2"],
             "APROBADO" if r2_ok else "RECHAZADO")

    # El modelo se aprueba SOLO si TODAS las métricas pasan
    aprobado = all(d["aprobado"] for d in detalle_aprobacion.values())

    if aprobado:
        log.info("  ✅ MODELO APROBADO — listo para despliegue a producción")
    else:
        log.warning("  ❌ MODELO RECHAZADO — no cumple los umbrales mínimos")
        log.warning("     → Acciones recomendadas:")
        log.warning("        1. Revisar calidad de datos")
        log.warning("        2. Probar otros algoritmos en config.yaml")
        log.warning("        3. Ajustar hiperparámetros")
        log.warning("        4. Crear más features relevantes")

    # Análisis de errores residuales
    residuos = y_test.values - y_pred
    log.info("\n  Análisis de residuos:")
    log.info("    Media de errores: %.4f (idealmente ~0)", residuos.mean())
    log.info("    Std de errores:   %.4f", residuos.std())
    log.info("    Error máximo:     %.4f", np.abs(residuos).max())
    log.info("    Percentil 90:     %.4f", np.percentile(np.abs(residuos), 90))

    # Guardar reporte de evaluación
    reporte = {
        "timestamp": datetime.now().isoformat(),
        "algoritmo": cfg["modelo"]["algoritmo"],
        "n_muestras_test": len(X_test),
        "metricas": metricas,
        "aprobado": aprobado,
        "detalle_aprobacion": detalle_aprobacion
    }
    ruta_reporte = ROOT / cfg["experimentos"]["ruta"] / "reporte_evaluacion.json"
    ruta_reporte.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_reporte, "w") as f:
        json.dump(reporte, f, indent=2)
    log.info("\n  ✓ Reporte guardado en: %s", ruta_reporte)

    log.info("✅ Etapa 5 completada\n")
    return reporte


if __name__ == "__main__":
    resultado = evaluar()
    if not resultado["aprobado"]:
        sys.exit(1)  # Retornar código de error para detener el pipeline en CI/CD
