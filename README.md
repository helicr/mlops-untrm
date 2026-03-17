# MLOps: Ciclo de Vida de un Modelo de Ciencia de Datos

Este proyecto demuestra el ciclo de vida completo de un modelo de Machine Learning usando MLOps,
con un ejemplo práctico de **predicción del precio de viviendas**.

---

## ¿Qué es MLOps?

MLOps (Machine Learning Operations) es un conjunto de prácticas que combina ML, DevOps e Ingeniería
de Datos para desplegar y mantener modelos de ML en producción de forma confiable y eficiente.

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

### Etapas del Ciclo

| Etapa | Descripción | Archivo clave |
|-------|-------------|---------------|
| 1. Problema | Definir objetivo, métricas y criterios de éxito | `config/config.yaml` |
| 2. Datos | Ingestión, validación y limpieza | `src/data/preparar_datos.py` |
| 3. Features | Transformaciones y creación de variables | `src/features/ingenieria_features.py` |
| 4. Entrenamiento | Experimentación y selección de modelo | `src/models/entrenar.py` |
| 5. Evaluación | Validación de métricas y aprobación | `src/models/evaluar.py` |
| 6. Despliegue | API REST para servir predicciones | `src/serving/api.py` |
| 7. Monitoreo | Detección de drift y alertas | `src/monitoring/monitor.py` |
| Pipeline | Orquesta todo el flujo | `pipeline/pipeline_completo.py` |

---

## Estructura del Proyecto

```
mlops-ciclo-vida/
├── config/
│   └── config.yaml              # Parámetros centralizados del proyecto
├── data/
│   ├── raw/                     # Datos originales (no modificar)
│   └── processed/               # Datos limpios y transformados
├── src/
│   ├── data/
│   │   └── preparar_datos.py    # Etapa 2: Ingestión y limpieza
│   ├── features/
│   │   └── ingenieria_features.py  # Etapa 3: Feature engineering
│   ├── models/
│   │   ├── entrenar.py          # Etapa 4: Entrenamiento
│   │   └── evaluar.py           # Etapa 5: Evaluación
│   ├── serving/
│   │   └── api.py               # Etapa 6: API de predicción
│   └── monitoring/
│       └── monitor.py           # Etapa 7: Monitoreo
├── tests/
│   ├── test_datos.py            # Pruebas de calidad de datos
│   └── test_modelo.py           # Pruebas del modelo
├── pipeline/
│   └── pipeline_completo.py    # Orquestador del ciclo completo
├── experiments/                 # Logs de experimentos MLflow
├── .github/workflows/
│   └── ci_cd.yaml               # Pipeline CI/CD
├── requirements.txt
└── Makefile                     # Comandos de utilidad
```

---

## Instalación y Uso

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar el pipeline completo (todas las etapas)
python pipeline/pipeline_completo.py

# 3. Ejecutar etapas individuales
python src/data/preparar_datos.py
python src/features/ingenieria_features.py
python src/models/entrenar.py
python src/models/evaluar.py

# 4. Levantar la API de predicción
uvicorn src.serving.api:app --reload

# 5. Correr pruebas
pytest tests/ -v

# 6. Ver experimentos en MLflow UI
mlflow ui --backend-store-uri experiments/
```

---

## Ejemplo Práctico: Predicción de Precio de Viviendas

**Dataset:** California Housing (sklearn)
**Objetivo:** Predecir el precio mediano de viviendas en bloques de California
**Métrica principal:** RMSE (Root Mean Squared Error)
**Criterio de éxito:** RMSE < 0.5 (escala normalizada) | R² > 0.80

---

## Conceptos Clave de MLOps

- **Reproducibilidad:** Cada experimento queda registrado con parámetros, métricas y artefactos
- **Versionado:** Datos, código y modelos tienen versiones
- **Automatización:** El pipeline puede ejecutarse sin intervención manual
- **Monitoreo:** Se detecta cuando el modelo degrada (data drift / concept drift)
- **Re-entrenamiento:** El ciclo se reinicia automáticamente si se detecta degradación
