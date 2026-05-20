import random


class QLearningDelivery:
    """
    Implementación básica de Q-Learning para el segundo avance.

    Esta clase permite:
    - crear una Tabla Q;
    - elegir acciones usando exploración/explotación;
    - actualizar valores Q;
    - representar estados en una clave simple.
    """

    def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.3):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = {}

    def obtener_valor_q(self, estado, accion):
        """
        Obtiene el valor Q de un par estado-acción.
        Si no existe, devuelve 0.
        """
        return self.q_table.get((estado, accion), 0.0)

    def elegir_accion(self, estado, acciones):
        """
        Elige una acción usando epsilon-greedy.

        - Con probabilidad epsilon explora una acción aleatoria.
        - Caso contrario, elige la acción con mayor valor Q.
        """
        if not acciones:
            return None

        if random.random() < self.epsilon:
            return random.choice(acciones)

        return max(
            acciones,
            key=lambda accion: self.obtener_valor_q(estado, accion)
        )

    def actualizar_q(self, estado, accion, recompensa, nuevo_estado, nuevas_acciones):
        """
        Actualiza la Tabla Q usando la fórmula:

        Q(s,a) = Q(s,a) + alpha * [r + gamma * max(Q(s',a')) - Q(s,a)]
        """
        valor_actual = self.obtener_valor_q(estado, accion)

        if nuevas_acciones:
            mejor_valor_futuro = max(
                self.obtener_valor_q(nuevo_estado, nueva_accion)
                for nueva_accion in nuevas_acciones
            )
        else:
            mejor_valor_futuro = 0

        nuevo_valor = valor_actual + self.alpha * (
            recompensa + self.gamma * mejor_valor_futuro - valor_actual
        )

        self.q_table[(estado, accion)] = nuevo_valor
        return nuevo_valor

    @staticmethod
    def crear_clave_estado(estado):
        """
        Convierte el estado del agente en una clave simple para usar en la Tabla Q.
        """
        posicion = estado.get("posicion_actual", "desconocido")

        pedidos_pendientes = estado.get("pedidos_pendientes", [])
        ids_pendientes = []

        for pedido in pedidos_pendientes:
            id_pedido = pedido.get("id_pedido", pedido.get("id"))
            ids_pendientes.append(id_pedido)

        return (
            posicion,
            tuple(sorted(ids_pendientes))
        )