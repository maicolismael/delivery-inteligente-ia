"""
main.py

Archivo central del sistema de Delivery Inteligente.

Este módulo conecta:
- dataset de pedidos;
- agente;
- recompensas;
- Q-Learning;
- almacenamiento de Tabla Q;
- datos que serán enviados a la interfaz.

Aunque la función principal se llama ejecutar_simulacion_beta(),
se mantiene ese nombre para no romper imports anteriores.

En el tercer avance, esta función incluye:
- persistencia de Tabla Q;
- logs detallados del aprendizaje;
- explicación textual de cada decisión;
- mejor ruta encontrada;
- historial de costos y recompensas;
- datos listos para la interfaz PySide6.
"""

import json
from pathlib import Path

from src.agente import AgenteDelivery
from src.qlearning import QLearningDelivery
from src.recompensas import calcular_costo_ruta, calcular_recompensa


BASE_DIR = Path(__file__).resolve().parent.parent

RUTA_DATASET = BASE_DIR / "data" / "pedidos_simulados.json"
RUTA_QTABLE = BASE_DIR / "resultados" / "q_table.pkl"


# =========================================================
# CARGA DE DATOS
# =========================================================

def cargar_datos_originales() -> dict:
    """
    Carga el JSON completo.

    Devuelve:
    - almacén;
    - pedidos con todos sus campos originales.

    Esto sirve principalmente para la interfaz y para dibujar la ruta.
    """
    with open(RUTA_DATASET, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def cargar_pedidos() -> list[dict]:
    """
    Carga los pedidos desde data/pedidos_simulados.json
    y los normaliza al formato que usa el agente.

    El JSON original usa campos como:
    - id
    - cliente_nombre
    - distancia_km
    - tiempo_estimado_min
    - ruta_bloqueada

    El agente usa campos como:
    - id_pedido
    - destino
    - distancia
    - tiempo
    - estado_ruta

    Esta función traduce los datos para que todos los módulos trabajen sin errores.
    """
    try:
        datos = cargar_datos_originales()

        pedidos_raw = datos.get("pedidos", datos) if isinstance(datos, dict) else datos

        normalizados = []

        for pedido in pedidos_raw:
            normalizados.append({
                # Campos principales para agente y Q-Learning.
                "id_pedido": pedido.get("id_pedido", pedido.get("id")),
                "destino": pedido.get(
                    "destino",
                    pedido.get("cliente_nombre", "Desconocido")
                ),
                "distancia": pedido.get(
                    "distancia",
                    pedido.get("distancia_km", 0)
                ),
                "tiempo": pedido.get(
                    "tiempo",
                    pedido.get("tiempo_estimado_min", 0)
                ),
                "trafico": pedido.get("trafico", "bajo"),
                "prioridad": pedido.get("prioridad", "media"),
                "estado": pedido.get("estado", "pendiente"),

                # El agente usa estado_ruta.
                "estado_ruta": (
                    "bloqueada"
                    if pedido.get("ruta_bloqueada", False)
                    else "libre"
                ),

                # Campos originales para recompensas y visualización.
                "cliente_nombre": pedido.get("cliente_nombre", "Desconocido"),
                "direccion": pedido.get("direccion", "Sin dirección"),
                "distancia_km": pedido.get(
                    "distancia_km",
                    pedido.get("distancia", 0)
                ),
                "tiempo_estimado_min": pedido.get(
                    "tiempo_estimado_min",
                    pedido.get("tiempo", 0)
                ),
                "ruta_bloqueada": pedido.get("ruta_bloqueada", False),
                "coordenadas": pedido.get("coordenadas", None),
            })

        return normalizados

    except (FileNotFoundError, json.JSONDecodeError):
        return []


def obtener_id_pedido(pedido: dict):
    """
    Obtiene el ID de un pedido.

    Soporta:
    - id_pedido
    - id
    """
    return pedido.get("id_pedido", pedido.get("id"))


def buscar_pedido_por_id(pedidos: list[dict], id_pedido) -> dict | None:
    """
    Busca un pedido por su identificador.
    """
    for pedido in pedidos:
        if obtener_id_pedido(pedido) == id_pedido:
            return pedido

    return None


# =========================================================
# UTILIDADES PARA RESULTADOS
# =========================================================

def construir_texto_estado(clave_estado) -> str:
    """
    Convierte una clave de estado en texto entendible.

    Ejemplo:
    ('almacen', (1, 2, 3)) -> almacén, pedidos pendientes: P1, P2, P3
    """
    posicion, pendientes = clave_estado

    pedidos_texto = ", ".join(f"P{id_pedido}" for id_pedido in pendientes)

    if not pedidos_texto:
        pedidos_texto = "ninguno"

    return f"Posición: {posicion} | Pendientes: {pedidos_texto}"


def explicar_decision_pedido(
    pedido: dict,
    decision: dict,
    costo: float,
    recompensa: float
) -> str:
    """
    Genera una explicación entendible de por qué el agente escogió un pedido.

    Esta función NO reemplaza a Q-Learning.
    Lo que hace es traducir la decisión del agente a un texto más claro
    para mostrarlo en la interfaz y poder defender el funcionamiento.

    Explica:
    - si la acción fue por exploración o explotación;
    - si la ruta estaba libre o bloqueada;
    - prioridad del pedido;
    - nivel de tráfico;
    - distancia;
    - tiempo;
    - costo de ruta;
    - recompensa obtenida.
    """
    razones = []

    prioridad = pedido.get("prioridad", "media")
    trafico = pedido.get("trafico", "bajo")
    estado_ruta = pedido.get("estado_ruta", "libre")
    distancia = pedido.get("distancia", 0)
    tiempo = pedido.get("tiempo", 0)

    # Estado de ruta.
    if estado_ruta != "bloqueada":
        razones.append("la ruta está disponible y no se encuentra bloqueada")
    else:
        razones.append("la ruta está bloqueada, por lo que representa una mala opción")

    # Prioridad.
    if prioridad == "alta":
        razones.append("el pedido tiene prioridad alta")
    elif prioridad == "media":
        razones.append("el pedido tiene prioridad media")
    else:
        razones.append("el pedido tiene prioridad baja")

    # Tráfico.
    if trafico == "bajo":
        razones.append("el tráfico es bajo")
    elif trafico == "medio":
        razones.append("el tráfico es medio, por lo que tiene una penalización moderada")
    else:
        razones.append("el tráfico es alto, por lo que recibe mayor penalización")

    # Distancia.
    if distancia <= 4:
        razones.append("la distancia es corta")
    elif distancia <= 8:
        razones.append("la distancia es moderada")
    else:
        razones.append("la distancia es larga")

    # Tiempo.
    if tiempo <= 20:
        razones.append("el tiempo estimado es bajo")
    elif tiempo <= 45:
        razones.append("el tiempo estimado es aceptable")
    else:
        razones.append("el tiempo estimado es alto")

    # Tipo de decisión.
    if decision["tipo_decision"] == "exploración":
        tipo = (
            "El agente eligió esta acción por exploración. "
            "Esto significa que decidió probar una opción para descubrir "
            "si podía generar una buena recompensa."
        )
    elif decision["tipo_decision"] == "explotación":
        tipo = (
            "El agente eligió esta acción por explotación. "
            "Esto significa que usó lo aprendido en la Tabla Q para seleccionar "
            "la acción con mejor valor conocido en ese estado."
        )
    else:
        tipo = (
            "El agente eligió esta acción según las acciones disponibles "
            "en el estado actual."
        )

    explicacion = (
        f"{tipo}\n"
        f"Se escogió el pedido P{pedido.get('id_pedido')} porque "
        + "; ".join(razones)
        + f".\nEl Costo de Ruta calculado fue {round(costo, 2)} "
        f"y la recompensa obtenida fue {round(recompensa, 2)}."
    )

    return explicacion


def obtener_mejor_resultado(resultados: list[dict]) -> dict | None:
    """
    Devuelve el episodio con menor costo total.

    Ese episodio se considera la mejor ruta encontrada.
    """
    if not resultados:
        return None

    return min(resultados, key=lambda item: item["costo_total"])


def resetear_aprendizaje():
    """
    Borra la Tabla Q guardada.

    Esta función se puede llamar desde la interfaz para reiniciar el aprendizaje.
    """
    qlearning = QLearningDelivery(ruta_qtable=RUTA_QTABLE)
    qlearning.resetear_q_table()

    return {
        "ok": True,
        "mensaje": "Tabla Q reiniciada correctamente."
    }


# =========================================================
# SIMULACIÓN PRINCIPAL
# =========================================================

def ejecutar_simulacion_beta(
    episodios: int = 10,
    guardar_q: bool = True,
    resetear_q: bool = False,
    epsilon: float | None = None
) -> dict:
    """
    Ejecuta la simulación de Q-Learning.

    Parámetros:
    - episodios:
        cantidad de episodios de entrenamiento/simulación.

    - guardar_q:
        si es True, guarda la Tabla Q al terminar.

    - resetear_q:
        si es True, borra la Tabla Q antes de empezar.

    - epsilon:
        permite cambiar la exploración desde la interfaz.

    Retorna un diccionario con:
    - resultados por episodio;
    - cantidad de valores Q;
    - logs del aprendizaje;
    - mejor ruta;
    - historial de recompensas;
    - historial de costos;
    - resumen de Tabla Q.
    """

    qlearning = QLearningDelivery(
        alpha=0.1,
        gamma=0.9,
        epsilon=0.3 if epsilon is None else epsilon,
        ruta_qtable=RUTA_QTABLE
    )

    if resetear_q:
        qlearning.resetear_q_table()
    else:
        qlearning.cargar_q_table()

    resultados = []
    logs_aprendizaje = []
    historial_recompensas = []
    historial_costos = []

    for numero_episodio in range(1, episodios + 1):

        pedidos_pendientes = cargar_pedidos()
        datos_raw = cargar_datos_originales()
        coord_alm = datos_raw.get("almacen", {}).get("coordenadas", {})
        coords_almacen = (
            coord_alm.get("lat", -12.0464),
            coord_alm.get("lng", -77.0428)
        )
 
        agente = AgenteDelivery(
            posicion_inicial="almacen",
            coords_almacen=coords_almacen
        )

        ruta = []
        recompensa_total = 0.0
        costo_total = 0.0

        paso = 1

        while pedidos_pendientes:

            # 1. Obtener estado actual.
            estado = agente.obtener_estado(pedidos_pendientes)
            clave_estado = qlearning.crear_clave_estado(estado)

            # 2. Obtener acciones posibles.
            acciones = agente.obtener_acciones(pedidos_pendientes)

            # 3. Q-Learning elige una acción con detalle.
            decision = qlearning.elegir_accion_detallada(
                clave_estado,
                acciones
            )

            accion = decision["accion"]

            if accion is None:
                logs_aprendizaje.append(
                    f"[EP {numero_episodio} | Paso {paso}] "
                    f"No existen acciones disponibles."
                )
                break

            # 4. Buscar el pedido asociado a la acción.
            pedido = buscar_pedido_por_id(pedidos_pendientes, accion)

            if pedido is None:
                logs_aprendizaje.append(
                    f"[EP {numero_episodio} | Paso {paso}] "
                    f"No se encontró el pedido P{accion}."
                )
                break

            # 5. Calcular recompensa y costo.
            # Guardar coords ANTES de entregar (posicion de donde sale)
            pos_actual = agente.coordenadas_actuales   # NUEVO
 
            recompensa = calcular_recompensa(
                pedido,
                entregado_exitosamente=True,
                pos_actual_coords=pos_actual            # NUEVO
            )
 
            costo = calcular_costo_ruta(
                pedido,
                pos_actual_coords=pos_actual            # NUEVO
            )
 
            # IMPORTANTE: registrar DESPUES de calcular costo
            # (para usar la posicion previa, no la nueva)
            agente.registrar_entrega(pedido)

            # 6. Generar explicación humana de la decisión.
            explicacion_decision = explicar_decision_pedido(
                pedido,
                decision,
                costo,
                recompensa
            )

            # 7. Registrar entrega en el agente.
            agente.registrar_entrega(pedido)

            pedido["estado"] = "entregado"

            # 8. Quitar pedido de pendientes.
            pedidos_pendientes = [
                p for p in pedidos_pendientes
                if obtener_id_pedido(p) != accion
            ]

            # 9. Calcular nuevo estado.
            nuevo_estado = agente.obtener_estado(pedidos_pendientes)
            clave_nuevo_estado = qlearning.crear_clave_estado(nuevo_estado)
            nuevas_acciones = agente.obtener_acciones(pedidos_pendientes)

            # 10. Actualizar Tabla Q y guardar detalle.
            detalle_q = qlearning.actualizar_q_detallado(
                clave_estado,
                accion,
                recompensa,
                clave_nuevo_estado,
                nuevas_acciones
            )

            # 11. Guardar paso de ruta.
            ruta.append({
                "pedido": obtener_id_pedido(pedido),
                "destino": pedido.get("destino"),
                "cliente_nombre": pedido.get("cliente_nombre"),
                "direccion": pedido.get("direccion"),
                "prioridad": pedido.get("prioridad"),
                "trafico": pedido.get("trafico"),
                "distancia": pedido.get("distancia"),
                "tiempo": pedido.get("tiempo"),
                "recompensa": round(recompensa, 2),
                "costo": round(costo, 2),
                "estado": pedido["estado"],
                "coordenadas": pedido.get("coordenadas"),
                "tipo_decision": decision["tipo_decision"],
                "motivo_decision": decision["motivo"],
                "explicacion": explicacion_decision,
                "q_anterior": detalle_q["q_anterior"],
                "q_nuevo": detalle_q["q_nuevo"]
            })

            recompensa_total += recompensa
            costo_total += costo

            # 12. Crear log explicativo para la interfaz.
            log = (
                f"[EP {numero_episodio} | Paso {paso}]\n"
                f"Estado actual: {construir_texto_estado(clave_estado)}\n"
                f"Acciones disponibles: {', '.join('P' + str(a) for a in acciones)}\n"
                f"Acción elegida: P{accion} - {pedido.get('destino')}\n"
                f"Tipo de decisión: {decision['tipo_decision']}\n"
                f"Motivo técnico: {decision['motivo']}\n"
                f"Explicación de la decisión:\n{explicacion_decision}\n"
                f"Costo de ruta: {round(costo, 2)}\n"
                f"Recompensa obtenida: {round(recompensa, 2)}\n"
                f"Q anterior: {detalle_q['q_anterior']}\n"
                f"Mejor valor futuro: {detalle_q['mejor_valor_futuro']}\n"
                f"Q actualizado: {detalle_q['q_nuevo']}\n"
                f"Fórmula aplicada: {detalle_q['formula']}\n"
                f"Interpretación Q: si Q aumenta, significa que el agente aprendió "
                f"que esta acción es más conveniente en este estado.\n"
                f"{'-' * 70}"
            )

            logs_aprendizaje.append(log)

            paso += 1

        resultado_episodio = {
            "episodio": numero_episodio,
            "ruta": ruta,
            "recompensa_total": round(recompensa_total, 2),
            "costo_total": round(costo_total, 2),
            "entregas_completadas": len(agente.pedidos_entregados),
            "historial_acciones": agente.historial_acciones
        }
        qlearning.decaer_epsilon(tasa=0.99, minimo=0.05)   
        resultados.append(resultado_episodio)
        historial_recompensas.append(round(recompensa_total, 2))
        historial_costos.append(round(costo_total, 2))

    if guardar_q:
        qlearning.guardar_q_table()

    mejor_resultado = obtener_mejor_resultado(resultados)

    return {
        "resultados": resultados,
        "cantidad_valores_q": len(qlearning.q_table),
        "logs_aprendizaje": logs_aprendizaje,
        "mejor_ruta": mejor_resultado,
        "historial_recompensas": historial_recompensas,
        "historial_costos": historial_costos,
        "tabla_q_resumen": qlearning.obtener_resumen_q_table(limite=20),
        "parametros": {
            "alpha": qlearning.alpha,
            "gamma": qlearning.gamma,
            "epsilon": qlearning.epsilon
        },
        "archivo_q_table": str(RUTA_QTABLE)
    }


# =========================================================
# EJECUCIÓN POR CONSOLA
# =========================================================

if __name__ == "__main__":

    resultado = ejecutar_simulacion_beta(episodios=5)

    print("SIMULACIÓN - DELIVERY INTELIGENTE CON Q-LEARNING")
    print("─" * 60)

    for episodio in resultado["resultados"]:
        print(f"\nEpisodio {episodio['episodio']}")
        print(f"Entregas completadas : {episodio['entregas_completadas']}")
        print(f"Recompensa total     : {episodio['recompensa_total']}")
        print(f"Costo total          : {episodio['costo_total']}")
        print("Ruta tomada:")

        for paso in episodio["ruta"]:
            print(
                f"  P{paso['pedido']} → {paso['destino']} "
                f"| Decisión: {paso['tipo_decision']} "
                f"| Q: {paso['q_anterior']} → {paso['q_nuevo']}"
            )

    print(f"\nValores en Tabla Q: {resultado['cantidad_valores_q']}")
    print(f"Archivo Tabla Q: {resultado['archivo_q_table']}")