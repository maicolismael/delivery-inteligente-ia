class AgenteDelivery:
    """
    Agente básico de delivery para el segundo avance.

    Esta versión permite:
    - conocer la posición actual;
    - recibir pedidos pendientes;
    - obtener acciones posibles;
    - seleccionar un pedido básico;
    - evitar rutas bloqueadas;
    - actualizar posición después de entregar;
    - guardar historial de acciones.
    """

    def __init__(self, posicion_inicial="almacen"):
        self.posicion_inicial = posicion_inicial
        self.posicion_actual = posicion_inicial
        self.pedidos_entregados = []
        self.historial_acciones = []

    def reiniciar(self):
        self.posicion_actual = self.posicion_inicial
        self.pedidos_entregados = []
        self.historial_acciones = []

    def obtener_estado(self, pedidos_pendientes):
        return {
            "posicion_actual": self.posicion_actual,
            "pedidos_pendientes": pedidos_pendientes,
            "cantidad_pedidos_pendientes": len(pedidos_pendientes),
            "pedidos_entregados": self.pedidos_entregados
        }

    def obtener_acciones(self, pedidos_pendientes):
        acciones = []

        for pedido in pedidos_pendientes:
            if pedido.get("estado_ruta", "libre") != "bloqueada":
                acciones.append(pedido.get("id_pedido"))

        return acciones

    def seleccionar_pedido_basico(self, pedidos_pendientes):
        pedidos_disponibles = [
            pedido for pedido in pedidos_pendientes
            if pedido.get("estado_ruta", "libre") != "bloqueada"
        ]

        if not pedidos_disponibles:
            return None

        pedido_seleccionado = min(
            pedidos_disponibles,
            key=self._calcular_puntaje_pedido
        )

        self.historial_acciones.append({
            "accion": "seleccion_basica",
            "pedido": pedido_seleccionado.get("id_pedido"),
            "posicion_origen": self.posicion_actual
        })

        return pedido_seleccionado

    def registrar_entrega(self, pedido):
        if pedido is None:
            return

        self.pedidos_entregados.append(pedido)

        nueva_posicion = pedido.get("destino", "desconocido")
        self.posicion_actual = nueva_posicion

        self.historial_acciones.append({
            "accion": "entrega_realizada",
            "pedido": pedido.get("id_pedido"),
            "nueva_posicion": self.posicion_actual
        })

    def _calcular_puntaje_pedido(self, pedido):
        distancia = pedido.get("distancia", 0)
        tiempo = pedido.get("tiempo", 0)

        prioridad = pedido.get("prioridad", "baja")
        trafico = pedido.get("trafico", "bajo")

        valor_prioridad = {
            "alta": -10,
            "media": -5,
            "baja": 0
        }.get(prioridad, 0)

        penalizacion_trafico = {
            "bajo": 0,
            "medio": 5,
            "alto": 10
        }.get(trafico, 0)

        return distancia + tiempo + penalizacion_trafico + valor_prioridad