"""
============================================================
ETAPA 3: INGENIERÍA DE FEATURES
============================================================
Responsabilidades:
  - Transformar variables crudas en representaciones útiles para el modelo
  - Crear nuevas variables que capturen patrones del dominio
  - Escalar/normalizar para que los algoritmos funcionen correctamente
  - Guardar los transformadores para usarlos en producción (¡crítico!)

Por qué importa en MLOps:
  - El mismo transformador entrenado en train DEBE usarse en producción.
    Si entrenas un nuevo StandardScaler en cada predicción, los resultados
    serán inconsistentes (training-serving skew).
  - Las features son la parte más creativa y de mayor impacto en el modelo.
============================================================
"""

import sys
import pickle
import logging
import numpy as np
import pandas as pd
import yaml
from pathlib import Path
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def cargar_config() -> dict:
    with open(ROOT / "config" / "config.yaml") as f:
        return yaml.safe_load(f)


# ---- CREACIÓN DE NUEVAS FEATURES ----

def crear_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables derivadas que capturan conocimiento del dominio.

    Ejemplos de razonamiento:
      - rooms_per_person: densidad habitacional, proxy de hacinamiento
      - income_per_room: poder adquisitivo relativo al tamaño
      - bedroom_ratio: proporción de dormitorios sobre total de cuartos
    """
    log.info("▶ Creando nuevas features...")
    df = df.copy()

    # Feature 1: Cuartos por persona (densidad habitacional)
    df["rooms_per_person"] = df["AveRooms"] / (df["AveOccup"] + 1e-6)

    # Feature 2: Ingreso por cuarto (poder adquisitivo por espacio)
    df["income_per_room"] = df["MedInc"] / (df["AveRooms"] + 1e-6)

    # Feature 3: Ratio de dormitorios (¿qué fracción son dormitorios?)
    df["bedroom_ratio"] = df["AveBedrms"] / (df["AveRooms"] + 1e-6)

    # Feature 4: Distancia al centro de California (Sacramento: 38.5°N, -121.5°W)
    df["dist_sacramento"] = np.sqrt(
        (df["Latitude"] - 38.5) ** 2 + (df["Longitude"] - (-121.5)) ** 2
    )

    # Feature 5: Distancia a Los Ángeles (34°N, -118.2°W)
    df["dist_los_angeles"] = np.sqrt(
        (df["Latitude"] - 34.0) ** 2 + (df["Longitude"] - (-118.2)) ** 2
    )

    nuevas = ["rooms_per_person", "income_per_room", "bedroom_ratio",
              "dist_sacramento", "dist_los_angeles"]
    log.info("  ✓ Nuevas features creadas: %s", nuevas)
    return df


# ---- ESCALADO ----

def escalar_features(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    cfg: dict,
    ruta_scaler: Path | None = None
) -> tuple[pd.DataFrame, pd.DataFrame, object]:
    """
    Escala las features numéricas.

    REGLA FUNDAMENTAL DE MLOps:
      - El scaler se AJUSTA (fit) SOLO con datos de entrenamiento.
      - El scaler se APLICA (transform) tanto a train como a test y producción.
      - Esto evita "data leakage" (filtración de información del futuro).
    """
    log.info("▶ Escalando features...")

    metodo = cfg["features"]["metodo_escalado"]
    scalers = {
        "standard": StandardScaler(),
        "minmax": MinMaxScaler(),
        "robust": RobustScaler()  # Más resistente a outliers
    }
    scaler = scalers[metodo]

    # Determinar qué columnas escalar (features + las nuevas creadas)
    columnas_base = cfg["features"]["numericas"]
    columnas_nuevas = [c for c in df_train.columns
                       if c not in columnas_base
                       and c != cfg["datos"]["variable_objetivo"]]
    columnas_a_escalar = columnas_base + columnas_nuevas

    # ✅ fit SOLO en train (aprende media y std del conjunto de entrenamiento)
    scaler.fit(df_train[columnas_a_escalar])

    # ✅ transform en ambos (aplica la misma transformación)
    df_train = df_train.copy()
    df_test = df_test.copy()
    df_train[columnas_a_escalar] = scaler.transform(df_train[columnas_a_escalar])
    df_test[columnas_a_escalar] = scaler.transform(df_test[columnas_a_escalar])

    # Guardar el scaler para usarlo en producción
    if ruta_scaler is None:
        ruta_scaler = ROOT / cfg["modelo"]["ruta_scaler"]
    ruta_scaler.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_scaler, "wb") as f:
        pickle.dump({"scaler": scaler, "columnas": columnas_a_escalar}, f)

    log.info("  ✓ Scaler '%s' ajustado y guardado en: %s", metodo, ruta_scaler)
    log.info("  ✓ Features escaladas: %d columnas", len(columnas_a_escalar))
    return df_train, df_test, scaler


# ---- PUNTO DE ENTRADA ----

def ejecutar(
    train_df: pd.DataFrame | None = None,
    test_df: pd.DataFrame | None = None,
    cfg: dict | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ejecuta el pipeline de ingeniería de features."""
    if cfg is None:
        cfg = cargar_config()

    # Si no se pasan dataframes, cargar desde disco
    if train_df is None:
        train_df = pd.read_csv(ROOT / cfg["datos"]["ruta_train"])
        test_df = pd.read_csv(ROOT / cfg["datos"]["ruta_test"])

    log.info("=" * 60)
    log.info("ETAPA 3: INGENIERÍA DE FEATURES")
    log.info("=" * 60)

    # Crear nuevas features en train y test
    train_df = crear_features(train_df)
    test_df = crear_features(test_df)

    # Escalar (ajustar solo con train, transformar ambos)
    if cfg["features"]["escalar"]:
        train_df, test_df, _ = escalar_features(train_df, test_df, cfg)

    # Guardar datasets con features
    train_df.to_csv(ROOT / cfg["datos"]["ruta_train"], index=False)
    test_df.to_csv(ROOT / cfg["datos"]["ruta_test"], index=False)

    log.info("  ✓ Features totales: %d", len(train_df.columns) - 1)
    log.info("✅ Etapa 3 completada exitosamente\n")
    return train_df, test_df


if __name__ == "__main__":
    ejecutar()
