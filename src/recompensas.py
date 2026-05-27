"""
recompensas.py
 
Calcula el costo de ruta y la recompensa del agente.
 
CAMBIO PRINCIPAL: calcular_costo_ruta ahora acepta pos_actual_coords (lat, lng).
Si se pasa, usa la distancia real desde la posicion actual al cliente.
Si no se pasa, usa distancia_km del JSON (compatibilidad con codigo anterior).
 
Esto es lo que permite que el agente aprenda el orden optimo:
antes, la recompensa era siempre la misma sin importar el orden de entregas.
"""
 
import math
from typing import Dict, Optional, Tuple
 
 
# ─── Constantes de penalizacion ───────────────────────────────────────────────
 
PEN_TRAFICO_ALTO   =  5.0
PEN_TRAFICO_MEDIO  =  2.0
PEN_RUTA_BLOQUEADA = 10.0
PEN_PRIORIDAD_BAJA =  2.0
BON_PRIORIDAD_ALTA = -3.0   # bonificacion: reduce el costo
 
 
# ─── Distancia entre coordenadas ──────────────────────────────────────────────
 
def calcular_distancia_coordenadas(
    pos_actual: Tuple[float, float],
    coord_destino: Dict
) -> float:
    """
    Distancia en km entre la posicion actual y el destino.
    Usa aproximacion plana (suficiente para distancias urbanas < 50 km).
 
    pos_actual: (lat, lng) del agente en este momento
    coord_destino: dict con claves 'lat' y 'lng'
    """
    lat1, lng1 = pos_actual
    lat2 = coord_destino.get("lat", lat1)
    lng2 = coord_destino.get("lng", lng1)
 
    dlat = (lat2 - lat1) * 111.0
    dlng = (lng2 - lng1) * 111.0 * math.cos(math.radians((lat1 + lat2) / 2.0))
 
    return math.sqrt(dlat ** 2 + dlng ** 2)
 
 
# ─── Costo de ruta ────────────────────────────────────────────────────────────
 
def calcular_costo_ruta(
    pedido: Dict,
    pos_actual_coords: Optional[Tuple[float, float]] = None
) -> float:
    """
    CR = distancia + (tiempo / 10) + penalizaciones
 
    pos_actual_coords: (lat, lng) de donde esta el agente AHORA.
    Si se pasa, la distancia es desde esa posicion al cliente.
    Si no se pasa, usa distancia_km del JSON (desde el almacen).
    """
    if pos_actual_coords is not None:
        coord_destino = pedido.get("coordenadas", {})
        distancia = calcular_distancia_coordenadas(pos_actual_coords, coord_destino)
    else:
        distancia = pedido.get("distancia_km", pedido.get("distancia", 0))
 
    tiempo    = pedido.get("tiempo_estimado_min", pedido.get("tiempo", 0))
    trafico   = pedido.get("trafico", "bajo").lower()
    bloqueada = pedido.get("ruta_bloqueada", False)
    prioridad = pedido.get("prioridad", "media").lower()
 
    penalizaciones = 0.0
 
    if trafico == "alto":
        penalizaciones += PEN_TRAFICO_ALTO
    elif trafico == "medio":
        penalizaciones += PEN_TRAFICO_MEDIO
 
    if bloqueada:
        penalizaciones += PEN_RUTA_BLOQUEADA
 
    if prioridad == "alta":
        penalizaciones += BON_PRIORIDAD_ALTA
    elif prioridad == "baja":
        penalizaciones += PEN_PRIORIDAD_BAJA
 
    return distancia + (tiempo / 10.0) + penalizaciones
 
 
# ─── Recompensa ───────────────────────────────────────────────────────────────
 
def calcular_recompensa(
    pedido: Dict,
    entregado_exitosamente: bool,
    pos_actual_coords: Optional[Tuple[float, float]] = None
) -> float:
    """
    Entrega exitosa : R = 100 - CR
    Entrega fallida : R = -CR
    """
    cr = calcular_costo_ruta(pedido, pos_actual_coords=pos_actual_coords)
    return (100.0 - cr) if entregado_exitosamente else -cr