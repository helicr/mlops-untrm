# ============================================================
# Dockerfile — API de Predicción de Precios de Vivienda
# MLOps: Ciclo de Vida del Modelo
# ============================================================

FROM python:3.11-slim

# Metadatos
LABEL maintainer="Equipo MLOps"
LABEL description="API FastAPI para predicción de precios de vivienda (California Housing)"
LABEL version="1.0.0"

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente y la configuración
COPY src/ ./src/
COPY config/ ./config/

# Crear directorio para experimentos (modelo y logs de predicciones)
# Los archivos .pkl se montan como volumen en docker-compose
RUN mkdir -p experiments/

# Puerto de la API (debe coincidir con config.yaml: api.puerto)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Ejecutar la API
CMD ["uvicorn", "src.serving.api:app", "--host", "0.0.0.0", "--port", "8000"]
