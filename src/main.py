import json
from pathlib import Path

from src.agente import AgenteDelivery
from src.qlearning import QLearningDelivery


BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_DATASET = BASE_DIR / "data" / "pedidos_simulados.json"


PEDIDOS_DEMO = [
    {
        "id_pedido": 1,
        "destino": "Cliente 1",
        "distancia": 4.5,
        "tiempo": 12,
        "trafico": "medio",
        "prioridad": "alta",
        "estado_ruta": "libre"
    },
    {
        "id_pedido": 2,
        "destino": "Cliente 2",
        "distancia": 2.8,
        "tiempo": 8,
        "trafico": "bajo",
        "prioridad": "media",
        "estado_ruta": "libre"
    },
    {
        "id_pedido": 3,
        "destino": "Cliente 3",
        "distancia": 6.0,
        "tiempo": 18,
        "trafico": "alto",
        "prioridad": "baja",
        "estado_ruta": "libre"
    },
    {
        "id_pedido": 4,
        "destino": "Cliente 4",
        "distancia": 3.5,
        "tiempo": 10,
        "trafico": "alto",
        "prioridad": "alta",
        "estado_ruta": "bloqueada"
    }
]


def cargar_pedidos():
    """
    Carga pedidos desde data/pedidos_simulados.json.
    Si el archivo no existe o está vacío, usa pedidos de demostración.
    """
    try:
        with open(RUTA_DATASET, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

            if isinstance(datos, list):
                return datos

            if isinstance(datos, dict) and "pedidos" in datos:
                return datos["pedidos"]

    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return PEDIDOS_DEMO.copy()


def obtener_id_pedido(pedido):
    return pedido.get("id_pedido", pedido.get("id"))


def buscar_pedido_por_id(pedidos, id_pedido):
    for pedido in pedidos:
        if obtener_id_pedido(pedido) == id_pedido:
            return pedido

    return None


def calcular_recompensa_temporal(pedido):
    """
    Recompensa temporal para la beta.
    Luego puede reemplazarse por src/recompensas.py.
    """
    recompensa = 10

    distancia = pedido.get("distancia", 0)
    tiempo = pedido.get("tiempo", 0)
    trafico = pedido.get("trafico", "bajo")
    prioridad = pedido.get("prioridad", "baja")
    estado_ruta = pedido.get("estado_ruta", "libre")

    recompensa -= distancia
    recompensa -= tiempo * 0.2

    if trafico == "medio":
        recompensa -= 3
    elif trafico == "alto":
        recompensa -= 6

    if prioridad == "media":
        recompensa += 3
    elif prioridad == "alta":
        recompensa += 6

    if estado_ruta == "bloqueada":
        recompensa -= 20

    return round(recompensa, 2)


def calcular_costo_ruta_temporal(pedido):
    """
    Cálculo temporal del Costo de Ruta para la beta.
    """
    distancia = pedido.get("distancia", 0)
    tiempo = pedido.get("tiempo", 0)
    trafico = pedido.get("trafico", "bajo")
    estado_ruta = pedido.get("estado_ruta", "libre")

    penalizacion = 0

    if trafico == "medio":
        penalizacion += 3
    elif trafico == "alto":
        penalizacion += 6

    if estado_ruta == "bloqueada":
        penalizacion += 20

    return round(distancia + tiempo + penalizacion, 2)


def ejecutar_simulacion_beta(episodios=3):
    """
    Ejecuta una simulación básica para el segundo avance.

    No representa el entrenamiento final.
    Solo demuestra que el flujo Q-Learning funciona.
    """
    qlearning = QLearningDelivery(alpha=0.1, gamma=0.9, epsilon=0.3)
    resultados = []

    for numero_episodio in range(1, episodios + 1):
        pedidos_pendientes = cargar_pedidos()
        agente = AgenteDelivery(posicion_inicial="almacen")

        ruta = []
        recompensa_total = 0
        costo_total = 0

        while pedidos_pendientes:
            estado = agente.obtener_estado(pedidos_pendientes)
            clave_estado = qlearning.crear_clave_estado(estado)

            acciones = agente.obtener_acciones(pedidos_pendientes)
            accion = qlearning.elegir_accion(clave_estado, acciones)

            if accion is None:
                break

            pedido = buscar_pedido_por_id(pedidos_pendientes, accion)

            if pedido is None:
                break

            recompensa = calcular_recompensa_temporal(pedido)
            costo = calcular_costo_ruta_temporal(pedido)

            agente.registrar_entrega(pedido)

            pedidos_pendientes = [
                p for p in pedidos_pendientes
                if obtener_id_pedido(p) != accion
            ]

            nuevo_estado = agente.obtener_estado(pedidos_pendientes)
            clave_nuevo_estado = qlearning.crear_clave_estado(nuevo_estado)
            nuevas_acciones = agente.obtener_acciones(pedidos_pendientes)

            qlearning.actualizar_q(
                clave_estado,
                accion,
                recompensa,
                clave_nuevo_estado,
                nuevas_acciones
            )

            ruta.append({
                "pedido": obtener_id_pedido(pedido),
                "destino": pedido.get("destino"),
                "recompensa": recompensa,
                "costo": costo
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


if __name__ == "__main__":
    resultado = ejecutar_simulacion_beta(episodios=3)

    print("SIMULACIÓN BETA - DELIVERY INTELIGENTE")
    print("--------------------------------------")

    for episodio in resultado["resultados"]:
        print(f"\nEpisodio: {episodio['episodio']}")
        print(f"Entregas completadas: {episodio['entregas_completadas']}")
        print(f"Recompensa total: {episodio['recompensa_total']}")
        print(f"Costo total: {episodio['costo_total']}")
        print("Ruta tomada:")

        for paso in episodio["ruta"]:
            print(
                f"  Pedido {paso['pedido']} -> {paso['destino']} "
                f"| Recompensa: {paso['recompensa']} "
                f"| Costo: {paso['costo']}"
            )

    print(f"\nValores almacenados en Tabla Q: {resultado['cantidad_valores_q']}")