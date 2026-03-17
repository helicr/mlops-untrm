# ============================================================
# Makefile — Comandos de utilidad del proyecto MLOps
# Uso: make <comando>
# ============================================================

.PHONY: instalar pipeline pipeline-completo entrenar evaluar api tests limpiar

# Instalar todas las dependencias
instalar:
	pip install -r requirements.txt

# Ejecutar el pipeline completo (sin monitoreo)
pipeline:
	python pipeline/pipeline_completo.py

# Ejecutar el pipeline completo CON monitoreo
pipeline-completo:
	python pipeline/pipeline_completo.py --incluir-monitoreo

# Ejecutar etapas individuales
datos:
	python src/data/preparar_datos.py

features:
	python src/features/ingenieria_features.py

entrenar:
	python src/models/entrenar.py

evaluar:
	python src/models/evaluar.py

monitoreo:
	python src/monitoring/monitor.py

# Levantar la API de predicción
api:
	uvicorn src.serving.api:app --reload --host 0.0.0.0 --port 8000

# Ejecutar pruebas
tests:
	pytest tests/ -v

tests-cobertura:
	pytest tests/ -v --cov=src --cov-report=html

# Ver experimentos en MLflow UI
mlflow-ui:
	mlflow ui --backend-store-uri experiments/ --port 5000

# Limpiar artefactos generados
limpiar:
	rm -rf data/processed/*.csv
	rm -rf data/raw/*.csv
	rm -rf experiments/*.pkl
	rm -rf experiments/*.json
	rm -rf experiments/*.jsonl
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
