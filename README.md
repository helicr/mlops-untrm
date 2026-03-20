# MLOps: Ciclo de Vida de un Modelo de Ciencia de Datos

Proyecto educativo que demuestra el ciclo de vida completo de un modelo de Machine Learning
usando prácticas MLOps, con un ejemplo práctico de **predicción del precio de viviendas en California**.

---

## ¿Qué es MLOps?

MLOps (Machine Learning Operations) combina ML, DevOps e Ingeniería de Datos para desplegar
y mantener modelos en producción de forma confiable, reproducible y automatizada.

---

## El Ciclo de Vida MLOps

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       CICLO DE VIDA MLOps                               │
│                                                                         │
│   1. Definición    2. Datos       3. Features     4. Entrenamiento      │
│   del Problema  →  Preparación  → Ingeniería   →  del Modelo           │
│        ↑                                               ↓                │
│        │                                               │                │
│   7. Monitoreo  ←  6. Despliegue  ←  5. Evaluación  ←┘                │
│        │                                                                │
│        └──────────── Re-entrenamiento (si drift) ────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Notebooks (00 – 13)

El proyecto está estructurado en 14 notebooks que cubren el flujo end-to-end:

| Notebook | Tema | Contenido principal |
|----------|------|---------------------|
| `00_introduccion.ipynb` | Introducción | Visión general, dataset y stack tecnológico |
| `01_eda_exploratorio.ipynb` | EDA | Calidad de datos, correlaciones, distribución geográfica |
| `02_ingenieria_features.ipynb` | Feature Engineering | 5 features derivadas, data leakage, StandardScaler |
| `03_entrenamiento_mlflow.ipynb` | Entrenamiento | 3 modelos con tracking de experimentos en MLflow |
| `04_seleccion_modelo.ipynb` | Selección | Cross-Validation 5-fold, bias-variance, curvas de aprendizaje |
| `05_evaluacion_final.ipynb` | Evaluación | Gate de calidad + MLflow Model Registry |
| `06_despliegue_api.ipynb` | Despliegue | Docker + FastAPI + Web UI + Swagger |
| `07_monitoreo_reentrenamiento.ipynb` | Monitoreo | PSI, drift, GitHub Actions, ciclo completo |
| `08_automl.ipynb` | AutoML | Optuna — búsqueda automática de hiperparámetros (TPE) |
| `09_explicabilidad_shap.ipynb` | Explicabilidad | SHAP values, beeswarm, dependence plots, waterfall |
| `10_validacion_datos.ipynb` | Validación | Pandera — schema contracts y detección de errores |
| `11_ab_testing.ipynb` | A/B Testing | Prueba controlada Modelo A vs B, análisis estadístico, aprobación manual |
| `12_model_card.ipynb` | Model Card | Documentación estructurada: métricas por subgrupo, limitaciones, ética |
| `13_inferencia_batch.ipynb` | Inferencia Batch | Predicciones masivas programadas, throughput, scheduling, trazabilidad |

**Criterios de calidad del modelo:** RMSE < 0.5 | R² > 0.80

---

## Stack Tecnológico

| Área | Herramientas |
|------|-------------|
| Datos y Modelos | scikit-learn, pandas, numpy |
| Tracking | MLflow (experimentos + Model Registry) |
| AutoML | Optuna (TPE sampler) |
| Explicabilidad | SHAP (TreeExplainer) |
| Validación de datos | Pandera (schema contracts) |
| Serving | FastAPI + uvicorn + Docker |
| CI/CD | GitHub Actions (4 jobs: CI, monitoreo, train/eval, deploy) |
| Calidad de código | pytest + flake8 |
| Registro de imágenes | GitHub Container Registry (GHCR) |

---

## Estructura del Proyecto

```
mlops-ciclo-vida/
├── config/
│   └── config.yaml                  # Parámetros centralizados
├── data/
│   ├── raw/                         # Datos originales (housing_raw.csv)
│   └── processed/                   # train.csv y test.csv tras el split
├── notebooks/                       # Notebooks 00–13 (flujo completo)
├── src/
│   ├── data/preparar_datos.py       # Etapa 2: Ingestión y limpieza
│   ├── features/ingenieria_features.py  # Etapa 3: Feature engineering
│   ├── models/entrenar.py           # Etapa 4: Entrenamiento
│   ├── models/evaluar.py            # Etapa 5: Evaluación
│   ├── serving/api.py               # Etapa 6: API REST de predicción
│   └── monitoring/monitor.py        # Etapa 7: Monitoreo y drift
├── pipeline/
│   └── pipeline_completo.py         # Orquesta todo el flujo
├── tests/
│   ├── test_datos.py
│   └── test_modelo.py
├── experiments/                     # Artefactos MLflow (modelo.pkl, scaler.pkl)
├── .github/workflows/
│   └── ci_cd.yaml                   # Pipeline CI/CD automatizado
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── Makefile
```

---

## Instalación

```bash
# Crear entorno conda
conda create -n mlops-ciclo-vida python=3.11
conda activate mlops-ciclo-vida

# Instalar dependencias
pip install -r requirements.txt

# Registrar kernel de Jupyter
python -m ipykernel install --user --name mlops-ciclo-vida
```

---

## Uso

### Ejecutar el pipeline completo

```bash
python pipeline/pipeline_completo.py
```

### Ejecutar etapas individuales

```bash
python src/data/preparar_datos.py
python src/features/ingenieria_features.py
python src/models/entrenar.py
python src/models/evaluar.py
```

### Levantar la API de predicción

```bash
# Con Docker (recomendado)
docker-compose up

# Sin Docker
uvicorn src.serving.api:app --reload
# API:     http://localhost:8000
# Web UI:  http://localhost:8000/ui
# Docs:    http://localhost:8000/docs
```

### Ver experimentos en MLflow UI

```bash
mlflow ui --backend-store-uri experiments/
# http://localhost:5000
```

### Ejecutar pruebas

```bash
pytest tests/ -v
```

---

## CI/CD — GitHub Actions

El pipeline (`.github/workflows/ci_cd.yaml`) se activa en push a `develop`/`master`,
PR a `master` y cron semanal (lunes 2am UTC):

| Job | Cuándo | Qué hace |
|-----|--------|----------|
| `ci` | Siempre | pytest + flake8 |
| `monitoreo` | Solo cron | Detección de drift (PSI) |
| `entrenar-evaluar` | master / PR / cron | Entrena, evalúa y valida gate RMSE/R² |
| `despliegue` | Solo push a master | Docker build + push a GHCR |

Imagen Docker publicada en: `ghcr.io/helicr/mlops-api-viviendas:latest`

---

## Generación de Presentaciones

Los scripts de `pdfs-ppts/` generan las presentaciones PowerPoint del curso.
Ejecutar **en este orden** desde la raíz del proyecto:

```bash
# Paso 1 — Ejecutar todos los notebooks y guardar sus outputs
python pdfs-ppts/ejecutar_notebooks.py

# Paso 2 — Generar gráficos matplotlib y extraer screenshots de notebooks
python pdfs-ppts/capturar_imagenes.py

# Paso 3 — Generar el PPT final (~65 slides)
python pdfs-ppts/generar_ppt_notebooks.py
# Salida: pdfs-ppts/output/mlops_ejemplo_notebooks.pptx
```

> Los scripts `crear_nb*.py` y `fix_*.py` son de uso único (ya ejecutados).
> No volver a ejecutarlos salvo que se necesite regenerar los notebooks desde cero.

---

## Dataset

**California Housing** (sklearn.datasets.fetch_california_housing)
- 20,640 muestras del censo de California (1990)
- 8 features originales → 13 tras feature engineering
- Target: precio mediano de la vivienda en bloques censales ($100K)
- Sin valores nulos ni duplicados

---

## Conceptos Clave

- **Reproducibilidad:** cada experimento queda registrado con parámetros, métricas y artefactos en MLflow
- **Data Leakage:** el scaler se ajusta solo en train y se aplica en test/producción
- **Training-Serving Parity:** `scaler.pkl` serializado garantiza la misma transformación en producción
- **Model Registry:** versionado y aprobación formal antes de promover a producción
- **PSI (Population Stability Index):** detecta data drift; PSI > 0.2 dispara re-entrenamiento
- **Gate de Calidad:** RMSE < 0.5 y R² > 0.80 como condición para el despliegue automático