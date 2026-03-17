"""
Tests de calidad de datos.
En MLOps, las pruebas son parte del pipeline: si fallan, el modelo no se entrena.
"""

import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data.preparar_datos import cargar_config, ingestar_datos, validar_datos, limpiar_datos


@pytest.fixture
def cfg():
    return cargar_config()


@pytest.fixture
def datos_raw(cfg):
    return ingestar_datos(cfg)


class TestIngestaDatos:
    def test_ingestión_retorna_dataframe(self, datos_raw):
        assert isinstance(datos_raw, pd.DataFrame)

    def test_dataset_no_vacio(self, datos_raw):
        assert len(datos_raw) > 1000, "El dataset debe tener más de 1000 filas"

    def test_columnas_esperadas_presentes(self, datos_raw, cfg):
        columnas_esperadas = cfg["features"]["numericas"] + [cfg["datos"]["variable_objetivo"]]
        for col in columnas_esperadas:
            assert col in datos_raw.columns, f"Columna faltante: {col}"


class TestValidacionDatos:
    def test_validacion_pasa_con_datos_correctos(self, datos_raw, cfg):
        assert validar_datos(datos_raw, cfg) is True

    def test_validacion_falla_con_columnas_faltantes(self, cfg):
        df_malo = pd.DataFrame({"columna_inexistente": [1, 2, 3]})
        assert validar_datos(df_malo, cfg) is False

    def test_validacion_falla_con_muchos_nulos(self, datos_raw, cfg):
        df_con_nulos = datos_raw.copy()
        df_con_nulos["MedInc"] = np.nan  # 100% nulos en una columna
        assert validar_datos(df_con_nulos, cfg) is False

    def test_validacion_falla_dataset_pequeno(self, cfg):
        df_pequeno = pd.DataFrame({
            col: [1.0] * 10 for col in cfg["features"]["numericas"]
        })
        df_pequeno[cfg["datos"]["variable_objetivo"]] = [2.0] * 10
        assert validar_datos(df_pequeno, cfg) is False


class TestLimpiezaDatos:
    def test_limpieza_elimina_duplicados(self, datos_raw, cfg):
        df_con_duplicados = pd.concat([datos_raw.head(100), datos_raw.head(50)])
        df_limpio = limpiar_datos(df_con_duplicados, cfg)
        assert len(df_limpio) <= len(df_con_duplicados)
        assert df_limpio.duplicated().sum() == 0

    def test_limpieza_imputa_nulos(self, datos_raw, cfg):
        df_con_nulos = datos_raw.copy()
        df_con_nulos.loc[df_con_nulos.index[:10], "MedInc"] = np.nan
        df_limpio = limpiar_datos(df_con_nulos, cfg)
        assert df_limpio["MedInc"].isnull().sum() == 0

    def test_limpieza_no_genera_nulos_nuevos(self, datos_raw, cfg):
        df_limpio = limpiar_datos(datos_raw, cfg)
        assert df_limpio.isnull().sum().sum() == 0
