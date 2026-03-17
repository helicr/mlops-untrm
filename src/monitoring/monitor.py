"""
============================================================
ETAPA 7: MONITOREO DEL MODELO EN PRODUCCIÓN
============================================================
Responsabilidades:
  - Detectar DATA DRIFT: ¿cambiaron las distribuciones de los datos de entrada?
  - Detectar CONCEPT DRIFT: ¿se degradó la calidad de las predicciones?
  - Generar alertas cuando se detectan problemas
  - Recomendar si se requiere re-entrenamiento

Por qué importa en MLOps:
  - Un modelo entrenado hoy puede quedar obsoleto mañana.
    Los datos del mundo real cambian (precios, comportamientos, patrones).
  - Sin monitoreo, el modelo puede estar haciendo predicciones malas
    sin que nadie lo sepa.
  - El monitoreo cierra el ciclo: detección de drift → re-entrenamiento.

Tipos de drift:
  - Data Drift: Las features de entrada cambian de distribución.
    Ej: las casas que llegan hoy tienen áreas muy distintas a las del entrenamiento.
  - Concept Drift: La relación entre features y target cambia.
    Ej: los precios subieron un 30% por inflación → el modelo subestima todo.
  - Label Drift: La distribución del target cambia.

Métrica usada: PSI (Population Stability Index)
  PSI < 0.1  → Sin cambio significativo
  PSI < 0.2  → Cambio moderado (vigilar)
  PSI >= 0.2 → Cambio significativo (re-entrenar)
============================================================
"""

import sys
import json
import logging
import numpy as np
import pandas as pd
import yaml
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def cargar_config() -> dict:
    with open(ROOT / "config" / "config.yaml") as f:
        return yaml.safe_load(f)


# ---- CÁLCULO DE PSI (Population Stability Index) ----

def calcular_psi(referencia: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """
    Calcula el PSI para detectar data drift entre dos distribuciones.

    PSI = Σ (actual% - referencia%) × ln(actual% / referencia%)

    referencia: distribución de los datos de entrenamiento
    actual:     distribución de los datos recientes en producción
    """
    # Crear bins basados en la distribución de referencia
    breakpoints = np.linspace(0, 100, bins + 1)
    puntos_corte = np.percentile(referencia, breakpoints)
    puntos_corte = np.unique(puntos_corte)

    # Calcular frecuencias
    def calcular_frecuencias(datos: np.ndarray) -> np.ndarray:
        conteo, _ = np.histogram(datos, bins=puntos_corte)
        frecuencias = conteo / len(datos)
        # Evitar ceros para el logaritmo
        return np.where(frecuencias == 0, 1e-6, frecuencias)

    freq_ref = calcular_frecuencias(referencia)
    freq_act = calcular_frecuencias(actual)

    psi = np.sum((freq_act - freq_ref) * np.log(freq_act / freq_ref))
    return float(psi)


# ---- ANÁLISIS DE DRIFT ----

def detectar_data_drift(cfg: dict) -> dict:
    """
    Compara la distribución de los datos de producción contra
    los datos de entrenamiento para detectar data drift.
    """
    log.info("▶ Analizando Data Drift...")

    # Cargar datos de referencia (entrenamiento)
    train_df = pd.read_csv(ROOT / cfg["datos"]["ruta_train"])

    # Cargar predicciones de producción (contiene los inputs recibidos)
    ruta_predicciones = ROOT / "experiments" / "predicciones_produccion.jsonl"

    if not ruta_predicciones.exists():
        log.info("  ℹ Sin datos de producción aún. Generando datos simulados para demo...")
        # Simular drift agregando ruido para demostración
        produccion_df = train_df.sample(200, random_state=99).copy()
        for col in cfg["features"]["numericas"][:3]:
            produccion_df[col] = produccion_df[col] * np.random.uniform(0.8, 1.2, len(produccion_df))
    else:
        predicciones = []
        with open(ruta_predicciones) as f:
            for linea in f:
                reg = json.loads(linea)
                predicciones.append(reg["input"])
        produccion_df = pd.DataFrame(predicciones)

    features = [f for f in cfg["features"]["numericas"] if f in produccion_df.columns]
    umbral = cfg["monitoreo"]["umbral_drift_psi"]

    resultados_drift = {}
    features_con_drift = []

    log.info("  PSI por feature (umbral: %.2f):", umbral)
    for feature in features:
        if feature in train_df.columns and feature in produccion_df.columns:
            psi = calcular_psi(train_df[feature].values, produccion_df[feature].values)
            nivel = "🟢 OK" if psi < 0.1 else ("🟡 MODERADO" if psi < umbral else "🔴 DRIFT")
            log.info("    %-20s PSI=%.4f  %s", feature, psi, nivel)
            resultados_drift[feature] = {"psi": psi, "drift_detectado": psi >= umbral}
            if psi >= umbral:
                features_con_drift.append(feature)

    hay_drift = len(features_con_drift) > 0
    if hay_drift:
        log.warning("  ⚠️  DRIFT DETECTADO en: %s", features_con_drift)
        log.warning("     → Recomendación: re-entrenar el modelo con datos recientes")
    else:
        log.info("  ✓ Sin drift significativo detectado")

    return {
        "hay_drift": hay_drift,
        "features_con_drift": features_con_drift,
        "detalle": resultados_drift
    }


def detectar_concept_drift(cfg: dict) -> dict:
    """
    Detecta si la calidad del modelo se ha degradado comparando
    las métricas actuales contra las métricas del entrenamiento.

    En producción real, necesitarías labels (valores reales) para comparar.
    Aquí simulamos usando el conjunto de test como proxy de "datos recientes".
    """
    log.info("▶ Analizando Concept Drift (degradación del modelo)...")

    # Cargar reporte de evaluación original
    ruta_reporte = ROOT / cfg["experimentos"]["ruta"] / "reporte_evaluacion.json"
    if not ruta_reporte.exists():
        log.warning("  No hay reporte de evaluación. Ejecuta primero evaluar.py")
        return {"hay_degradacion": False, "mensaje": "Sin datos históricos"}

    with open(ruta_reporte) as f:
        reporte_original = json.load(f)

    rmse_original = reporte_original["metricas"]["rmse"]
    umbral = cfg["monitoreo"]["umbral_degradacion_rmse"]

    # Simular métricas "actuales" con leve degradación para demostración
    rmse_actual = rmse_original * (1 + np.random.uniform(0, 0.15))

    incremento = (rmse_actual - rmse_original) / rmse_original
    hay_degradacion = incremento > umbral

    log.info("  RMSE original (entrenamiento): %.4f", rmse_original)
    log.info("  RMSE actual   (producción):    %.4f", rmse_actual)
    log.info("  Incremento:                    %.1f%%", incremento * 100)

    if hay_degradacion:
        log.warning("  ⚠️  DEGRADACIÓN DETECTADA: RMSE subió %.1f%% (umbral: %.0f%%)",
                    incremento * 100, umbral * 100)
        log.warning("     → Recomendación: re-entrenar el modelo")
    else:
        log.info("  ✓ Modelo estable (degradación < %.0f%%)", umbral * 100)

    return {
        "hay_degradacion": hay_degradacion,
        "rmse_original": rmse_original,
        "rmse_actual": rmse_actual,
        "incremento_pct": round(incremento * 100, 2),
        "umbral_pct": umbral * 100
    }


# ---- REPORTE DE MONITOREO ----

def generar_reporte_monitoreo(cfg: dict) -> dict:
    """Genera un reporte consolidado de monitoreo."""
    log.info("=" * 60)
    log.info("ETAPA 7: MONITOREO DEL MODELO EN PRODUCCIÓN")
    log.info("=" * 60)

    drift_datos = detectar_data_drift(cfg)
    drift_concepto = detectar_concept_drift(cfg)

    requiere_reentrenamiento = (
        drift_datos["hay_drift"] or drift_concepto["hay_degradacion"]
    )

    reporte = {
        "timestamp": datetime.now().isoformat(),
        "data_drift": drift_datos,
        "concept_drift": drift_concepto,
        "requiere_reentrenamiento": requiere_reentrenamiento,
        "accion_recomendada": (
            "RE-ENTRENAR EL MODELO con datos recientes"
            if requiere_reentrenamiento
            else "NINGUNA — modelo estable"
        )
    }

    log.info("\n  ─── RESUMEN DE MONITOREO ───")
    log.info("  Data Drift:     %s", "⚠️  DETECTADO" if drift_datos["hay_drift"] else "✓ OK")
    log.info("  Concept Drift:  %s", "⚠️  DETECTADO" if drift_concepto["hay_degradacion"] else "✓ OK")
    log.info("  Acción:         %s", reporte["accion_recomendada"])

    # Guardar reporte
    ruta_reporte = ROOT / cfg["experimentos"]["ruta"] / "reporte_monitoreo.json"
    ruta_reporte.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_reporte, "w") as f:
        json.dump(reporte, f, indent=2, default=str)
    log.info("\n  ✓ Reporte guardado en: %s", ruta_reporte)

    if requiere_reentrenamiento:
        log.warning("\n  🔄 CICLO MLOps: iniciando re-entrenamiento...")
        log.warning("     El pipeline completo se ejecutará nuevamente")

    log.info("✅ Etapa 7 completada\n")
    return reporte


if __name__ == "__main__":
    cfg = cargar_config()
    generar_reporte_monitoreo(cfg)
