# Guía de Ejecución Paso a Paso — MLOps Ciclo de Vida

Esta guía muestra cómo ejecutar el proyecto **sin notebooks**, lanzando cada etapa del pipeline
de forma individual para entender qué hace cada script y qué produce.

> **Requisito previo:** tener el entorno conda creado e instalado.
> ```bash
> conda activate mlops-ciclo-vida
> cd C:\Users\bk70827\PycharmProjects\mlops-ciclo-vida
> ```

---

## Visión general del flujo

```
  FUENTE DE DATOS
 ┌──────────────┐
 │  sklearn     │
 │  California  │
 │  Housing     │
 └──────┬───────┘
        │ fetch_california_housing()
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  ETAPA 2 · preparar_datos.py                                              │
│                                                                           │
│  Ingestión → Validación → Limpieza → Split 80/20                         │
│                                                                           │
│  Genera: housing_raw.csv  │  train.csv  │  test.csv                       │
└───────────────────────────┬───────────────────────────────────────────────┘
                            │ train.csv + test.csv
                            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  ETAPA 3 · ingenieria_features.py                                         │
│                                                                           │
│  8 features originales  →  +5 features derivadas  →  StandardScaler       │
│  rooms_per_person · income_per_room · bedroom_ratio · dist_sac · dist_la  │
│                                 ⚠ fit() solo en TRAIN                     │
│  Genera: train.csv (13 cols) │  test.csv (13 cols) │  scaler.pkl           │
└───────────────────────────┬───────────────────────────────────────────────┘
                            │ train.csv escalado
                            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  ETAPA 4 · entrenar.py                                                    │
│                                                                           │
│  GradientBoostingRegressor  →  MLflow tracking  →  Feature Importance    │
│  (hiperparámetros desde config/config.yaml)                               │
│                                                                           │
│  Genera: modelo_produccion.pkl │  run en MLflow                           │
└───────────────────────────┬───────────────────────────────────────────────┘
                            │ modelo_produccion.pkl
                            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  ETAPA 5 · evaluar.py                                                     │
│                                                                           │
│  Predicciones en TEST SET  →  RMSE · MAE · R²  →  Gate de Calidad        │
│                                                                           │
│        ┌──────────────────────┐     ┌──────────────────────┐             │
│        │  RMSE < 0.50  ✓ ?   │     │   R²  > 0.80  ✓ ?   │             │
│        └──────────┬───────────┘     └──────────┬───────────┘             │
│                   │  ambas condiciones          │                         │
│            ┌──────┴─────────────────────────────┴──────┐                 │
│            │  APROBADO → continúa el pipeline          │                 │
│            │  RECHAZADO → error, pipeline se detiene   │                 │
│            └───────────────────────────────────────────┘                 │
│  Genera: reporte_evaluacion.json                                          │
└───────────────────────────┬───────────────────────────────────────────────┘
                            │ modelo aprobado
                            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  ETAPA 6 · api.py  (uvicorn)                                              │
│                                                                           │
│  Carga modelo_produccion.pkl + scaler.pkl                                 │
│                                                                           │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────────┐    │
│  │  GET  /         │  │  POST /v1/predecir│  │  GET  /ui            │    │
│  │  health check   │  │  8 campos JSON   │  │  Web UI negocio      │    │
│  └─────────────────┘  └──────────────────┘  └──────────────────────┘    │
│                                │                                          │
│                    ┌───────────┘                                          │
│                    │ aplica mismas transformaciones que Etapa 3           │
│                    │ (training-serving parity)                            │
│                    ▼                                                      │
│           precio estimado en USD                                          │
│           log → predicciones_produccion.jsonl                             │
└───────────────────────────┬───────────────────────────────────────────────┘
                            │ predicciones_produccion.jsonl
                            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  ETAPA 7 · monitor.py                                                     │
│                                                                           │
│  Data Drift (PSI por feature)       Concept Drift (RMSE degradación)      │
│  ┌────────────────────────────┐     ┌──────────────────────────────────┐  │
│  │ PSI < 0.10  → 🟢 Sin cambio│     │ RMSE subió < 10%  → 🟢 Estable  │  │
│  │ PSI < 0.20  → 🟡 Moderado  │     │ RMSE subió > 10%  → 🔴 Degradado│  │
│  │ PSI ≥ 0.20  → 🔴 Drift     │     └──────────────────────────────────┘  │
│  └────────────────────────────┘                                           │
│                                                                           │
│  Genera: reporte_monitoreo.json                                           │
└───────────────────────────┬───────────────────────────────────────────────┘
                            │ ¿requiere re-entrenamiento?
                            ▼
                  ┌─────────────────────┐
                  │  SÍ → volver a      │
                  │  Etapa 2 (nuevo     │
                  │  ciclo MLOps)       │
                  │                     │
                  │  NO → modelo        │
                  │  sigue en producción│
                  └─────────────────────┘
```

Cada número corresponde a la etapa del ciclo MLOps definida en el proyecto.

---

## Etapa 2 — Preparación de Datos

```bash
python src/data/preparar_datos.py
```

**¿Qué hace?**
- Descarga el dataset California Housing desde `sklearn`
- Valida que no haya nulos, duplicados ni columnas faltantes
- Elimina outliers extremos (Z-score > 3.0) — elimina ~4% de filas
- Divide en train (80%) y test (20%) con semilla fija para reproducibilidad

**Archivos generados:**
```
data/
├── raw/
│   └── housing_raw.csv          ← 20,640 filas originales (nunca modificar)
└── processed/
    ├── housing_procesado.csv    ← dataset limpio completo
    ├── train.csv                ← 15,835 filas para entrenar
    └── test.csv                 ← 3,959 filas para evaluar
```

**Conceptos clave:** ingestión, validación, data quality, reproducibilidad.

---

## Etapa 3 — Ingeniería de Features

```bash
python src/features/ingenieria_features.py
```

**¿Qué hace?**
- Crea 5 nuevas variables derivadas a partir de las 8 originales:
  - `rooms_per_person` — densidad habitacional
  - `income_per_room` — poder adquisitivo por espacio
  - `bedroom_ratio` — proporción de dormitorios
  - `dist_sacramento` — distancia a la capital
  - `dist_los_angeles` — distancia al mayor mercado
- Ajusta un `StandardScaler` **solo** con train (evita data leakage)
- Aplica la transformación a train y test por separado
- Guarda el scaler para usarlo en producción (training-serving parity)

**Archivos generados / actualizados:**
```
data/processed/
├── train.csv          ← ahora con 13 columnas (8 orig + 5 nuevas), escaladas
└── test.csv           ← misma transformación aplicada
experiments/
└── scaler.pkl         ← StandardScaler entrenado (se usará en la API)
```

**Conceptos clave:** feature engineering, data leakage, training-serving parity.

---

## Etapa 4 — Entrenamiento del Modelo

```bash
python src/models/entrenar.py
```

**¿Qué hace?**
- Lee el algoritmo e hiperparámetros desde `config/config.yaml`
- Entrena un `GradientBoostingRegressor` con los datos de train
- Registra el experimento en MLflow (parámetros + métricas + artefacto)
- Muestra las 5 features más importantes del modelo
- Guarda el modelo entrenado como archivo `.pkl`

**Archivos generados:**
```
experiments/
├── modelo_produccion.pkl    ← modelo entrenado listo para predecir
└── <mlflow_run_id>/         ← registro del experimento en MLflow
```

**Conceptos clave:** tracking de experimentos, reproducibilidad, feature importance.

---

## (Opcional) Ver experimentos en MLflow UI

> Abrir una **segunda terminal** con el entorno activado:

```bash
mlflow ui --backend-store-uri experiments/
```

Acceder en el navegador: **http://localhost:5000**

Permite comparar runs, ver métricas, descargar artefactos y comparar experimentos visualmente.

---

## Etapa 5 — Evaluación del Modelo

```bash
python src/models/evaluar.py
```

**¿Qué hace?**
- Carga el modelo guardado y lo evalúa en el conjunto de **test** (datos nunca vistos)
- Verifica el **gate de calidad** definido en `config/config.yaml`:
  - RMSE < 0.5 ✓
  - R² > 0.80 ✓
- Si el modelo **no aprueba** → sale con código de error 1 (detiene el CI/CD)
- Analiza los residuos (media, std, percentil 90)
- Guarda el reporte de evaluación

**Archivos generados:**
```
experiments/
└── reporte_evaluacion.json    ← métricas, resultado aprobado/rechazado
```

**Conceptos clave:** gate de calidad, evaluación en test set, CI/CD gate.

---

## Etapa 6 — Serving: API REST

> Abrir una **segunda terminal** con el entorno activado:

```bash
uvicorn src.serving.api:app --reload --port 8000
```

**¿Qué hace?**
- Carga el modelo (`modelo_produccion.pkl`) y el scaler (`scaler.pkl`) en memoria
- Expone tres interfaces:

| URL | Descripción |
|-----|-------------|
| http://localhost:8000/ | Health check |
| http://localhost:8000/ui | Web UI para usuarios de negocio |
| http://localhost:8000/docs | Swagger — documentación interactiva |
| http://localhost:8000/v1/predecir | Endpoint de predicción (POST) |
| http://localhost:8000/v1/info-modelo | Información del modelo en producción |

**Probar la API desde otra terminal:**
```bash
curl -X POST "http://localhost:8000/v1/predecir" ^
  -H "Content-Type: application/json" ^
  -d "{\"MedInc\": 5.0, \"HouseAge\": 20, \"AveRooms\": 6.0, \"AveBedrms\": 1.0, \"Population\": 1000, \"AveOccup\": 3.0, \"Latitude\": 37.5, \"Longitude\": -122.0}"
```

**Respuesta esperada:**
```json
{
  "prediccion_normalizada": 2.87,
  "precio_estimado_usd": 287000.0,
  "unidad": "USD"
}
```

**Conceptos clave:** API REST, FastAPI, Pydantic, training-serving parity, logging de predicciones.

---

## Etapa 7 — Monitoreo

```bash
python src/monitoring/monitor.py
```

**¿Qué hace?**
- **Data Drift:** calcula el PSI (Population Stability Index) por feature comparando
  los datos de entrenamiento con los datos recientes de producción
  - PSI < 0.10 → sin cambio (verde)
  - PSI < 0.20 → cambio moderado (amarillo)
  - PSI ≥ 0.20 → drift significativo → re-entrenar (rojo)
- **Concept Drift:** compara el RMSE actual con el RMSE del entrenamiento;
  si sube más de un 10% → alerta de degradación
- Decide si se requiere re-entrenamiento

**Archivos generados:**
```
experiments/
└── reporte_monitoreo.json    ← resultado del análisis de drift
```

**Conceptos clave:** data drift, concept drift, PSI, ciclo de re-entrenamiento.

---

## Pipeline completo (alternativa)

Si quieres ejecutar todas las etapas de una sola vez:

```bash
# Solo entrenamiento (etapas 2 → 5)
python pipeline/pipeline_completo.py

# Con monitoreo incluido (etapas 2 → 7)
python pipeline/pipeline_completo.py --incluir-monitoreo
```

---

## Tests

Verificar que el código y el modelo cumplen los criterios de calidad:

```bash
pytest tests/ -v
```

| Test | Qué verifica |
|------|-------------|
| `test_ingestion_retorna_dataframe` | Los datos se cargan correctamente |
| `test_dataset_no_vacio` | El dataset tiene filas |
| `test_columnas_esperadas_presentes` | Las features existen |
| `test_validacion_pasa_con_datos_correctos` | La validación aprueba datos buenos |
| `test_validacion_falla_con_*` | La validación rechaza datos malos |
| `test_limpieza_*` | La limpieza funciona correctamente |
| `test_modelo_genera_predicciones` | El modelo predice sin errores |
| `test_modelo_cumple_umbral_rmse` | RMSE < 0.5 |
| `test_modelo_cumple_umbral_r2` | R² > 0.80 |
| `test_crear_features_agrega_columnas` | Feature engineering añade columnas |
| `test_features_no_contienen_nan` | Las nuevas features no generan NaN |

---

## Resumen de archivos por etapa

```
mlops-ciclo-vida/
├── data/raw/housing_raw.csv              ← Etapa 2
├── data/processed/train.csv             ← Etapas 2 y 3
├── data/processed/test.csv              ← Etapas 2 y 3
├── experiments/scaler.pkl               ← Etapa 3
├── experiments/modelo_produccion.pkl    ← Etapa 4
├── experiments/reporte_evaluacion.json  ← Etapa 5
└── experiments/reporte_monitoreo.json   ← Etapa 7
```