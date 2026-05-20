"""
metricas.py - Módulo de cálculo de métricas para el sistema de despacho.
Lee los pedidos desde data/pedidos_simulados.json y calcula:
distancia, tiempo, penalización y Costo de Ruta.
"""

import json
import os
from dataclasses import dataclass

# ─── Constantes ───────────────────────────────────────────────────────────────
COSTO_POR_KM            = 2.5
PENALIZACION_TRAFICO    = {"bajo": 0.0, "medio": 5.0, "alto": 15.0}
PENALIZACION_BLOQUEADA  = 20.0
TIEMPO_LIMITE_MINUTOS   = 45.0
PENALIZACION_POR_MINUTO = 1.0


@dataclass
class ResultadoMetricas:
    id: int
    cliente: str
    distancia_km: float
    tiempo_minutos: float
    penalizacion: float
    costo_ruta: float
    dentro_de_tiempo: bool
    ruta_bloqueada: bool
    trafico: str
    detalle: str


def _ruta_json() -> str:
    base = os.path.dirname(__file__)
    return os.path.join(base, "..", "data", "pedidos_simulados.json")


def cargar_datos() -> dict:
    """Carga y devuelve el JSON completo (almacen + pedidos)."""
    with open(_ruta_json(), "r", encoding="utf-8") as f:
        return json.load(f)


def calcular_penalizacion(pedido: dict) -> float:
    tiempo    = pedido["tiempo_estimado_min"]
    trafico   = pedido.get("trafico", "bajo")
    bloqueada = pedido.get("ruta_bloqueada", False)

    pen_demora    = max(0.0, tiempo - TIEMPO_LIMITE_MINUTOS) * PENALIZACION_POR_MINUTO
    pen_trafico   = PENALIZACION_TRAFICO.get(trafico, 0.0)
    pen_bloqueada = PENALIZACION_BLOQUEADA if bloqueada else 0.0
    return round(pen_demora + pen_trafico + pen_bloqueada, 2)


def calcular_costo_ruta(distancia_km: float, penalizacion: float) -> float:
    """Costo de Ruta = (distancia_km × COSTO_POR_KM) + penalización"""
    return round(distancia_km * COSTO_POR_KM + penalizacion, 2)


def evaluar_pedido(pedido: dict) -> ResultadoMetricas:
    distancia = pedido["distancia_km"]
    tiempo    = pedido["tiempo_estimado_min"]
    penaliz   = calcular_penalizacion(pedido)
    costo     = calcular_costo_ruta(distancia, penaliz)
    en_tiempo = tiempo <= TIEMPO_LIMITE_MINUTOS
    bloqueada = pedido.get("ruta_bloqueada", False)
    trafico   = pedido.get("trafico", "bajo")

    partes = [
        f"Ruta: Almacén → {pedido['direccion']}",
        f"Distancia: {distancia} km",
        f"Tiempo: {tiempo} min",
        f"Tráfico: {trafico}",
        f"Ruta bloqueada: {'Sí' if bloqueada else 'No'}",
        f"{'✓ En tiempo' if en_tiempo else f'✗ Demora {round(tiempo - TIEMPO_LIMITE_MINUTOS, 1)} min'}",
    ]
    return ResultadoMetricas(
        id               = pedido["id"],
        cliente          = pedido["cliente_nombre"],
        distancia_km     = distancia,
        tiempo_minutos   = tiempo,
        penalizacion     = penaliz,
        costo_ruta       = costo,
        dentro_de_tiempo = en_tiempo,
        ruta_bloqueada   = bloqueada,
        trafico          = trafico,
        detalle          = " | ".join(partes),
    )


def simular_pedidos() -> list[dict]:
    """Devuelve lista de dicts con métricas calculadas, lista para la interfaz."""
    datos = cargar_datos()
    resultados = []
    for p in datos["pedidos"]:
        m = evaluar_pedido(p)
        resultados.append({
            "ID":                  m.id,
            "Cliente":             m.cliente,
            "Dirección":           p["direccion"],
            "Prioridad":           p["prioridad"].capitalize(),
            "Tráfico":             m.trafico.capitalize(),
            "Bloqueada":           "⚠ Sí" if m.ruta_bloqueada else "No",
            "Distancia (km)":      m.distancia_km,
            "Tiempo (min)":        m.tiempo_minutos,
            "Penalización (Bs.)":  m.penalizacion,
            "Costo de Ruta (Bs.)": m.costo_ruta,
            "En tiempo":           "✓ Sí" if m.dentro_de_tiempo else "✗ No",
            "_metricas":           m,
        })
    return resultados


def resumen_simulacion(pedidos: list[dict]) -> dict:
    """Métricas agregadas de toda la simulación."""
    costos     = [p["Costo de Ruta (Bs.)"] for p in pedidos]
    distancias = [p["Distancia (km)"]      for p in pedidos]
    tiempos    = [p["Tiempo (min)"]         for p in pedidos]
    penaliz    = [p["Penalización (Bs.)"]   for p in pedidos]
    en_tiempo  = sum(1 for p in pedidos if p["En tiempo"] == "✓ Sí")
    bloqueadas = sum(1 for p in pedidos if p["Bloqueada"] == "⚠ Sí")
    n = len(pedidos) or 1
    return {
        "total_pedidos":      len(pedidos),
        "costo_total":        round(sum(costos), 2),
        "costo_promedio":     round(sum(costos) / n, 2),
        "distancia_total":    round(sum(distancias), 2),
        "distancia_promedio": round(sum(distancias) / n, 2),
        "tiempo_promedio":    round(sum(tiempos) / n, 2),
        "penalizacion_total": round(sum(penaliz), 2),
        "pedidos_en_tiempo":  en_tiempo,
        "pedidos_con_demora": len(pedidos) - en_tiempo,
        "rutas_bloqueadas":   bloqueadas,
        "tasa_cumplimiento":  round(en_tiempo / n * 100, 1),
    }