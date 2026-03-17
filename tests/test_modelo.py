"""
Tests del modelo.
Verifican que el modelo sea funcional y cumpla los criterios mínimos de calidad.
"""

import sys
import pickle
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data.preparar_datos import cargar_config
from src.features.ingenieria_features import crear_features


@pytest.fixture
def cfg():
    return cargar_config()


@pytest.fixture
def modelo_entrenado(cfg):
    """Carga el modelo si existe, de lo contrario lo entrena."""
    ruta_modelo = ROOT / cfg["modelo"]["ruta_modelo"]
    if not ruta_modelo.exists():
        pytest.skip("Modelo no entrenado. Ejecuta el pipeline primero.")
    with open(ruta_modelo, "rb") as f:
        return pickle.load(f)


@pytest.fixture
def datos_test(cfg):
    ruta = ROOT / cfg["datos"]["ruta_test"]
    if not ruta.exists():
        pytest.skip("Datos de test no generados. Ejecuta el pipeline primero.")
    return pd.read_csv(ruta)


class TestModeloFuncional:
    def test_modelo_genera_predicciones(self, modelo_entrenado, datos_test, cfg):
        """El modelo debe poder generar predicciones sin errores."""
        target = cfg["datos"]["variable_objetivo"]
        X = datos_test.drop(columns=[target])
        predicciones = modelo_entrenado.predict(X)
        assert len(predicciones) == len(X)

    def test_predicciones_son_numericas(self, modelo_entrenado, datos_test, cfg):
        """Las predicciones deben ser valores numéricos."""
        target = cfg["datos"]["variable_objetivo"]
        X = datos_test.drop(columns=[target])
        predicciones = modelo_entrenado.predict(X)
        assert np.issubdtype(predicciones.dtype, np.floating)

    def test_predicciones_son_positivas(self, modelo_entrenado, datos_test, cfg):
        """Los precios de vivienda deben ser positivos."""
        target = cfg["datos"]["variable_objetivo"]
        X = datos_test.drop(columns=[target])
        predicciones = modelo_entrenado.predict(X)
        assert np.all(predicciones > 0), "Se encontraron predicciones negativas"

    def test_modelo_cumple_umbral_rmse(self, modelo_entrenado, datos_test, cfg):
        """El modelo debe cumplir el umbral de RMSE definido en config."""
        from sklearn.metrics import mean_squared_error
        target = cfg["datos"]["variable_objetivo"]
        X = datos_test.drop(columns=[target])
        y = datos_test[target]
        predicciones = modelo_entrenado.predict(X)
        rmse = np.sqrt(mean_squared_error(y, predicciones))
        umbral = cfg["objetivo"]["umbral_aprobacion"]["rmse"]
        assert rmse < umbral, f"RMSE {rmse:.4f} supera el umbral {umbral}"

    def test_modelo_cumple_umbral_r2(self, modelo_entrenado, datos_test, cfg):
        """El modelo debe cumplir el umbral de R² definido en config."""
        from sklearn.metrics import r2_score
        target = cfg["datos"]["variable_objetivo"]
        X = datos_test.drop(columns=[target])
        y = datos_test[target]
        predicciones = modelo_entrenado.predict(X)
        r2 = r2_score(y, predicciones)
        umbral = cfg["objetivo"]["umbral_aprobacion"]["r2"]
        assert r2 > umbral, f"R² {r2:.4f} está por debajo del umbral {umbral}"


class TestFeatureEngineering:
    def test_crear_features_agrega_columnas(self, cfg):
        """La función de feature engineering debe añadir nuevas columnas."""
        df = pd.DataFrame({
            col: [1.0] * 10 for col in cfg["features"]["numericas"]
        })
        df_con_features = crear_features(df)
        nuevas_cols = set(df_con_features.columns) - set(df.columns)
        assert len(nuevas_cols) > 0, "No se crearon nuevas features"

    def test_features_no_contienen_nan(self, cfg):
        """Las nuevas features no deben generar valores NaN."""
        df = pd.DataFrame({
            col: np.random.rand(50) + 0.1 for col in cfg["features"]["numericas"]
        })
        df_con_features = crear_features(df)
        assert df_con_features.isnull().sum().sum() == 0
