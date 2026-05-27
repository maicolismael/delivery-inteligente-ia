"""
agente.py

CAMBIO PRINCIPAL: el agente ahora rastrea coordenadas reales (lat, lng).
Antes solo guardaba el nombre del cliente como posicion.
Esto permite calcular la distancia real entre paradas consecutivas.
"""


class AgenteDelivery:

    # Coordenadas por defecto del almacen (del JSON)
    COORDS_ALMACEN_DEFAULT = (-12.0464, -77.0428)

    def __init__(self, posicion_inicial="almacen", coords_almacen=None):
        self.posicion_inicial     = posicion_inicial
        self.posicion_actual      = posicion_inicial
        # NUEVO: posicion real como (lat, lng)
        self.coordenadas_actuales = coords_almacen or self.COORDS_ALMACEN_DEFAULT
        self.pedidos_entregados   = []
        self.historial_acciones   = []

    def reiniciar(self, coords_almacen=None):
        self.posicion_actual      = self.posicion_inicial
        self.coordenadas_actuales = coords_almacen or self.COORDS_ALMACEN_DEFAULT
        self.pedidos_entregados   = []
        self.historial_acciones   = []

    def obtener_estado(self, pedidos_pendientes):
        return {
            "posicion_actual":            self.posicion_actual,
            "coordenadas_actuales":       self.coordenadas_actuales,
            "pedidos_pendientes":         pedidos_pendientes,
            "cantidad_pedidos_pendientes": len(pedidos_pendientes),
            "pedidos_entregados":         self.pedidos_entregados,
        }

    def obtener_acciones(self, pedidos_pendientes):
        """
        Devuelve IDs de pedidos entregables.
        Excluye rutas bloqueadas por ruta_bloqueada o estado_ruta.
        """
        acciones = []
        for pedido in pedidos_pendientes:
            bloqueada = pedido.get("ruta_bloqueada", False)
            estado    = pedido.get("estado_ruta", "libre")
            if not bloqueada and estado != "bloqueada":
                pid = pedido.get("id_pedido", pedido.get("id"))
                acciones.append(pid)
        return acciones

    def registrar_entrega(self, pedido):
        """
        Registra la entrega y actualiza posicion + coordenadas reales.
        """
        if pedido is None:
            return

        self.pedidos_entregados.append(pedido)

        # Posicion como texto (para la clave de estado en la tabla Q)
        self.posicion_actual = pedido.get(
            "destino",
            pedido.get("cliente_nombre", "desconocido")
        )

        # NUEVO: actualizar coordenadas reales
        coord = pedido.get("coordenadas")
        if coord and "lat" in coord and "lng" in coord:
            self.coordenadas_actuales = (coord["lat"], coord["lng"])

        self.historial_acciones.append({
            "accion":         "entrega_realizada",
            "pedido":         pedido.get("id_pedido", pedido.get("id")),
            "nueva_posicion": self.posicion_actual,
            "coordenadas":    self.coordenadas_actuales,
        })

    def seleccionar_pedido_basico(self, pedidos_pendientes):
        """Seleccion greedy simple (sin Q-Learning). Solo para comparar."""
        disponibles = [
            p for p in pedidos_pendientes
            if not p.get("ruta_bloqueada", False)
            and p.get("estado_ruta", "libre") != "bloqueada"
        ]
        if not disponibles:
            return None
        return min(disponibles, key=self._calcular_puntaje_pedido)

    def _calcular_puntaje_pedido(self, pedido):
        distancia = pedido.get("distancia", pedido.get("distancia_km", 0))
        tiempo    = pedido.get("tiempo",    pedido.get("tiempo_estimado_min", 0))
        trafico   = pedido.get("trafico", "bajo")
        prioridad = pedido.get("prioridad", "baja")

        pen_trafico  = {"bajo": 0, "medio": 5, "alto": 10}.get(trafico, 0)
        val_prioridad = {"alta": -10, "media": -5, "baja": 0}.get(prioridad, 0)

        return distancia + tiempo + pen_trafico + val_prioridad