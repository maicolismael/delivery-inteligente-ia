"""
qlearning.py

Módulo encargado del aprendizaje por refuerzo mediante Q-Learning.

Este archivo contiene la clase QLearningDelivery, que permite:
- crear y actualizar una Tabla Q;
- elegir acciones mediante epsilon-greedy;
- diferenciar exploración y explotación;
- guardar el aprendizaje en un archivo;
- cargar el aprendizaje guardado;
- generar información explicable para mostrar en la interfaz.

La fórmula utilizada es:

Q(s,a) = Q(s,a) + alpha * [ recompensa + gamma * max(Q(s',a')) - Q(s,a) ]

Donde:
- s  = estado actual
- a  = acción elegida
- s' = nuevo estado
- alpha = tasa de aprendizaje
- gamma = factor de descuento
"""

import pickle
import random
from pathlib import Path


class QLearningDelivery:
    """
    Clase principal del algoritmo Q-Learning para el agente de delivery.
    """

    def __init__(
        self,
        alpha=0.1,
        gamma=0.9,
        epsilon=0.3,
        ruta_qtable="resultados/q_table.pkl"
    ):
        """
        Constructor de Q-Learning.

        alpha:
            Tasa de aprendizaje.
            Mientras más alto, más rápido actualiza los valores Q.

        gamma:
            Factor de descuento.
            Define cuánto importa la recompensa futura.

        epsilon:
            Probabilidad de exploración.
            Si epsilon = 0.3, el agente explora aproximadamente el 30% de las veces.

        ruta_qtable:
            Archivo donde se guarda/carga la Tabla Q.
        """
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

        # La Tabla Q se guarda como diccionario:
        # clave: (estado, accion)
        # valor: valor Q aprendido
        self.q_table = {}

        # Ruta donde se guardará el aprendizaje.
        self.ruta_qtable = Path(ruta_qtable)

    # =========================================================
    # PERSISTENCIA DE TABLA Q
    # =========================================================

    def cargar_q_table(self):
        """
        Carga la Tabla Q desde archivo.

        Esto evita que el aprendizaje se pierda cada vez que se cierra
        o se vuelve a ejecutar el programa.
        """
        if not self.ruta_qtable.exists():
            self.q_table = {}
            return False

        try:
            with open(self.ruta_qtable, "rb") as archivo:
                self.q_table = pickle.load(archivo)

            return True

        except Exception:
            # Si el archivo está dañado o no se puede leer,
            # se inicia con una tabla vacía para evitar que el sistema falle.
            self.q_table = {}
            return False

    def guardar_q_table(self):
        """
        Guarda la Tabla Q en un archivo .pkl.

        Se crea la carpeta resultados/ si no existe.
        """
        self.ruta_qtable.parent.mkdir(parents=True, exist_ok=True)

        with open(self.ruta_qtable, "wb") as archivo:
            pickle.dump(self.q_table, archivo)

    def resetear_q_table(self):
        """
        Borra el aprendizaje de memoria y del archivo guardado.

        Esto sirve para demostrar la diferencia entre:
        - agente sin aprendizaje;
        - agente después de entrenar.
        """
        self.q_table = {}

        if self.ruta_qtable.exists():
            self.ruta_qtable.unlink()

    # =========================================================
    # VALORES Q
    # =========================================================

    def obtener_valor_q(self, estado, accion):
        """
        Devuelve el valor Q de un par estado-acción.

        Si ese par aún no existe en la Tabla Q, devuelve 0.0.
        """
        return self.q_table.get((estado, accion), 0.0)

    def obtener_valores_acciones(self, estado, acciones):
        """
        Devuelve un diccionario con los valores Q de todas las acciones disponibles.

        Ejemplo:
        {
            1: 8.5,
            2: 0.0,
            3: 12.3
        }
        """
        return {
            accion: round(self.obtener_valor_q(estado, accion), 4)
            for accion in acciones
        }

    # =========================================================
    # SELECCIÓN DE ACCIONES
    # =========================================================

    def elegir_accion(self, estado, acciones):
        """
        Versión simple: devuelve solo la acción elegida.

        Se mantiene para compatibilidad con código anterior.
        """
        detalle = self.elegir_accion_detallada(estado, acciones)
        return detalle["accion"]

    def elegir_accion_detallada(self, estado, acciones):
        """
        Elige una acción usando epsilon-greedy y devuelve explicación.

        Puede elegir por:
        - exploración: prueba una acción aleatoria;
        - explotación: elige la acción con mayor valor Q conocido.

        Esta función es importante para la interfaz, porque permite mostrar:
        - qué acción eligió;
        - por qué la eligió;
        - qué valores Q tenía disponibles.
        """
        if not acciones:
            return {
                "accion": None,
                "tipo_decision": "sin_acciones",
                "motivo": "No existen acciones disponibles.",
                "valores_q": {}
            }

        valores_q = self.obtener_valores_acciones(estado, acciones)

        # Exploración: el agente prueba una acción aleatoria.
        if random.random() < self.epsilon:
            accion = random.choice(acciones)

            return {
                "accion": accion,
                "tipo_decision": "exploración",
                "motivo": (
                    f"El agente exploró una acción aleatoria "
                    f"porque epsilon = {self.epsilon}."
                ),
                "valores_q": valores_q
            }

        # Explotación: el agente usa lo aprendido.
        accion = max(
            acciones,
            key=lambda accion_actual: self.obtener_valor_q(estado, accion_actual)
        )

        return {
            "accion": accion,
            "tipo_decision": "explotación",
            "motivo": (
                "El agente eligió la acción con mayor valor Q conocido "
                "para este estado."
            ),
            "valores_q": valores_q
        }

    # =========================================================
    # ACTUALIZACIÓN DE TABLA Q
    # =========================================================

    def actualizar_q(self, estado, accion, recompensa, nuevo_estado, nuevas_acciones):
        """
        Versión simple: actualiza Q y devuelve el nuevo valor.

        Se mantiene para compatibilidad con código anterior.
        """
        detalle = self.actualizar_q_detallado(
            estado,
            accion,
            recompensa,
            nuevo_estado,
            nuevas_acciones
        )

        return detalle["q_nuevo"]

    def actualizar_q_detallado(
        self,
        estado,
        accion,
        recompensa,
        nuevo_estado,
        nuevas_acciones
    ):
        """
        Actualiza la Tabla Q y devuelve información detallada.

        Devuelve:
        - Q anterior;
        - mejor valor futuro;
        - Q nuevo;
        - explicación textual de la actualización.

        Esto será mostrado en la interfaz para demostrar cómo aprende.
        """
        q_anterior = self.obtener_valor_q(estado, accion)

        if nuevas_acciones:
            mejor_valor_futuro = max(
                self.obtener_valor_q(nuevo_estado, nueva_accion)
                for nueva_accion in nuevas_acciones
            )
        else:
            mejor_valor_futuro = 0.0

        q_nuevo = q_anterior + self.alpha * (
            recompensa + self.gamma * mejor_valor_futuro - q_anterior
        )

        self.q_table[(estado, accion)] = q_nuevo

        return {
            "q_anterior": round(q_anterior, 4),
            "mejor_valor_futuro": round(mejor_valor_futuro, 4),
            "q_nuevo": round(q_nuevo, 4),
            "formula": (
                f"Q nuevo = {round(q_anterior, 4)} + {self.alpha} * "
                f"[{round(recompensa, 4)} + {self.gamma} * "
                f"{round(mejor_valor_futuro, 4)} - {round(q_anterior, 4)}]"
            )
        }

    # =========================================================
    # ESTADOS
    # =========================================================

    @staticmethod
    def crear_clave_estado(estado):
        """
        Convierte el estado del agente en una clave simple para la Tabla Q.

        En lugar de guardar todo el diccionario del estado, se resume en:
        - posición actual;
        - pedidos pendientes.

        Ejemplo:
        ('almacen', (1, 2, 3, 4))
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

    # =========================================================
    # RESUMEN PARA INTERFAZ
    # =========================================================

    def obtener_resumen_q_table(self, limite=15):
        """
        Devuelve un resumen de los valores más altos de la Tabla Q.

        Esto evita mostrar toda la Tabla Q completa, que puede ser muy grande.
        """
        elementos = []

        for (estado, accion), valor in self.q_table.items():
            elementos.append({
                "estado": str(estado),
                "accion": accion,
                "valor_q": round(valor, 4)
            })

        elementos.sort(key=lambda item: item["valor_q"], reverse=True)

        return elementos[:limite]