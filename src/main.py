"""
main.py - Conecta entorno + agente + recompensas + Q-Learning y ejecuta la simulación.
"""

import json
from pathlib import Path

from src.agente import AgenteDelivery
from src.qlearning import QLearningDelivery
from src.recompensas import calcular_costo_ruta, calcular_recompensa

BASE_DIR     = Path(__file__).resolve().parent.parent
RUTA_DATASET = BASE_DIR / "data" / "pedidos_simulados.json"


# ─── Carga de pedidos ─────────────────────────────────────────────────────────

def cargar_pedidos() -> list[dict]:
    """
    Carga pedidos desde data/pedidos_simulados.json.
    Normaliza los campos al formato que usan agente.py y qlearning.py:
      id_pedido, destino, distancia, tiempo, trafico, prioridad, estado_ruta
    """
    try:
        with open(RUTA_DATASET, "r", encoding="utf-8") as f:
            datos = json.load(f)

        pedidos_raw = datos.get("pedidos", datos) if isinstance(datos, dict) else datos

        normalizados = []
        for p in pedidos_raw:
            normalizados.append({
                # campos que usan agente.py / qlearning.py
                "id_pedido":   p.get("id_pedido", p.get("id")),
                "destino":     p.get("destino", p.get("cliente_nombre", "Desconocido")),
                "distancia":   p.get("distancia", p.get("distancia_km", 0)),
                "tiempo":      p.get("tiempo", p.get("tiempo_estimado_min", 0)),
                "trafico":     p.get("trafico", "bajo"),
                "prioridad":   p.get("prioridad", "media"),

                # NUEVO
                "estado":      p.get("estado", "pendiente"),

                "estado_ruta": "bloqueada" if p.get("ruta_bloqueada", False) else "libre",

                # campos originales del JSON (para recompensas.py)
                "distancia_km":        p.get("distancia_km", p.get("distancia", 0)),
                "tiempo_estimado_min": p.get("tiempo_estimado_min", p.get("tiempo", 0)),
                "ruta_bloqueada":      p.get("ruta_bloqueada", False),
            })

        return normalizados

    except (FileNotFoundError, json.JSONDecodeError):
        return []


def obtener_id_pedido(pedido: dict):
    return pedido.get("id_pedido", pedido.get("id"))


def buscar_pedido_por_id(pedidos: list[dict], id_pedido) -> dict | None:
    for p in pedidos:
        if obtener_id_pedido(p) == id_pedido:
            return p
    return None


# ─── Simulación ───────────────────────────────────────────────────────────────

def ejecutar_simulacion_beta(episodios: int = 3) -> dict:
    """
    Ejecuta la simulación Q-Learning usando los pedidos reales del JSON.

    Flujo por episodio:
      estado → acción → recompensa → nuevo estado → actualizar Tabla Q
    """

    qlearning = QLearningDelivery(alpha=0.1, gamma=0.9, epsilon=0.3)
    resultados = []

    for numero_episodio in range(1, episodios + 1):

        pedidos_pendientes = cargar_pedidos()
        agente = AgenteDelivery(posicion_inicial="almacen")

        ruta = []
        recompensa_total = 0.0
        costo_total = 0.0

        while pedidos_pendientes:

            estado = agente.obtener_estado(pedidos_pendientes)
            clave_estado = qlearning.crear_clave_estado(estado)

            acciones = agente.obtener_acciones(pedidos_pendientes)

            accion = qlearning.elegir_accion(
                clave_estado,
                acciones
            )

            if accion is None:
                break

            pedido = buscar_pedido_por_id(
                pedidos_pendientes,
                accion
            )

            if pedido is None:
                break

            # ─── calcular recompensa y costo ──────────────────────

            recompensa = calcular_recompensa(
                pedido,
                entregado_exitosamente=True
            )

            costo = calcular_costo_ruta(pedido)

            # ─── registrar entrega ────────────────────────────────

            agente.registrar_entrega(pedido)

            # ─── ACTUALIZAR ESTADO DEL PEDIDO ────────────────────

            pedido["estado"] = "entregado"

            # ─── quitar de pendientes ────────────────────────────

            pedidos_pendientes = [
                p for p in pedidos_pendientes
                if obtener_id_pedido(p) != accion
            ]

            # ─── nuevo estado ────────────────────────────────────

            nuevo_estado = agente.obtener_estado(
                pedidos_pendientes
            )

            clave_nuevo_estado = qlearning.crear_clave_estado(
                nuevo_estado
            )

            nuevas_acciones = agente.obtener_acciones(
                pedidos_pendientes
            )

            # ─── actualizar tabla Q ──────────────────────────────

            qlearning.actualizar_q(
                clave_estado,
                accion,
                recompensa,
                clave_nuevo_estado,
                nuevas_acciones
            )

            # ─── guardar historial de ruta ───────────────────────

            ruta.append({
                "pedido": obtener_id_pedido(pedido),
                "destino": pedido.get("destino"),
                "recompensa": round(recompensa, 2),
                "costo": round(costo, 2),
                "estado": pedido["estado"]
            })

            recompensa_total += recompensa
            costo_total += costo

        resultados.append({
            "episodio": numero_episodio,
            "ruta": ruta,
            "recompensa_total": round(recompensa_total, 2),
            "costo_total": round(costo_total, 2),
            "entregas_completadas": len(agente.pedidos_entregados),
            "historial_acciones": agente.historial_acciones
        })

    return {
        "resultados": resultados,
        "cantidad_valores_q": len(qlearning.q_table)
    }


# ─── Ejecución directa ────────────────────────────────────────────────────────

if __name__ == "__main__":

    resultado = ejecutar_simulacion_beta(episodios=3)

    print("SIMULACIÓN BETA - DELIVERY INTELIGENTE")
    print("─" * 50)

    for ep in resultado["resultados"]:

        print(f"\nEpisodio {ep['episodio']}")
        print(f"  Entregas completadas : {ep['entregas_completadas']}")
        print(f"  Recompensa total     : {ep['recompensa_total']}")
        print(f"  Costo total          : {ep['costo_total']}")

        print("  Ruta tomada:")

        for paso in ep["ruta"]:

            print(
                f"    Pedido {paso['pedido']} → "
                f"{paso['destino']} "
                f"| Estado: {paso['estado']} "
                f"| Recomp: {paso['recompensa']} "
                f"| Costo: {paso['costo']}"
            )

    print(f"\nValores en Tabla Q: {resultado['cantidad_valores_q']}")