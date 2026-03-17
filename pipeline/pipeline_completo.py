"""
============================================================
PIPELINE COMPLETO MLOps
============================================================
Este script orquesta todas las etapas del ciclo de vida MLOps
en el orden correcto.

Ejecutar:
  python pipeline/pipeline_completo.py
  python pipeline/pipeline_completo.py --solo-entrenamiento
  python pipeline/pipeline_completo.py --incluir-monitoreo

En producción, este pipeline sería ejecutado por:
  - Apache Airflow (DAGs)
  - Prefect / Metaflow
  - GitHub Actions / Jenkins (CI/CD)
  - Vertex AI Pipelines / SageMaker Pipelines
============================================================
"""

import sys
import time
import logging
import argparse
import yaml
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data.preparar_datos import ejecutar as etapa_datos
from src.features.ingenieria_features import ejecutar as etapa_features
from src.models.entrenar import entrenar as etapa_entrenamiento
from src.models.evaluar import evaluar as etapa_evaluacion
from src.monitoring.monitor import generar_reporte_monitoreo as etapa_monitoreo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


def cargar_config() -> dict:
    with open(ROOT / "config" / "config.yaml") as f:
        return yaml.safe_load(f)


def imprimir_separador(etapa: str, numero: int):
    log.info("")
    log.info("█" * 60)
    log.info("█  ETAPA %d: %-48s█", numero, etapa.upper())
    log.info("█" * 60)


def ejecutar_pipeline(incluir_monitoreo: bool = False):
    """
    Ejecuta el pipeline MLOps completo en secuencia.

    El orden importa:
      1. Datos → 2. Features → 3. Entrenamiento → 4. Evaluación
      → 5. [Despliegue manual o CI/CD] → 6. [Monitoreo]
    """
    cfg = cargar_config()
    inicio_total = time.time()
    resultados = {}

    log.info("")
    log.info("╔" + "═" * 58 + "╗")
    log.info("║       PIPELINE MLOps — CICLO DE VIDA COMPLETO           ║")
    log.info("║  Proyecto: %-46s║", cfg["proyecto"]["nombre"])
    log.info("║  Inicio:   %-46s║", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log.info("╚" + "═" * 58 + "╝")

    # ─── ETAPA 2: DATOS ───────────────────────────────────────────
    imprimir_separador("Preparación de Datos", 2)
    inicio = time.time()
    try:
        train_df, test_df = etapa_datos(cfg)
        resultados["datos"] = {
            "estado": "✅ OK",
            "tiempo_s": round(time.time() - inicio, 2),
            "n_train": len(train_df),
            "n_test": len(test_df)
        }
    except Exception as e:
        log.error("❌ Etapa de datos falló: %s", e)
        resultados["datos"] = {"estado": "❌ FALLIDO", "error": str(e)}
        imprimir_resumen(resultados)
        sys.exit(1)

    # ─── ETAPA 3: FEATURES ────────────────────────────────────────
    imprimir_separador("Ingeniería de Features", 3)
    inicio = time.time()
    try:
        train_df, test_df = etapa_features(train_df, test_df, cfg)
        resultados["features"] = {
            "estado": "✅ OK",
            "tiempo_s": round(time.time() - inicio, 2),
            "n_features": len(train_df.columns) - 1
        }
    except Exception as e:
        log.error("❌ Etapa de features falló: %s", e)
        resultados["features"] = {"estado": "❌ FALLIDO", "error": str(e)}
        imprimir_resumen(resultados)
        sys.exit(1)

    # ─── ETAPA 4: ENTRENAMIENTO ───────────────────────────────────
    imprimir_separador("Entrenamiento del Modelo", 4)
    inicio = time.time()
    try:
        modelo, metricas_train = etapa_entrenamiento(train_df, cfg)
        resultados["entrenamiento"] = {
            "estado": "✅ OK",
            "tiempo_s": round(time.time() - inicio, 2),
            "algoritmo": cfg["modelo"]["algoritmo"],
            "rmse_train": round(metricas_train["rmse"], 4),
            "r2_train": round(metricas_train["r2"], 4)
        }
    except Exception as e:
        log.error("❌ Etapa de entrenamiento falló: %s", e)
        resultados["entrenamiento"] = {"estado": "❌ FALLIDO", "error": str(e)}
        imprimir_resumen(resultados)
        sys.exit(1)

    # ─── ETAPA 5: EVALUACIÓN ──────────────────────────────────────
    imprimir_separador("Evaluación del Modelo", 5)
    inicio = time.time()
    try:
        reporte_eval = etapa_evaluacion(modelo, test_df, cfg)
        aprobado = reporte_eval["aprobado"]
        resultados["evaluacion"] = {
            "estado": "✅ APROBADO" if aprobado else "❌ RECHAZADO",
            "tiempo_s": round(time.time() - inicio, 2),
            "rmse_test": round(reporte_eval["metricas"]["rmse"], 4),
            "r2_test": round(reporte_eval["metricas"]["r2"], 4),
            "aprobado": aprobado
        }

        if not aprobado:
            log.error("❌ Modelo rechazado. El pipeline se detiene.")
            log.error("   Revisa los umbrales en config/config.yaml o mejora el modelo.")
            imprimir_resumen(resultados)
            sys.exit(1)

    except Exception as e:
        log.error("❌ Etapa de evaluación falló: %s", e)
        resultados["evaluacion"] = {"estado": "❌ FALLIDO", "error": str(e)}
        imprimir_resumen(resultados)
        sys.exit(1)

    # ─── ETAPA 6: DESPLIEGUE (informativo) ────────────────────────
    imprimir_separador("Despliegue", 6)
    log.info("  El modelo está APROBADO y listo para producción.")
    log.info("")
    log.info("  Para servir predicciones, ejecuta:")
    log.info("    uvicorn src.serving.api:app --reload --port 8000")
    log.info("")
    log.info("  Luego prueba con:")
    log.info('    curl -X POST "http://localhost:8000/v1/predecir" \\')
    log.info('      -H "Content-Type: application/json" \\')
    log.info('      -d \'{"MedInc":5.0,"HouseAge":20,"AveRooms":6.0,\'')
    log.info('           \'"AveBedrms":1.0,"Population":1000,\'')
    log.info('           \'"AveOccup":3.0,"Latitude":37.5,"Longitude":-122.0}\'')
    resultados["despliegue"] = {"estado": "⏸ LISTO (manual)", "tiempo_s": 0}

    # ─── ETAPA 7: MONITOREO (opcional) ────────────────────────────
    if incluir_monitoreo:
        imprimir_separador("Monitoreo", 7)
        inicio = time.time()
        try:
            reporte_mon = etapa_monitoreo(cfg)
            resultados["monitoreo"] = {
                "estado": "✅ OK",
                "tiempo_s": round(time.time() - inicio, 2),
                "data_drift": reporte_mon["data_drift"]["hay_drift"],
                "concept_drift": reporte_mon["concept_drift"]["hay_degradacion"],
                "requiere_reentrenamiento": reporte_mon["requiere_reentrenamiento"]
            }
        except Exception as e:
            log.warning("⚠️ Monitoreo falló (no crítico): %s", e)
            resultados["monitoreo"] = {"estado": "⚠️ ADVERTENCIA", "error": str(e)}

    # ─── RESUMEN FINAL ────────────────────────────────────────────
    tiempo_total = round(time.time() - inicio_total, 2)
    resultados["tiempo_total_s"] = tiempo_total
    imprimir_resumen(resultados)


def imprimir_resumen(resultados: dict):
    """Imprime un resumen visual del pipeline."""
    log.info("")
    log.info("╔" + "═" * 58 + "╗")
    log.info("║                  RESUMEN DEL PIPELINE                   ║")
    log.info("╠" + "═" * 58 + "╣")

    etapas = {
        "datos": "Preparación de Datos",
        "features": "Ingeniería de Features",
        "entrenamiento": "Entrenamiento",
        "evaluacion": "Evaluación",
        "despliegue": "Despliegue",
        "monitoreo": "Monitoreo"
    }

    for clave, nombre in etapas.items():
        if clave in resultados:
            r = resultados[clave]
            estado = r.get("estado", "—")
            tiempo = r.get("tiempo_s", 0)
            log.info("║  %-25s %-20s %5.1fs  ║", nombre, estado, tiempo)

    log.info("╠" + "═" * 58 + "╣")
    tiempo_total = resultados.get("tiempo_total_s", 0)
    log.info("║  %-25s %-20s %5.1fs  ║", "TOTAL", "", tiempo_total)
    log.info("╚" + "═" * 58 + "╝")
    log.info("")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline MLOps completo")
    parser.add_argument(
        "--incluir-monitoreo",
        action="store_true",
        help="Ejecutar también la etapa de monitoreo"
    )
    args = parser.parse_args()

    ejecutar_pipeline(incluir_monitoreo=args.incluir_monitoreo)
