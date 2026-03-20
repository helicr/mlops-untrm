"""
============================================================
BATCH INFERENCE — Inferencia masiva desde fichero
============================================================
Uso:
  python src/serving/batch_inference.py \\
      --input  data/nuevas_viviendas.csv \\
      --output output/predicciones.csv

Con Docker:
  docker run --rm \\
      -v %cd%/data:/app/data \\
      -v %cd%/output:/app/output \\
      -v %cd%/experiments:/app/experiments \\
      mlops-viviendas:v1 \\
      python src/serving/batch_inference.py \\
          --input data/nuevas_viviendas.csv \\
          --output output/predicciones.csv

Formato del CSV de entrada (8 columnas obligatorias):
  MedInc, HouseAge, AveRooms, AveBedrms, Population, AveOccup, Latitude, Longitude

Formato del CSV de salida:
  Todas las columnas de entrada + prediccion_normalizada + precio_estimado_usd
  + batch_id + timestamp + version_modelo
============================================================
"""

import sys
import json
import pickle
import logging
import argparse
import numpy as np
import pandas as pd
import yaml
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

FEATURES_ENTRADA = [
    "MedInc", "HouseAge", "AveRooms", "AveBedrms",
    "Population", "AveOccup", "Latitude", "Longitude"
]


# ── Carga de artefactos ────────────────────────────────────────────────────────

def cargar_config() -> dict:
    with open(ROOT / "config" / "config.yaml") as f:
        return yaml.safe_load(f)


def cargar_artefactos(cfg: dict):
    ruta_modelo = ROOT / cfg["modelo"]["ruta_modelo"]
    ruta_scaler = ROOT / cfg["modelo"]["ruta_scaler"]

    if not ruta_modelo.exists():
        raise FileNotFoundError(f"Modelo no encontrado: {ruta_modelo}")
    if not ruta_scaler.exists():
        raise FileNotFoundError(f"Scaler no encontrado: {ruta_scaler}")

    with open(ruta_modelo, "rb") as f:
        modelo = pickle.load(f)
    with open(ruta_scaler, "rb") as f:
        scaler_obj = pickle.load(f)

    if isinstance(scaler_obj, dict):
        scaler = scaler_obj["scaler"]
        columnas_scaler = scaler_obj["columnas"]
    else:
        scaler = scaler_obj
        columnas_scaler = FEATURES_ENTRADA

    log.info("Modelo cargado: %s", type(modelo).__name__)
    log.info("Scaler cargado: %s (%d columnas)", type(scaler).__name__, len(columnas_scaler))
    return modelo, scaler, columnas_scaler


# ── Pipeline de transformación (mismo que API y entrenamiento) ─────────────────

def crear_features_derivadas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["rooms_per_person"] = df["AveRooms"] / (df["AveOccup"] + 1e-6)
    df["income_per_room"]  = df["MedInc"]   / (df["AveRooms"] + 1e-6)
    df["bedroom_ratio"]    = df["AveBedrms"] / (df["AveRooms"] + 1e-6)
    df["dist_sacramento"]  = np.sqrt(
        (df["Latitude"] - 38.5) ** 2 + (df["Longitude"] - (-121.5)) ** 2
    )
    df["dist_los_angeles"] = np.sqrt(
        (df["Latitude"] - 34.0) ** 2 + (df["Longitude"] - (-118.2)) ** 2
    )
    return df


def preparar_batch(df: pd.DataFrame, scaler, columnas_scaler: list) -> pd.DataFrame:
    df = crear_features_derivadas(df)
    cols_presentes = [c for c in columnas_scaler if c in df.columns]
    df[cols_presentes] = scaler.transform(df[cols_presentes])
    return df[cols_presentes]


# ── Validación de entrada ──────────────────────────────────────────────────────

def validar_entrada(df: pd.DataFrame) -> None:
    faltantes = [c for c in FEATURES_ENTRADA if c not in df.columns]
    if faltantes:
        raise ValueError(f"Columnas faltantes en el CSV de entrada: {faltantes}")

    nulos = df[FEATURES_ENTRADA].isnull().sum()
    if nulos.any():
        log.warning("Filas con nulos detectadas:\n%s", nulos[nulos > 0].to_string())

    numericas = ["MedInc", "HouseAge", "AveRooms", "AveBedrms",
                 "Population", "AveOccup", "Latitude", "Longitude"]
    positivas = ["MedInc", "HouseAge", "AveRooms", "AveBedrms", "Population", "AveOccup"]
    for col in positivas:
        if (df[col] <= 0).any():
            n = int((df[col] <= 0).sum())
            log.warning("Columna '%s': %d registros con valor <= 0", col, n)


# ── Ejecución principal ────────────────────────────────────────────────────────

def ejecutar_batch(ruta_entrada: Path, ruta_salida: Path) -> dict:
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log.info("=" * 55)
    log.info("  BATCH INFERENCE — batch_id: %s", batch_id)
    log.info("=" * 55)

    # 1. Cargar configuración y artefactos
    cfg = cargar_config()
    modelo, scaler, columnas_scaler = cargar_artefactos(cfg)

    # 2. Leer fichero de entrada
    log.info("Leyendo entrada: %s", ruta_entrada)
    df_entrada = pd.read_csv(ruta_entrada)
    n_registros = len(df_entrada)
    log.info("Registros leídos: %d", n_registros)

    # 3. Validar
    validar_entrada(df_entrada)
    df_limpio = df_entrada.dropna(subset=FEATURES_ENTRADA).copy()
    n_descartados = n_registros - len(df_limpio)
    if n_descartados > 0:
        log.warning("Registros descartados por nulos: %d", n_descartados)

    # 4. Transformar (feature engineering + escalado)
    log.info("Aplicando pipeline de transformación...")
    import time
    t0 = time.perf_counter()
    df_procesado = preparar_batch(df_limpio, scaler, columnas_scaler)
    t_transform = time.perf_counter() - t0

    # 5. Predecir
    log.info("Ejecutando predicciones...")
    t1 = time.perf_counter()
    predicciones = modelo.predict(df_procesado)
    t_predict = time.perf_counter() - t1

    t_total = t_transform + t_predict

    # 6. Construir DataFrame de salida
    df_salida = df_limpio[FEATURES_ENTRADA].copy()
    df_salida["prediccion_normalizada"] = predicciones.round(4)
    df_salida["precio_estimado_usd"]    = (predicciones * 100_000).round(0).astype(int)
    df_salida["batch_id"]               = batch_id
    df_salida["timestamp"]              = datetime.now().isoformat()
    df_salida["version_modelo"]         = type(modelo).__name__

    # 7. Guardar CSV de salida
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df_salida.to_csv(ruta_salida, index=False)
    log.info("Predicciones guardadas en: %s", ruta_salida)

    # 8. Reporte de ejecución
    throughput = len(df_limpio) / t_total if t_total > 0 else 0
    reporte = {
        "batch_id":             batch_id,
        "timestamp":            datetime.now().isoformat(),
        "modelo":               type(modelo).__name__,
        "fichero_entrada":      str(ruta_entrada),
        "fichero_salida":       str(ruta_salida),
        "n_registros_entrada":  n_registros,
        "n_registros_procesados": len(df_limpio),
        "n_registros_descartados": n_descartados,
        "tiempos_ms": {
            "transformacion": round(t_transform * 1000, 2),
            "prediccion":     round(t_predict   * 1000, 2),
            "total":          round(t_total      * 1000, 2),
        },
        "throughput_reg_seg":     round(throughput, 0),
        "latencia_ms_registro":   round(t_total / len(df_limpio) * 1000, 4) if len(df_limpio) else 0,
        "estadisticas_predicciones": {
            "media": round(float(predicciones.mean()), 4),
            "std":   round(float(predicciones.std()),  4),
            "min":   round(float(predicciones.min()),  4),
            "max":   round(float(predicciones.max()),  4),
            "p25":   round(float(np.percentile(predicciones, 25)), 4),
            "p75":   round(float(np.percentile(predicciones, 75)), 4),
        },
    }

    ruta_reporte = ruta_salida.parent / f"reporte_batch_{batch_id}.json"
    with open(ruta_reporte, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    log.info("=" * 55)
    log.info("  Registros procesados : %d", len(df_limpio))
    log.info("  Tiempo total         : %.1f ms", t_total * 1000)
    log.info("  Throughput           : %.0f reg/s", throughput)
    log.info("  Reporte guardado en  : %s", ruta_reporte)
    log.info("=" * 55)

    return reporte


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Inferencia batch: CSV entrada → CSV con predicciones"
    )
    parser.add_argument(
        "--input", required=True,
        help="Ruta al CSV de entrada (8 features: MedInc, HouseAge, ...)"
    )
    parser.add_argument(
        "--output", required=True,
        help="Ruta al CSV de salida con predicciones"
    )
    args = parser.parse_args()

    ruta_entrada = Path(args.input)
    ruta_salida  = Path(args.output)

    if not ruta_entrada.exists():
        log.error("Fichero de entrada no encontrado: %s", ruta_entrada)
        sys.exit(1)

    ejecutar_batch(ruta_entrada, ruta_salida)


if __name__ == "__main__":
    main()
