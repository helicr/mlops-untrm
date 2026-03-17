"""
============================================================
ETAPA 2: PREPARACIÓN DE DATOS
============================================================
Responsabilidades:
  - Ingestión: cargar datos desde la fuente
  - Validación: verificar calidad y esquema
  - Limpieza: tratar nulos, duplicados, tipos incorrectos
  - División: separar train/test

En MLOps esto es crítico porque:
  - Los datos son la base del modelo; basura entra → basura sale
  - La validación evita que datos corruptos lleguen a producción
  - La división reproducible garantiza comparaciones justas
============================================================
"""

import sys
import yaml
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split

# Agregar raíz del proyecto al path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


def cargar_config() -> dict:
    """Carga la configuración central del proyecto."""
    ruta = ROOT / "config" / "config.yaml"
    with open(ruta) as f:
        return yaml.safe_load(f)


# ---- PASO 1: INGESTIÓN ----

def ingestar_datos(cfg: dict) -> pd.DataFrame:
    """
    Carga los datos desde la fuente definida en config.
    En producción esto podría ser: S3, BigQuery, API, base de datos, etc.
    """
    log.info("▶ Ingestando datos desde: %s", cfg["datos"]["fuente"])

    # Cargar California Housing Dataset (incluido en sklearn)
    dataset = fetch_california_housing(as_frame=True)
    df = dataset.frame.copy()

    # Renombrar la columna objetivo para claridad
    df = df.rename(columns={"MedHouseVal": cfg["datos"]["variable_objetivo"]})

    log.info("  ✓ Datos cargados: %d filas × %d columnas", *df.shape)
    log.info("  Columnas: %s", list(df.columns))

    # Guardar datos crudos (nunca se modifican)
    ruta_raw = ROOT / cfg["datos"]["ruta_raw"]
    ruta_raw.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta_raw, index=False)
    log.info("  ✓ Datos crudos guardados en: %s", ruta_raw)

    return df


# ---- PASO 2: VALIDACIÓN DE DATOS ----

def validar_datos(df: pd.DataFrame, cfg: dict) -> bool:
    """
    Verifica que los datos cumplan las reglas de calidad esperadas.
    Si fallan, el pipeline se detiene (no se entrena con datos malos).

    En MLOps esto se conoce como "Data Validation" y herramientas como
    Great Expectations o TFX Data Validation lo automatizan.
    """
    log.info("▶ Validando calidad de datos...")
    errores = []

    # Regla 1: Las columnas esperadas deben existir
    columnas_esperadas = cfg["features"]["numericas"] + [cfg["datos"]["variable_objetivo"]]
    faltantes = set(columnas_esperadas) - set(df.columns)
    if faltantes:
        errores.append(f"Columnas faltantes: {faltantes}")

    # Regla 2: No debe haber más del 5% de nulos en ninguna columna
    pct_nulos = df.isnull().mean()
    columnas_con_muchos_nulos = pct_nulos[pct_nulos > 0.05].index.tolist()
    if columnas_con_muchos_nulos:
        errores.append(f"Columnas con >5% nulos: {columnas_con_muchos_nulos}")

    # Regla 3: El dataset debe tener suficientes filas
    if len(df) < 1000:
        errores.append(f"Dataset demasiado pequeño: {len(df)} filas (mínimo 1000)")

    # Regla 4: La variable objetivo debe ser numérica positiva
    target = cfg["datos"]["variable_objetivo"]
    if target in df.columns:
        if df[target].min() <= 0:
            errores.append("La variable objetivo contiene valores <= 0")

    # Reportar resultado
    if errores:
        for e in errores:
            log.error("  ✗ %s", e)
        log.error("  VALIDACIÓN FALLIDA — el pipeline se detiene")
        return False

    log.info("  ✓ Validación exitosa — datos aptos para procesamiento")
    return True


# ---- PASO 3: LIMPIEZA ----

def limpiar_datos(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    Aplica transformaciones de limpieza:
      - Elimina duplicados
      - Imputa o elimina nulos
      - Corrige tipos de datos
    """
    log.info("▶ Limpiando datos...")
    n_original = len(df)

    # Eliminar duplicados exactos
    df = df.drop_duplicates()
    n_dup = n_original - len(df)
    if n_dup > 0:
        log.info("  ✓ Eliminados %d duplicados", n_dup)

    # Imputar nulos con la mediana (estrategia simple y robusta)
    columnas_con_nulos = df.columns[df.isnull().any()].tolist()
    if columnas_con_nulos:
        df[columnas_con_nulos] = df[columnas_con_nulos].fillna(
            df[columnas_con_nulos].median()
        )
        log.info("  ✓ Nulos imputados con mediana en: %s", columnas_con_nulos)

    # Eliminar outliers extremos usando Z-score (opcional, configurable)
    if cfg["features"]["eliminar_outliers"]:
        umbral = cfg["features"]["umbral_outliers"]
        features = cfg["features"]["numericas"]
        z_scores = np.abs((df[features] - df[features].mean()) / df[features].std())
        mascara_sin_outliers = (z_scores < umbral).all(axis=1)
        n_antes = len(df)
        df = df[mascara_sin_outliers]
        n_eliminados = n_antes - len(df)
        log.info(
            "  ✓ Outliers eliminados (Z > %.1f): %d filas (%.1f%%)",
            umbral, n_eliminados, 100 * n_eliminados / n_antes
        )

    log.info("  ✓ Dataset limpio: %d filas × %d columnas", *df.shape)
    return df


# ---- PASO 4: DIVISIÓN TRAIN/TEST ----

def dividir_datos(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Divide el dataset en conjuntos de entrenamiento y prueba.

    La semilla (random_state) garantiza reproducibilidad: siempre la misma división.
    Esto es fundamental en MLOps para comparar experimentos de forma justa.
    """
    log.info("▶ Dividiendo datos en train/test...")

    proporcion_test = cfg["datos"]["proporcion_test"]
    semilla = cfg["datos"]["semilla"]

    train_df, test_df = train_test_split(
        df,
        test_size=proporcion_test,
        random_state=semilla
    )

    # Guardar particiones
    ruta_procesada = ROOT / cfg["datos"]["ruta_procesada"]
    ruta_train = ROOT / cfg["datos"]["ruta_train"]
    ruta_test = ROOT / cfg["datos"]["ruta_test"]

    ruta_procesada.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta_procesada, index=False)
    train_df.to_csv(ruta_train, index=False)
    test_df.to_csv(ruta_test, index=False)

    log.info("  ✓ Train: %d filas  |  Test: %d filas", len(train_df), len(test_df))
    log.info("  ✓ Archivos guardados en data/processed/")

    return train_df, test_df


# ---- PUNTO DE ENTRADA ----

def ejecutar(cfg: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ejecuta todo el flujo de preparación de datos."""
    if cfg is None:
        cfg = cargar_config()

    log.info("=" * 60)
    log.info("ETAPA 2: PREPARACIÓN DE DATOS")
    log.info("=" * 60)

    df = ingestar_datos(cfg)

    if not validar_datos(df, cfg):
        raise ValueError("Validación de datos fallida. Revisa los logs.")

    df_limpio = limpiar_datos(df, cfg)
    train_df, test_df = dividir_datos(df_limpio, cfg)

    log.info("✅ Etapa 2 completada exitosamente\n")
    return train_df, test_df


if __name__ == "__main__":
    ejecutar()
