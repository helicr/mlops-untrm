"""
============================================================
ETAPA 6: DESPLIEGUE — API REST DE PREDICCIÓN
============================================================
Responsabilidades:
  - Exponer el modelo como un servicio HTTP consumible
  - Recibir datos nuevos, transformarlos y retornar predicciones
  - Registrar cada predicción (para monitoreo futuro)
  - Manejar errores graciosamente

Por qué importa en MLOps:
  - El modelo solo tiene valor si puede ser consumido por otras aplicaciones
  - La API es el "contrato" con los consumidores del modelo
  - El versionado (/v1/) permite actualizaciones sin romper consumidores
  - El logging de predicciones alimenta el sistema de monitoreo

Cómo ejecutar:
  uvicorn src.serving.api:app --reload --port 8000

Cómo probar:
  curl -X POST "http://localhost:8000/v1/predecir" \
    -H "Content-Type: application/json" \
    -d '{"MedInc": 5.0, "HouseAge": 20, "AveRooms": 6.0,
         "AveBedrms": 1.0, "Population": 1000, "AveOccup": 3.0,
         "Latitude": 37.5, "Longitude": -122.0}'
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

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def cargar_config() -> dict:
    with open(ROOT / "config" / "config.yaml") as f:
        return yaml.safe_load(f)


# ---- Intentar importar FastAPI (opcional) ----
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    from pydantic import BaseModel, Field
    FASTAPI_DISPONIBLE = True
except ImportError:
    FASTAPI_DISPONIBLE = False
    log.warning("FastAPI no instalado. Ejecuta: pip install fastapi uvicorn")


# ---- CARGA DEL MODELO ----

_cfg = cargar_config()
_modelo = None
_scaler_data = None


def cargar_modelo():
    """Carga el modelo y el scaler desde disco (lazy loading)."""
    global _modelo, _scaler_data

    if _modelo is None:
        ruta_modelo = ROOT / _cfg["modelo"]["ruta_modelo"]
        with open(ruta_modelo, "rb") as f:
            _modelo = pickle.load(f)
        log.info("Modelo cargado desde: %s", ruta_modelo)

    if _scaler_data is None:
        ruta_scaler = ROOT / _cfg["modelo"]["ruta_scaler"]
        with open(ruta_scaler, "rb") as f:
            _scaler_data = pickle.load(f)
        log.info("Scaler cargado desde: %s", ruta_scaler)

    return _modelo, _scaler_data


# ---- LÓGICA DE PREDICCIÓN (independiente de FastAPI) ----

def preparar_input(datos: dict) -> pd.DataFrame:
    """
    Aplica las mismas transformaciones que en entrenamiento.
    Este es el punto crítico del "training-serving parity":
    la lógica debe ser IDÉNTICA a src/features/ingenieria_features.py
    """
    df = pd.DataFrame([datos])

    # Crear las mismas features derivadas
    df["rooms_per_person"] = df["AveRooms"] / (df["AveOccup"] + 1e-6)
    df["income_per_room"] = df["MedInc"] / (df["AveRooms"] + 1e-6)
    df["bedroom_ratio"] = df["AveBedrms"] / (df["AveRooms"] + 1e-6)
    df["dist_sacramento"] = np.sqrt(
        (df["Latitude"] - 38.5) ** 2 + (df["Longitude"] - (-121.5)) ** 2
    )
    df["dist_los_angeles"] = np.sqrt(
        (df["Latitude"] - 34.0) ** 2 + (df["Longitude"] - (-118.2)) ** 2
    )

    # Aplicar el mismo scaler
    _, scaler_data = cargar_modelo()
    columnas = scaler_data["columnas"]
    df[columnas] = scaler_data["scaler"].transform(df[columnas])

    return df


def predecir(datos: dict) -> dict:
    """Genera una predicción y la registra para monitoreo."""
    modelo, _ = cargar_modelo()
    df_input = preparar_input(datos)

    prediccion = float(modelo.predict(df_input)[0])

    # Registrar predicción para monitoreo posterior
    registro = {
        "timestamp": datetime.now().isoformat(),
        "input": datos,
        "prediccion": prediccion
    }
    ruta_log = ROOT / "experiments" / "predicciones_produccion.jsonl"
    ruta_log.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_log, "a") as f:
        f.write(json.dumps(registro) + "\n")

    # El precio está en unidades de $100,000 en el dataset California Housing
    return {
        "prediccion_normalizada": prediccion,
        "precio_estimado_usd": prediccion * 100_000,
        "unidad": "USD"
    }


# ---- API FastAPI ----

if FASTAPI_DISPONIBLE:
    _STATIC = Path(__file__).parent / "static"

    app = FastAPI(
        title="API de Predicción de Precios de Vivienda",
        description="Modelo MLOps - California Housing Price Predictor",
        version=_cfg["api"]["version"]
    )

    app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")

    @app.get("/ui", include_in_schema=False)
    def interfaz_web():
        """Interfaz web amigable para usuarios de negocio."""
        return FileResponse(str(_STATIC / "index.html"))

    class EntradaVivienda(BaseModel):
        """Datos de entrada para predecir el precio de una vivienda."""
        MedInc: float = Field(..., description="Ingreso mediano del bloque (en $10,000)", gt=0)
        HouseAge: float = Field(..., description="Edad mediana de las viviendas (años)", gt=0)
        AveRooms: float = Field(..., description="Promedio de cuartos por vivienda", gt=0)
        AveBedrms: float = Field(..., description="Promedio de dormitorios por vivienda", gt=0)
        Population: float = Field(..., description="Población del bloque", gt=0)
        AveOccup: float = Field(..., description="Promedio de ocupantes por vivienda", gt=0)
        Latitude: float = Field(..., description="Latitud del bloque")
        Longitude: float = Field(..., description="Longitud del bloque")

    class RespuestaPrediccion(BaseModel):
        prediccion_normalizada: float
        precio_estimado_usd: float
        unidad: str

    @app.get("/")
    def raiz():
        """Health check del servicio."""
        return {
            "servicio": "API de Predicción de Viviendas",
            "version": _cfg["api"]["version"],
            "estado": "activo",
            "modelo": _cfg["modelo"]["algoritmo"]
        }

    @app.get("/health")
    def health_check():
        """Verificación de salud para load balancers / Kubernetes."""
        try:
            cargar_modelo()
            return {"status": "healthy", "modelo_cargado": True}
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Modelo no disponible: {e}")

    @app.post(f"/{_cfg['api']['version']}/predecir", response_model=RespuestaPrediccion)
    def endpoint_prediccion(vivienda: EntradaVivienda):
        """
        Predice el precio de una vivienda.

        Ejemplo de uso:
        ```json
        {
          "MedInc": 5.0,
          "HouseAge": 20,
          "AveRooms": 6.0,
          "AveBedrms": 1.0,
          "Population": 1000,
          "AveOccup": 3.0,
          "Latitude": 37.5,
          "Longitude": -122.0
        }
        ```
        """
        try:
            resultado = predecir(vivienda.model_dump())
            log.info("Predicción: $%.0f USD", resultado["precio_estimado_usd"])
            return resultado
        except Exception as e:
            log.error("Error en predicción: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get(f"/{_cfg['api']['version']}/info-modelo")
    def info_modelo():
        """Retorna información sobre el modelo en producción."""
        modelo, _ = cargar_modelo()
        return {
            "algoritmo": _cfg["modelo"]["algoritmo"],
            "version": _cfg["proyecto"]["version"],
            "features": _cfg["features"]["numericas"],
            "metrica_objetivo": _cfg["objetivo"]["metrica_principal"],
            "tiene_importancia_features": hasattr(modelo, "feature_importances_")
        }
