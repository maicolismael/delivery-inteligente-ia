"""
ui/app.py

Interfaz gráfica para el sistema Delivery Inteligente con Q-Learning.

Esta versión usa PySide6 y organiza la información en varias ventanas:
- Ventana principal
- Ventana de pedidos
- Ventana de mapa offline animado
- Ventana de aprendizaje detallado
- Ventana de Tabla Q

Ejecutar desde la raíz del proyecto:

python ui/app.py
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QBrush, QFont, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QGraphicsView,
    QGraphicsScene,
)


# =========================================================
# RUTAS DEL PROYECTO
# =========================================================

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# =========================================================
# IMPORTS DEL SISTEMA
# =========================================================

from src.main import (
    cargar_datos_originales,
    ejecutar_simulacion_beta,
    resetear_aprendizaje,
)


# =========================================================
# COLORES
# =========================================================

COLOR_FONDO = "#f4f6f9"
COLOR_CARD = "#ffffff"
COLOR_HEADER = "#111827"
COLOR_AZUL = "#2563eb"
COLOR_AZUL_OSCURO = "#1d4ed8"
COLOR_VERDE = "#16a34a"
COLOR_ROJO = "#dc2626"
COLOR_NARANJA = "#ea580c"
COLOR_MORADO = "#7c3aed"
COLOR_AMARILLO = "#facc15"
COLOR_GRIS = "#6b7280"
COLOR_TEXTO = "#1f2937"


# =========================================================
# TARJETA DE MÉTRICA
# =========================================================

class TarjetaMetrica(QFrame):
    """
    Tarjeta visual para mostrar una métrica importante.

    Ejemplo:
    -------------------
    | Mejor costo      |
    | 120.5            |
    -------------------
    """

    def __init__(self, titulo: str, valor="-", color=COLOR_AZUL):
        super().__init__()

        self.setObjectName("tarjetaMetrica")

        layout = QVBoxLayout(self)

        self.lbl_titulo = QLabel(titulo)
        self.lbl_titulo.setStyleSheet(
            f"color: {COLOR_GRIS}; font-size: 12px;"
        )

        self.lbl_valor = QLabel(str(valor))
        self.lbl_valor.setStyleSheet(
            f"color: {color}; font-size: 22px; font-weight: bold;"
        )

        layout.addWidget(self.lbl_titulo)
        layout.addWidget(self.lbl_valor)

    def set_valor(self, valor):
        """
        Actualiza el valor de la tarjeta.
        """
        self.lbl_valor.setText(str(valor))


# =========================================================
# VENTANA DE PEDIDOS
# =========================================================

class VentanaPedidos(QDialog):
    """
    Ventana que muestra el dataset de pedidos.

    Esta ventana sirve para explicar el entorno:
    - qué pedidos existen;
    - qué distancia tienen;
    - qué prioridad poseen;
    - si tienen tráfico;
    - si hay rutas bloqueadas.
    """

    def __init__(self, datos_json, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Pedidos simulados")
        self.resize(1150, 650)

        self.datos_json = datos_json

        layout = QVBoxLayout(self)

        titulo = QLabel("Pedidos simulados del entorno")
        titulo.setObjectName("tituloVentana")

        descripcion = QLabel(
            "Esta tabla representa el entorno inicial del agente. "
            "Cada pedido contiene distancia, tiempo estimado, prioridad, tráfico y estado de ruta."
        )
        descripcion.setWordWrap(True)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "ID",
            "Cliente",
            "Dirección",
            "Distancia km",
            "Tiempo min",
            "Prioridad",
            "Tráfico",
            "Bloqueada",
            "Estado"
        ])

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(self.tabla)

        self._cargar_pedidos()

    def _cargar_pedidos(self):
        """
        Carga pedidos del JSON en la tabla.
        """
        pedidos = self.datos_json.get("pedidos", [])

        self.tabla.setRowCount(len(pedidos))

        for fila, pedido in enumerate(pedidos):
            valores = [
                pedido.get("id"),
                pedido.get("cliente_nombre"),
                pedido.get("direccion"),
                pedido.get("distancia_km"),
                pedido.get("tiempo_estimado_min"),
                pedido.get("prioridad"),
                pedido.get("trafico"),
                "Sí" if pedido.get("ruta_bloqueada") else "No",
                pedido.get("estado"),
            ]

            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignCenter)
                self.tabla.setItem(fila, columna, item)

        self.tabla.resizeColumnsToContents()


# =========================================================
# VENTANA DE APRENDIZAJE
# =========================================================

class VentanaAprendizaje(QDialog):
    """
    Ventana que muestra cómo aprende el agente paso a paso.

    Aquí se ve:
    - estado actual;
    - acciones disponibles;
    - acción elegida;
    - exploración o explotación;
    - recompensa;
    - Q anterior;
    - Q actualizado;
    - explicación del cambio.
    """

    def __init__(self, resultado, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Aprendizaje detallado Q-Learning")
        self.resize(1200, 780)

        self.resultado = resultado or {}

        layout = QVBoxLayout(self)

        titulo = QLabel("Proceso de aprendizaje Q-Learning")
        titulo.setObjectName("tituloVentana")

        explicacion = QLabel(
            "Esta consola muestra el proceso interno del agente. "
            "Cada bloque representa una decisión tomada durante el entrenamiento: "
            "estado, acción, recompensa y actualización de la Tabla Q."
        )
        explicacion.setWordWrap(True)

        nota = QLabel(
            "Importante: en este sistema, un valor Q más alto significa que el agente "
            "espera una mayor recompensa para esa acción. En cambio, el Costo de Ruta debe ser bajo."
        )
        nota.setWordWrap(True)
        nota.setObjectName("notaImportante")

        self.txt_logs = QPlainTextEdit()
        self.txt_logs.setReadOnly(True)

        layout.addWidget(titulo)
        layout.addWidget(explicacion)
        layout.addWidget(nota)
        layout.addWidget(self.txt_logs)

        self._cargar_logs()

    def _cargar_logs(self):
        """
        Muestra los logs de aprendizaje generados por main.py.
        """
        logs = self.resultado.get("logs_aprendizaje", [])

        if not logs:
            self.txt_logs.setPlainText(
                "Todavía no hay logs de aprendizaje.\n\n"
                "Primero ejecuta 'Entrenar agente' desde la ventana principal."
            )
            return

        texto = "\n\n".join(logs)
        self.txt_logs.setPlainText(texto)


# =========================================================
# VENTANA DE TABLA Q
# =========================================================

class VentanaTablaQ(QDialog):
    """
    Ventana que muestra un resumen de la Tabla Q.

    La Tabla Q representa la memoria del agente.
    Cada fila indica:
    - estado;
    - acción;
    - valor Q;
    - interpretación.
    """

    def __init__(self, resultado, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Resumen de Tabla Q")
        self.resize(1150, 700)

        self.resultado = resultado or {}

        layout = QVBoxLayout(self)

        titulo = QLabel("Tabla Q aprendida por el agente")
        titulo.setObjectName("tituloVentana")

        explicacion = QLabel(
            "La Tabla Q almacena lo que el agente aprendió. "
            "Un valor Q alto indica que esa acción resultó conveniente en ese estado. "
            "Un valor Q bajo indica que la acción no fue tan favorable. "
            "El agente busca valores Q altos porque representan mayor recompensa esperada."
        )
        explicacion.setWordWrap(True)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels([
            "Estado",
            "Acción",
            "Valor Q",
            "Interpretación"
        ])

        layout.addWidget(titulo)
        layout.addWidget(explicacion)
        layout.addWidget(self.tabla)

        self._cargar_tabla_q()

    def _interpretar_valor_q(self, valor_q):
        """
        Genera una explicación simple del valor Q.
        """
        try:
            valor = float(valor_q)
        except Exception:
            return "Sin interpretación"

        if valor > 20:
            return "Acción muy conveniente aprendida"
        if valor > 0:
            return "Acción favorable"
        if valor == 0:
            return "Acción aún no aprendida"
        return "Acción poco conveniente o penalizada"

    def _cargar_tabla_q(self):
        """
        Carga el resumen de Tabla Q en la tabla visual.
        """
        resumen = self.resultado.get("tabla_q_resumen", [])

        self.tabla.setRowCount(len(resumen))

        for fila, item in enumerate(resumen):
            estado = item.get("estado", "")
            accion = item.get("accion", "")
            valor_q = item.get("valor_q", 0)
            interpretacion = self._interpretar_valor_q(valor_q)

            valores = [
                estado,
                accion,
                valor_q,
                interpretacion
            ]

            for columna, valor in enumerate(valores):
                celda = QTableWidgetItem(str(valor))
                self.tabla.setItem(fila, columna, celda)

        self.tabla.resizeColumnsToContents()


# =========================================================
# VENTANA DE MAPA OFFLINE ANIMADO
# =========================================================

class VentanaMapa(QDialog):
    """
    Ventana de mapa offline animado.

    Esta ventana NO usa internet.
    No utiliza Folium ni OpenStreetMap.

    Lo que hace:
    - Dibuja un mapa simulado tipo tablero de calles.
    - Muestra el almacén.
    - Muestra todos los pedidos.
    - Dibuja la ruta que eligió el agente.
    - Anima el movimiento del agente como si fuera un video.

    Importante:
    El agente aprende el ORDEN de entrega.
    Esta ventana visualiza ese orden en un mapa lógico/simulado.
    """

    def __init__(self, datos_json, resultado, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Mapa animado de la ruta del agente")
        self.resize(1200, 780)

        self.datos_json = datos_json
        self.resultado = resultado or {}

        self.ruta = self._obtener_mejor_ruta()

        self.scene = QGraphicsScene()

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._avanzar_animacion)

        self.puntos_canvas = {}
        self.puntos_animacion = []
        self.indice_animacion = 0
        self.agente_item = None
        self.agente_label = None

        self._construir_ui()
        self._preparar_mapa()
        self._dibujar_mapa()
        self._preparar_animacion()

    # =====================================================
    # UI
    # =====================================================

    def _construir_ui(self):
        """
        Construye la ventana del mapa animado.
        """
        layout = QVBoxLayout(self)

        titulo = QLabel("Mapa offline animado de la ruta elegida")
        titulo.setObjectName("tituloVentana")

        descripcion = QLabel(
            "Este mapa no usa internet. Representa un entorno simulado de calles. "
            "El agente se mueve desde el almacén hacia los pedidos en el orden que eligió Q-Learning."
        )
        descripcion.setWordWrap(True)

        self.lbl_estado = QLabel("Presiona 'Iniciar animación' para ver el recorrido.")
        self.lbl_estado.setStyleSheet("font-weight: bold; color: #1d4ed8;")

        botones = QHBoxLayout()

        self.btn_iniciar = QPushButton("▶ Iniciar animación")
        self.btn_pausar = QPushButton("⏸ Pausar")
        self.btn_reiniciar = QPushButton("↺ Reiniciar")
        self.btn_paso = QPushButton("Avanzar paso")

        self.btn_iniciar.clicked.connect(self.iniciar_animacion)
        self.btn_pausar.clicked.connect(self.pausar_animacion)
        self.btn_reiniciar.clicked.connect(self.reiniciar_animacion)
        self.btn_paso.clicked.connect(self.avanzar_un_paso)

        botones.addWidget(self.btn_iniciar)
        botones.addWidget(self.btn_pausar)
        botones.addWidget(self.btn_reiniciar)
        botones.addWidget(self.btn_paso)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(self.lbl_estado)
        layout.addLayout(botones)
        layout.addWidget(self.view)

    # =====================================================
    # DATOS DE RUTA
    # =====================================================

    def _obtener_mejor_ruta(self):
        """
        Obtiene la mejor ruta encontrada por el agente.

        En main.py, 'mejor_ruta' representa el episodio con menor costo total.
        """
        mejor = self.resultado.get("mejor_ruta")

        if mejor:
            return mejor.get("ruta", [])

        return []

    # =====================================================
    # PREPARACIÓN DE COORDENADAS
    # =====================================================

    def _preparar_mapa(self):
        """
        Convierte coordenadas geográficas del JSON a coordenadas de pantalla.

        Como no usamos mapa real, tomamos latitud/longitud y las escalamos
        dentro del área gráfica.
        """
        almacen = self.datos_json.get("almacen", {})
        pedidos = self.datos_json.get("pedidos", [])

        coordenadas = []

        coord_almacen = almacen.get("coordenadas", {})
        if "lat" in coord_almacen and "lng" in coord_almacen:
            coordenadas.append(coord_almacen)

        for pedido in pedidos:
            coord = pedido.get("coordenadas", {})
            if "lat" in coord and "lng" in coord:
                coordenadas.append(coord)

        if not coordenadas:
            return

        latitudes = [c["lat"] for c in coordenadas]
        longitudes = [c["lng"] for c in coordenadas]

        self.min_lat = min(latitudes)
        self.max_lat = max(latitudes)
        self.min_lng = min(longitudes)
        self.max_lng = max(longitudes)

        self.ancho_mapa = 1000
        self.alto_mapa = 540
        self.margen = 60

        self.scene.setSceneRect(0, 0, self.ancho_mapa, self.alto_mapa)

        self.puntos_canvas["almacen"] = self._coord_a_canvas(
            coord_almacen["lat"],
            coord_almacen["lng"]
        )

        for pedido in pedidos:
            coord = pedido.get("coordenadas", {})
            if "lat" not in coord or "lng" not in coord:
                continue

            pedido_id = pedido.get("id")

            self.puntos_canvas[pedido_id] = self._coord_a_canvas(
                coord["lat"],
                coord["lng"]
            )

    def _coord_a_canvas(self, lat, lng):
        """
        Convierte lat/lng a coordenadas X/Y de la escena.

        X se calcula con longitud.
        Y se calcula con latitud invertida porque en pantalla Y crece hacia abajo.
        """
        rango_lng = self.max_lng - self.min_lng
        rango_lat = self.max_lat - self.min_lat

        if rango_lng == 0:
            rango_lng = 1

        if rango_lat == 0:
            rango_lat = 1

        x = self.margen + ((lng - self.min_lng) / rango_lng) * (
            self.ancho_mapa - 2 * self.margen
        )

        y = self.alto_mapa - (
            self.margen + ((lat - self.min_lat) / rango_lat) * (
                self.alto_mapa - 2 * self.margen
            )
        )

        return QPointF(x, y)

    # =====================================================
    # DIBUJO DEL MAPA
    # =====================================================

    def _dibujar_mapa(self):
        """
        Dibuja el mapa completo:
        - fondo;
        - calles simuladas;
        - almacén;
        - pedidos;
        - ruta elegida;
        - agente.
        """
        self.scene.clear()

        self._dibujar_fondo()
        self._dibujar_calles()
        self._dibujar_pedidos()
        self._dibujar_ruta()
        self._dibujar_agente()

    def _dibujar_fondo(self):
        """
        Dibuja el fondo del mapa.
        """
        self.scene.setBackgroundBrush(QBrush(QColor("#f8fafc")))

    def _dibujar_calles(self):
        """
        Dibuja una grilla de calles simuladas.

        Esto evita que la ruta se vea como una línea cruzando casas.
        No es una ruta real, pero visualmente representa avenidas/calles.
        """
        pen_calle = QPen(QColor("#d1d5db"))
        pen_calle.setWidth(1)

        separacion = 70

        x = self.margen
        while x <= self.ancho_mapa - self.margen:
            self.scene.addLine(
                x,
                self.margen,
                x,
                self.alto_mapa - self.margen,
                pen_calle
            )
            x += separacion

        y = self.margen
        while y <= self.alto_mapa - self.margen:
            self.scene.addLine(
                self.margen,
                y,
                self.ancho_mapa - self.margen,
                y,
                pen_calle
            )
            y += separacion

    def _dibujar_pedidos(self):
        """
        Dibuja almacén y pedidos.
        """
        fuente = QFont("Segoe UI", 9)
        fuente.setBold(True)

        almacen_punto = self.puntos_canvas.get("almacen")
        if almacen_punto:
            self.scene.addRect(
                almacen_punto.x() - 12,
                almacen_punto.y() - 12,
                24,
                24,
                QPen(QColor("#1d4ed8")),
                QBrush(QColor("#2563eb"))
            )

            texto = self.scene.addText("Almacén", fuente)
            texto.setDefaultTextColor(QColor("#1d4ed8"))
            texto.setPos(almacen_punto.x() + 14, almacen_punto.y() - 14)

        pedidos = self.datos_json.get("pedidos", [])

        for pedido in pedidos:
            pedido_id = pedido.get("id")
            punto = self.puntos_canvas.get(pedido_id)

            if not punto:
                continue

            color = QColor("#16a34a")

            if pedido.get("ruta_bloqueada"):
                color = QColor("#dc2626")
            elif pedido.get("trafico") == "alto":
                color = QColor("#ea580c")
            elif pedido.get("prioridad") == "alta":
                color = QColor("#7c3aed")

            self.scene.addEllipse(
                punto.x() - 9,
                punto.y() - 9,
                18,
                18,
                QPen(QColor("#111827")),
                QBrush(color)
            )

            etiqueta = self.scene.addText(f"P{pedido_id}", fuente)
            etiqueta.setDefaultTextColor(QColor("#111827"))
            etiqueta.setPos(punto.x() + 10, punto.y() - 14)

    def _dibujar_ruta(self):
        """
        Dibuja la ruta elegida por el agente.

        En lugar de unir puntos con diagonales directas, usa caminos tipo L:
        primero horizontal y luego vertical, simulando calles.
        """
        if not self.ruta:
            return

        puntos_ruta = self._obtener_puntos_de_ruta()

        if len(puntos_ruta) < 2:
            return

        pen_ruta = QPen(QColor("#2563eb"))
        pen_ruta.setWidth(4)

        pen_ruta_fondo = QPen(QColor("#bfdbfe"))
        pen_ruta_fondo.setWidth(10)

        font_orden = QFont("Segoe UI", 10)
        font_orden.setBold(True)

        for i in range(len(puntos_ruta) - 1):
            origen = puntos_ruta[i]
            destino = puntos_ruta[i + 1]

            esquina = QPointF(destino.x(), origen.y())

            self.scene.addLine(
                origen.x(),
                origen.y(),
                esquina.x(),
                esquina.y(),
                pen_ruta_fondo
            )
            self.scene.addLine(
                esquina.x(),
                esquina.y(),
                destino.x(),
                destino.y(),
                pen_ruta_fondo
            )

            self.scene.addLine(
                origen.x(),
                origen.y(),
                esquina.x(),
                esquina.y(),
                pen_ruta
            )
            self.scene.addLine(
                esquina.x(),
                esquina.y(),
                destino.x(),
                destino.y(),
                pen_ruta
            )

            if i > 0:
                orden = self.scene.addText(str(i), font_orden)
                orden.setDefaultTextColor(QColor("#1d4ed8"))
                orden.setPos(origen.x() - 6, origen.y() - 28)

    def _dibujar_agente(self):
        """
        Dibuja el agente como un círculo sobre el almacén.
        """
        origen = self.puntos_canvas.get("almacen")

        if not origen:
            return

        self.agente_item = self.scene.addEllipse(
            QRectF(-10, -10, 20, 20),
            QPen(QColor("#111827")),
            QBrush(QColor("#facc15"))
        )

        self.agente_item.setPos(origen)

        fuente = QFont("Segoe UI", 8)
        fuente.setBold(True)

        self.agente_label = self.scene.addText("Agente", fuente)
        self.agente_label.setDefaultTextColor(QColor("#111827"))
        self.agente_label.setPos(origen.x() + 12, origen.y() - 25)

    # =====================================================
    # ANIMACIÓN
    # =====================================================

    def _obtener_puntos_de_ruta(self):
        """
        Devuelve los puntos de la ruta en orden:
        almacén → pedido 1 → pedido 2 → ...
        """
        puntos = []

        almacen = self.puntos_canvas.get("almacen")

        if almacen:
            puntos.append(almacen)

        for paso in self.ruta:
            pedido_id = paso.get("pedido")
            punto = self.puntos_canvas.get(pedido_id)

            if punto:
                puntos.append(punto)

        return puntos

    def _preparar_animacion(self):
        """
        Crea una lista de puntos intermedios para animar al agente.

        La ruta se mueve por tramos tipo L:
        origen → esquina → destino.
        """
        puntos_ruta = self._obtener_puntos_de_ruta()

        self.puntos_animacion = []

        if len(puntos_ruta) < 2:
            return

        for i in range(len(puntos_ruta) - 1):
            origen = puntos_ruta[i]
            destino = puntos_ruta[i + 1]
            esquina = QPointF(destino.x(), origen.y())

            self._agregar_tramo_animacion(origen, esquina, i)
            self._agregar_tramo_animacion(esquina, destino, i)

    def _agregar_tramo_animacion(self, origen, destino, indice_tramo):
        """
        Agrega puntos intermedios entre origen y destino.
        """
        pasos = 35

        for i in range(pasos):
            t = i / pasos

            x = origen.x() + (destino.x() - origen.x()) * t
            y = origen.y() + (destino.y() - origen.y()) * t

            self.puntos_animacion.append({
                "punto": QPointF(x, y),
                "tramo": indice_tramo
            })

    def iniciar_animacion(self):
        """
        Inicia la animación del agente.
        """
        if not self.puntos_animacion:
            self.lbl_estado.setText("No existe ruta para animar. Primero ejecuta el agente.")
            return

        self.timer.start(30)

    def pausar_animacion(self):
        """
        Pausa la animación.
        """
        self.timer.stop()

    def reiniciar_animacion(self):
        """
        Reinicia la animación al almacén.
        """
        self.timer.stop()
        self.indice_animacion = 0

        origen = self.puntos_canvas.get("almacen")

        if origen and self.agente_item:
            self.agente_item.setPos(origen)
            self.agente_label.setPos(origen.x() + 12, origen.y() - 25)

        self.lbl_estado.setText("Animación reiniciada. El agente está en el almacén.")

    def avanzar_un_paso(self):
        """
        Avanza un solo punto de la animación.
        """
        self._avanzar_animacion()

    def _avanzar_animacion(self):
        """
        Mueve el agente al siguiente punto de la animación.
        """
        if self.indice_animacion >= len(self.puntos_animacion):
            self.timer.stop()
            self.lbl_estado.setText("Ruta completada. El agente terminó las entregas.")
            return

        dato = self.puntos_animacion[self.indice_animacion]
        punto = dato["punto"]
        tramo = dato["tramo"]

        if self.agente_item:
            self.agente_item.setPos(punto)

        if self.agente_label:
            self.agente_label.setPos(punto.x() + 12, punto.y() - 25)

        if tramo < len(self.ruta):
            paso = self.ruta[tramo]
            self.lbl_estado.setText(
                f"El agente se dirige al Pedido P{paso.get('pedido')} - "
                f"{paso.get('destino')} | Decisión: {paso.get('tipo_decision')} | "
                f"Costo: {paso.get('costo')} | Recompensa: {paso.get('recompensa')}"
            )

        self.indice_animacion += 1


# =========================================================
# VENTANA PRINCIPAL
# =========================================================

class VentanaPrincipal(QMainWindow):
    """
    Ventana principal del sistema.

    Desde aquí se controla:
    - entrenamiento;
    - ejecución;
    - reset de Tabla Q;
    - apertura de ventanas secundarias.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Delivery Inteligente con Q-Learning")
        self.resize(980, 720)

        self.datos_json = cargar_datos_originales()
        self.resultado_actual = None

        self._construir_ui()
        self._aplicar_estilos()

    # =====================================================
    # CONSTRUCCIÓN DE UI
    # =====================================================

    def _construir_ui(self):
        """
        Construye la ventana principal.
        """
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)

        header = self._crear_header()
        controles = self._crear_controles()
        metricas = self._crear_metricas()
        botones_ventanas = self._crear_botones_ventanas()
        descripcion = self._crear_descripcion()

        layout.addWidget(header)
        layout.addWidget(controles)
        layout.addWidget(metricas, stretch=1)
        layout.addWidget(botones_ventanas)
        layout.addWidget(descripcion)

        self.setCentralWidget(contenedor)

    def _crear_header(self):
        """
        Crea el encabezado superior.
        """
        frame = QFrame()
        frame.setObjectName("header")

        layout = QVBoxLayout(frame)

        titulo = QLabel("🚚 Delivery Inteligente con Q-Learning")
        titulo.setObjectName("tituloHeader")

        subtitulo = QLabel(
            "Tercer avance: aprendizaje persistente, explicación del agente, mapa animado y Tabla Q"
        )
        subtitulo.setObjectName("subtituloHeader")

        layout.addWidget(titulo)
        layout.addWidget(subtitulo)

        return frame

    def _crear_controles(self):
        """
        Crea los campos de configuración y botones principales.
        """
        grupo = QGroupBox("Control de entrenamiento")
        layout = QGridLayout(grupo)

        self.spin_episodios = QSpinBox()
        self.spin_episodios.setMinimum(1)
        self.spin_episodios.setMaximum(1000)
        self.spin_episodios.setValue(1)
        self.spin_episodios.setToolTip(
            "Cantidad de veces que el agente repetirá la simulación para aprender."
        )

        self.spin_epsilon = QDoubleSpinBox()
        self.spin_epsilon.setMinimum(0.0)
        self.spin_epsilon.setMaximum(1.0)
        self.spin_epsilon.setSingleStep(0.05)
        self.spin_epsilon.setValue(0.30)
        self.spin_epsilon.setToolTip(
            "Probabilidad de exploración. Alto = prueba rutas nuevas. Bajo = usa lo aprendido."
        )

        self.btn_entrenar = QPushButton("Entrenar agente")
        self.btn_ejecutar = QPushButton("Ejecutar con aprendizaje guardado")
        self.btn_reset = QPushButton("Resetear Tabla Q")

        self.btn_entrenar.clicked.connect(self.entrenar_agente)
        self.btn_ejecutar.clicked.connect(self.ejecutar_con_aprendizaje)
        self.btn_reset.clicked.connect(self.resetear_tabla_q)

        layout.addWidget(QLabel("Episodios:"), 0, 0)
        layout.addWidget(self.spin_episodios, 0, 1)

        layout.addWidget(QLabel("Epsilon:"), 1, 0)
        layout.addWidget(self.spin_epsilon, 1, 1)

        layout.addWidget(self.btn_entrenar, 0, 2)
        layout.addWidget(self.btn_ejecutar, 1, 2)
        layout.addWidget(self.btn_reset, 2, 2)

        return grupo

    def _crear_metricas(self):
        """
        Crea el área de resumen rápido.

        Ahora usa QScrollArea para que las cards no se pierdan
        cuando la ventana es pequeña o cuando se agreguen más métricas.
        """
        grupo = QGroupBox("Resumen del último resultado")
        layout_principal = QVBoxLayout(grupo)

        self.scroll_metricas = QScrollArea()
        self.scroll_metricas.setWidgetResizable(True)
        self.scroll_metricas.setMinimumHeight(210)

        contenido = QWidget()
        layout = QGridLayout(contenido)

        self.card_episodios = TarjetaMetrica("Episodios", "-")
        self.card_valores_q = TarjetaMetrica("Valores Tabla Q", "-", COLOR_NARANJA)
        self.card_mejor_costo = TarjetaMetrica("Mejor costo", "-", COLOR_VERDE)
        self.card_recompensa = TarjetaMetrica("Mejor recompensa", "-", COLOR_AZUL)
        self.card_entregas = TarjetaMetrica("Entregas completadas", "-", COLOR_ROJO)
        self.card_archivo = TarjetaMetrica("Archivo Q", "q_table.pkl", COLOR_NARANJA)

        layout.addWidget(self.card_episodios, 0, 0)
        layout.addWidget(self.card_valores_q, 0, 1)
        layout.addWidget(self.card_mejor_costo, 1, 0)
        layout.addWidget(self.card_recompensa, 1, 1)
        layout.addWidget(self.card_entregas, 2, 0)
        layout.addWidget(self.card_archivo, 2, 1)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        self.scroll_metricas.setWidget(contenido)
        layout_principal.addWidget(self.scroll_metricas)

        return grupo

    def _crear_botones_ventanas(self):
        """
        Crea botones para abrir ventanas secundarias.
        """
        grupo = QGroupBox("Ventanas de análisis")
        layout = QGridLayout(grupo)

        self.btn_pedidos = QPushButton("Ver pedidos")
        self.btn_mapa = QPushButton("Ver mapa animado")
        self.btn_aprendizaje = QPushButton("Ver aprendizaje detallado")
        self.btn_tabla_q = QPushButton("Ver Tabla Q")

        self.btn_pedidos.clicked.connect(self.abrir_pedidos)
        self.btn_mapa.clicked.connect(self.abrir_mapa)
        self.btn_aprendizaje.clicked.connect(self.abrir_aprendizaje)
        self.btn_tabla_q.clicked.connect(self.abrir_tabla_q)

        layout.addWidget(self.btn_pedidos, 0, 0)
        layout.addWidget(self.btn_mapa, 0, 1)
        layout.addWidget(self.btn_aprendizaje, 1, 0)
        layout.addWidget(self.btn_tabla_q, 1, 1)

        return grupo

    def _crear_descripcion(self):
        """
        Explica cómo interpretar los valores.
        """
        texto = QPlainTextEdit()
        texto.setReadOnly(True)
        texto.setMaximumHeight(155)

        texto.setPlainText(
            "Interpretación rápida:\n"
            "- 1 episodio = el agente empieza en el almacén y entrega a todos los pedidos disponibles una vez.\n"
            "- Costo de Ruta bajo = ruta más eficiente.\n"
            "- Recompensa alta = buena decisión del agente.\n"
            "- Valor Q alto = el agente aprendió que esa acción conviene en ese estado.\n"
            "- Epsilon alto = más exploración; epsilon bajo = más uso de lo aprendido.\n\n"
            "El mapa animado es una simulación offline. No representa calles reales, "
            "sino el orden de entrega elegido por el agente en un entorno visual tipo tablero."
        )

        return texto

    # =====================================================
    # ACCIONES PRINCIPALES
    # =====================================================

    def entrenar_agente(self):
        """
        Entrena al agente con los episodios y epsilon elegidos.
        """
        episodios = self.spin_episodios.value()
        epsilon = self.spin_epsilon.value()

        self._ejecutar_simulacion(
            episodios=episodios,
            epsilon=epsilon,
            resetear_q=False
        )

    def ejecutar_con_aprendizaje(self):
        """
        Ejecuta usando la Tabla Q guardada, respetando la cantidad
        de episodios escrita por el usuario en la interfaz.

        Se usa epsilon bajo para que el agente use principalmente
        lo que ya aprendió.
        """
        episodios = self.spin_episodios.value()

        self._ejecutar_simulacion(
            episodios=episodios,
            epsilon=0.05,
            resetear_q=False
        )

    def resetear_tabla_q(self):
        """
        Borra la Tabla Q guardada.
        """
        respuesta = QMessageBox.question(
            self,
            "Resetear Tabla Q",
            "¿Seguro que deseas borrar el aprendizaje guardado?",
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:
            resultado = resetear_aprendizaje()

            self.resultado_actual = None

            self.card_episodios.set_valor("-")
            self.card_valores_q.set_valor("-")
            self.card_mejor_costo.set_valor("-")
            self.card_recompensa.set_valor("-")
            self.card_entregas.set_valor("-")

            QMessageBox.information(
                self,
                "Tabla Q",
                resultado.get("mensaje", "Tabla Q reiniciada.")
            )

    def _ejecutar_simulacion(self, episodios, epsilon, resetear_q):
        """
        Llama al backend principal y actualiza métricas.
        """
        try:
            self.resultado_actual = ejecutar_simulacion_beta(
                episodios=episodios,
                guardar_q=True,
                resetear_q=resetear_q,
                epsilon=epsilon
            )

            self._actualizar_resumen()

            QMessageBox.information(
                self,
                "Simulación terminada",
                "La simulación se ejecutó correctamente."
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Error",
                f"Ocurrió un error durante la simulación:\n\n{error}"
            )

    def _actualizar_resumen(self):
        """
        Actualiza las tarjetas de resumen en la ventana principal.
        """
        resultado = self.resultado_actual

        if not resultado:
            return

        mejor = resultado.get("mejor_ruta")

        self.card_episodios.set_valor(len(resultado.get("resultados", [])))
        self.card_valores_q.set_valor(resultado.get("cantidad_valores_q", 0))

        if mejor:
            self.card_mejor_costo.set_valor(mejor.get("costo_total"))
            self.card_recompensa.set_valor(mejor.get("recompensa_total"))
            self.card_entregas.set_valor(mejor.get("entregas_completadas"))

    # =====================================================
    # ABRIR VENTANAS SECUNDARIAS
    # =====================================================

    def abrir_pedidos(self):
        """
        Abre ventana de pedidos.
        """
        ventana = VentanaPedidos(self.datos_json, self)
        ventana.exec()

    def abrir_mapa(self):
        """
        Abre ventana de mapa animado.
        """
        if not self.resultado_actual:
            QMessageBox.warning(
                self,
                "Sin simulación",
                "Primero debes entrenar o ejecutar el agente."
            )
            return

        ventana = VentanaMapa(self.datos_json, self.resultado_actual, self)
        ventana.exec()

    def abrir_aprendizaje(self):
        """
        Abre ventana de aprendizaje detallado.
        """
        if not self.resultado_actual:
            QMessageBox.warning(
                self,
                "Sin simulación",
                "Primero debes entrenar o ejecutar el agente."
            )
            return

        ventana = VentanaAprendizaje(self.resultado_actual, self)
        ventana.exec()

    def abrir_tabla_q(self):
        """
        Abre ventana de Tabla Q.
        """
        if not self.resultado_actual:
            QMessageBox.warning(
                self,
                "Sin simulación",
                "Primero debes entrenar o ejecutar el agente."
            )
            return

        ventana = VentanaTablaQ(self.resultado_actual, self)
        ventana.exec()

    # =====================================================
    # ESTILOS
    # =====================================================

    def _aplicar_estilos(self):
        """
        Aplica estilo visual general.
        """
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLOR_FONDO};
            }}

            QDialog {{
                background-color: {COLOR_FONDO};
            }}

            QWidget {{
                font-family: Segoe UI;
                font-size: 13px;
                color: {COLOR_TEXTO};
            }}

            QFrame#header {{
                background-color: {COLOR_HEADER};
                border-radius: 0px;
                padding: 12px;
            }}

            QLabel#tituloHeader {{
                color: white;
                font-size: 28px;
                font-weight: bold;
            }}

            QLabel#subtituloHeader {{
                color: #c7d2fe;
                font-size: 13px;
            }}

            QLabel#tituloVentana {{
                font-size: 22px;
                font-weight: bold;
                color: {COLOR_HEADER};
            }}

            QLabel#notaImportante {{
                background-color: #fff7ed;
                border: 1px solid #fed7aa;
                border-radius: 8px;
                padding: 8px;
                color: #9a3412;
            }}

            QGroupBox {{
                background-color: {COLOR_CARD};
                border: 1px solid #d1d5db;
                border-radius: 10px;
                margin-top: 12px;
                padding: 10px;
                font-weight: bold;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }}

            QPushButton {{
                background-color: {COLOR_AZUL};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px 14px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: {COLOR_AZUL_OSCURO};
            }}

            QPlainTextEdit {{
                background-color: #f8fafc;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 8px;
                font-family: Consolas;
                font-size: 12px;
            }}

            QTableWidget {{
                background-color: white;
                border: 1px solid #d1d5db;
                gridline-color: #e5e7eb;
            }}

            QHeaderView::section {{
                background-color: #e5e7eb;
                padding: 6px;
                border: 1px solid #d1d5db;
                font-weight: bold;
            }}

            QFrame#tarjetaMetrica {{
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                padding: 8px;
            }}

            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)


# =========================================================
# EJECUCIÓN
# =========================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    ventana = VentanaPrincipal()
    ventana.show()

    sys.exit(app.exec())