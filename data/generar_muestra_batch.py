"""
Genera un CSV de muestra para demostrar la inferencia batch.
Ejecutar: python data/generar_muestra_batch.py
"""
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
np.random.seed(42)

viviendas = pd.DataFrame([
    {"MedInc": 8.50, "HouseAge": 15, "AveRooms": 6.5, "AveBedrms": 1.1, "Population": 1200, "AveOccup": 2.8, "Latitude": 37.78, "Longitude": -122.42},
    {"MedInc": 6.20, "HouseAge": 25, "AveRooms": 5.8, "AveBedrms": 1.2, "Population": 1800, "AveOccup": 3.1, "Latitude": 34.05, "Longitude": -118.25},
    {"MedInc": 4.80, "HouseAge": 20, "AveRooms": 5.2, "AveBedrms": 1.1, "Population": 2200, "AveOccup": 3.4, "Latitude": 32.72, "Longitude": -117.15},
    {"MedInc": 3.50, "HouseAge": 35, "AveRooms": 4.8, "AveBedrms": 1.0, "Population": 3100, "AveOccup": 3.8, "Latitude": 38.58, "Longitude": -121.49},
    {"MedInc": 2.10, "HouseAge": 40, "AveRooms": 4.2, "AveBedrms": 1.1, "Population": 2800, "AveOccup": 4.1, "Latitude": 36.74, "Longitude": -119.77},
    {"MedInc": 9.20, "HouseAge": 10, "AveRooms": 7.1, "AveBedrms": 1.0, "Population":  950, "AveOccup": 2.5, "Latitude": 37.45, "Longitude": -122.18},
    {"MedInc": 5.60, "HouseAge": 30, "AveRooms": 5.5, "AveBedrms": 1.2, "Population": 1600, "AveOccup": 3.2, "Latitude": 33.99, "Longitude": -118.47},
    {"MedInc": 1.80, "HouseAge": 50, "AveRooms": 3.9, "AveBedrms": 1.0, "Population": 4200, "AveOccup": 5.1, "Latitude": 37.33, "Longitude": -121.89},
    {"MedInc": 7.30, "HouseAge": 18, "AveRooms": 6.2, "AveBedrms": 1.1, "Population": 1100, "AveOccup": 2.9, "Latitude": 37.88, "Longitude": -122.27},
    {"MedInc": 3.90, "HouseAge": 28, "AveRooms": 4.9, "AveBedrms": 1.0, "Population": 2500, "AveOccup": 3.6, "Latitude": 34.42, "Longitude": -119.70},
])

ruta = ROOT / "data" / "nuevas_viviendas.csv"
viviendas.to_csv(ruta, index=False)
print(f"Fichero generado: {ruta}")
print(f"Registros: {len(viviendas)}")
print(viviendas.to_string(index=False))
