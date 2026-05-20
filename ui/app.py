"""
app.py - Interfaz CustomTkinter para el Sistema de Despacho Inteligente
Dashboard moderno + métricas Q-Learning
Ejecutar: python ui/app.py
"""

import sys
import os
import threading

# ─────────────────────────────────────────────────────────────
# RUTAS
# ─────────────────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

# ─────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────
import customtkinter as ctk

from metricas import (
    simular_pedidos,
    resumen_simulacion,
    cargar_datos
)

from src.main import ejecutar_simulacion_beta
from src.recompensas import (
    calcular_costo_ruta,
    calcular_recompensa
)

# ─────────────────────────────────────────────────────────────
# TEMA
# ─────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ─────────────────────────────────────────────────────────────
# COLORES
# ─────────────────────────────────────────────────────────────
C_BG          = "#f4f6f9"
C_CARD        = "#ffffff"
C_HEADER      = "#1a1a2e"

C_TEXT        = "#222222"
C_SUBTEXT     = "#6c757d"

C_BLUE        = "#2563eb"
C_GREEN       = "#16a34a"
C_RED         = "#dc2626"
C_ORANGE      = "#ea580c"
C_YELLOW      = "#ca8a04"

# ─────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────
class App(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.title("Sistema de Despacho Inteligente")
        self.geometry("1450x900")
        self.minsize(1200, 720)

        self.configure(fg_color=C_BG)

        self._pedidos_metricas = []
        self._resumen = {}
        self._resultado_qlearn = None
        self._datos_json = {}

        self._build_ui()
        self._cargar_datos()

    # =========================================================
    # UI
    # =========================================================

    def _build_ui(self):

        # HEADER
        header = ctk.CTkFrame(
            self,
            fg_color=C_HEADER,
            height=85,
            corner_radius=0
        )

        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="🚚 Sistema de Despacho Inteligente",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="white"
        ).pack(anchor="w", padx=25, pady=(14, 0))

        ctk.CTkLabel(
            header,
            text="Agente Q-Learning para optimización de entregas",
            font=ctk.CTkFont(size=13),
            text_color="#b8c1ec"
        ).pack(anchor="w", padx=28)

        # BODY
        body = ctk.CTkFrame(self, fg_color=C_BG)
        body.pack(fill="both", expand=True, padx=15, pady=15)

        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)

        body.rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_right(body)

    # =========================================================
    # PANEL IZQUIERDO
    # =========================================================

    def _build_left(self, parent):

        frame = ctk.CTkFrame(
            parent,
            fg_color=C_CARD,
            corner_radius=16
        )

        frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )

        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(0, weight=1)

        # ALMACEN
        self.lbl_almacen = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=C_GREEN
        )

        self.lbl_almacen.grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=(15, 5)
        )

        # TITULO
        ctk.CTkLabel(
            frame,
            text="📋 Pedidos registrados",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=C_HEADER
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=20,
            pady=(5, 10)
        )

        # TABLA
        self.tabla = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(
                family="Courier New",
                size=11
            ),
            fg_color="#f8fafc",
            text_color=C_TEXT,
            border_width=1,
            border_color="#dbe2ea",
            corner_radius=12
        )

        self.tabla.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=15,
            pady=10
        )

        # BOTON
        self.btn_simular = ctk.CTkButton(
            frame,
            text="▶ Ejecutar simulación",
            height=48,
            corner_radius=12,
            fg_color=C_BLUE,
            hover_color="#1d4ed8",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            ),
            command=self._ejecutar_simulacion
        )

        self.btn_simular.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=15,
            pady=15
        )

    # =========================================================
    # PANEL DERECHO
    # =========================================================

    def _build_right(self, parent):

        frame = ctk.CTkFrame(
            parent,
            fg_color=C_CARD,
            corner_radius=16
        )

        frame.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        frame.columnconfigure(0, weight=1)

        # TITULO
        ctk.CTkLabel(
            frame,
            text="🤖 Resultado del agente",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=C_HEADER
        ).pack(anchor="w", padx=20, pady=(20, 10))

        # COMBO
        self.combo = ctk.CTkComboBox(
            frame,
            values=["Ejecuta la simulación"],
            state="disabled",
            command=self._mostrar_detalle
        )

        self.combo.pack(fill="x", padx=20)

        # DETALLE
        self.detalle = ctk.CTkTextbox(
            frame,
            height=260,
            font=ctk.CTkFont(
                family="Courier New",
                size=12
            ),
            fg_color="#eef4ff",
            text_color="#1e3a8a",
            corner_radius=12
        )

        self.detalle.pack(
            fill="x",
            padx=20,
            pady=15
        )

        # METRICAS
        ctk.CTkLabel(
            frame,
            text="📈 Métricas básicas",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=C_HEADER
        ).pack(anchor="w", padx=20)

        self.metricas_frame = ctk.CTkScrollableFrame(
            frame,
            fg_color=C_BG,
            corner_radius=12
        )

        self.metricas_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

    # =========================================================
    # CARGAR DATOS
    # =========================================================

    def _cargar_datos(self):

        self._datos_json = cargar_datos()

        alm = self._datos_json["almacen"]

        self.lbl_almacen.configure(
            text=(
                f"📦 Almacén: {alm['direccion']}   "
                f"| Lat: {alm['coordenadas']['lat']}   "
                f"| Lng: {alm['coordenadas']['lng']}"
            )
        )

        self._refrescar_tabla(
            self._datos_json["pedidos"]
        )

    # =========================================================
    # TABLA
    # =========================================================

    def _refrescar_tabla(self, pedidos):

        lineas = []

        sep = "─" * 120

        lineas.append(sep)

        lineas.append(
            f"{'ID':<4}"
            f"{'Cliente':<22}"
            f"{'Prioridad':<12}"
            f"{'Tráfico':<12}"
            f"{'Distancia':<12}"
            f"{'Tiempo':<12}"
            f"{'Estado':<15}"
        )

        lineas.append(sep)

        for p in pedidos:

            lineas.append(
                f"{str(p['id']):<4}"
                f"{p['cliente_nombre'][:20]:<22}"
                f"{p['prioridad']:<12}"
                f"{p['trafico']:<12}"
                f"{str(p['distancia_km']) + ' km':<12}"
                f"{str(p['tiempo_estimado_min']) + ' min':<12}"
                f"{p['estado']:<15}"
            )

        lineas.append(sep)

        self.tabla.delete("1.0", "end")
        self.tabla.insert("end", "\n".join(lineas))

    # =========================================================
    # SIMULACION
    # =========================================================

    def _ejecutar_simulacion(self):

        self.btn_simular.configure(
            state="disabled",
            text="⏳ Simulando..."
        )

        threading.Thread(
            target=self._simular,
            daemon=True
        ).start()

    def _simular(self):

        # METRICAS
        self._pedidos_metricas = simular_pedidos()

        self._resumen = resumen_simulacion(
            self._pedidos_metricas
        )

        # Q LEARNING
        self._resultado_qlearn = ejecutar_simulacion_beta(
            episodios=3
        )

        self.after(0, self._post_simulacion)

    # =========================================================
    # POST SIMULACION
    # =========================================================

    def _post_simulacion(self):

        # ACTUALIZAR ESTADOS
        pedidos_actualizados = []

        for p in self._pedidos_metricas:

            pedidos_actualizados.append({
                "id": p["ID"],
                "cliente_nombre": p["Cliente"],
                "direccion": p["Dirección"],
                "prioridad": p["Prioridad"],
                "trafico": p["Tráfico"].lower(),
                "ruta_bloqueada": p["Bloqueada"] == "⚠️ Sí",
                "distancia_km": p["Distancia (km)"],
                "tiempo_estimado_min": p["Tiempo (min)"],
                "estado": "entregado"
            })

        self._refrescar_tabla(
            pedidos_actualizados
        )

        # COMBO
        opciones = [
            f"P{p['ID']:02d} — {p['Cliente']}"
            for p in self._pedidos_metricas
        ]

        self.combo.configure(
            values=opciones,
            state="normal"
        )

        self.combo.set(opciones[0])

        self._mostrar_detalle(opciones[0])

        self._mostrar_metricas()

        self.btn_simular.configure(
            state="normal",
            text="▶ Ejecutar simulación"
        )

    # =========================================================
    # DETALLE
    # =========================================================

    def _mostrar_detalle(self, seleccion):

        pid = int(seleccion[1:3])

        pedido = next(
            p for p in self._pedidos_metricas
            if p["ID"] == pid
        )

        m = pedido["_metricas"]

        pedido_real = next(
            (x for x in self._datos_json["pedidos"] if x["id"] == m.id),
            {}
        )

        recompensa = calcular_recompensa(
            pedido_real,
            True
        )

        costo = calcular_costo_ruta(
            pedido_real
        )

        texto = f"""
ID:                 {m.id}

Cliente:            {m.cliente}

Dirección:          {pedido['Dirección']}

Prioridad:          {pedido['Prioridad']}

Tráfico:            {m.trafico}

Ruta bloqueada:     {'Sí' if m.ruta_bloqueada else 'No'}

Distancia:          {m.distancia_km} km

Tiempo estimado:    {m.tiempo_minutos} min

Penalización:       Bs. {m.penalizacion}

Costo Ruta:         Bs. {m.costo_ruta}

Recompensa:         {round(recompensa, 2)}

Costo Agente:       {round(costo, 2)}

Estado:             ENTREGADO
"""

        self.detalle.delete("1.0", "end")
        self.detalle.insert("end", texto)

    # =========================================================
    # TARJETA
    # =========================================================

    def _crear_tarjeta(self, fila, columna, titulo, valor, color):

        card = ctk.CTkFrame(
            self.metricas_frame,
            fg_color=C_CARD,
            corner_radius=12,
            border_width=2,
            border_color=color
        )

        card.grid(
            row=fila,
            column=columna,
            padx=8,
            pady=8,
            sticky="ew"
        )

        ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(size=12),
            text_color=C_SUBTEXT
        ).pack(anchor="w", padx=12, pady=(10, 0))

        ctk.CTkLabel(
            card,
            text=str(valor),
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            ),
            text_color=color
        ).pack(anchor="w", padx=12, pady=(0, 10))

    # =========================================================
    # METRICAS
    # =========================================================

    def _mostrar_metricas(self):

        for w in self.metricas_frame.winfo_children():
            w.destroy()

        r = self._resumen

        self.metricas_frame.columnconfigure(0, weight=1)
        self.metricas_frame.columnconfigure(1, weight=1)

        tarjetas = [

            ("Total pedidos", r["total_pedidos"], C_BLUE),

            ("Costo total", f"Bs. {r['costo_total']}", C_GREEN),

            ("Distancia total", f"{r['distancia_total']} km", C_ORANGE),

            ("Cumplimiento", f"{r['tasa_cumplimiento']} %", C_BLUE),

            ("Costo promedio", f"Bs. {r['costo_promedio']}", C_GREEN),

            ("Tiempo promedio", f"{r['tiempo_promedio']} min", C_ORANGE),

            ("En tiempo", r["pedidos_en_tiempo"], C_GREEN),

            ("Con demora", r["pedidos_con_demora"], C_RED),

            ("Rutas bloqueadas", r["rutas_bloqueadas"], C_YELLOW)

        ]

        for i, (titulo, valor, color) in enumerate(tarjetas):

            self._crear_tarjeta(
                i // 2,
                i % 2,
                titulo,
                valor,
                color
            )

        # =====================================================
        # Q LEARNING
        # =====================================================

        if self._resultado_qlearn:

            q = self._resultado_qlearn

            total_recompensa = sum(
                ep["recompensa_total"]
                for ep in q["resultados"]
            )

            total_costo = sum(
                ep["costo_total"]
                for ep in q["resultados"]
            )

            cantidad_q = q["cantidad_valores_q"]

            fila_base = (len(tarjetas) // 2) + 1

            self._crear_tarjeta(
                fila_base,
                0,
                "Recompensa Q-Learning",
                round(total_recompensa, 2),
                C_GREEN
            )

            self._crear_tarjeta(
                fila_base,
                1,
                "Costo Q-Learning",
                round(total_costo, 2),
                C_BLUE
            )

            self._crear_tarjeta(
                fila_base + 1,
                0,
                "Valores Tabla Q",
                cantidad_q,
                C_ORANGE
            )

            episodios = len(q["resultados"])

            self._crear_tarjeta(
                fila_base + 1,
                1,
                "Episodios",
                episodios,
                C_RED
            )

            # =============================================
            # DETALLE EPISODIOS
            # =============================================

            titulo = ctk.CTkLabel(
                self.metricas_frame,
                text="🧠 Episodios del Agente Q-Learning",
                font=ctk.CTkFont(
                    size=15,
                    weight="bold"
                ),
                text_color=C_HEADER
            )

            titulo.grid(
                row=fila_base + 2,
                column=0,
                columnspan=2,
                sticky="w",
                padx=8,
                pady=(20, 10)
            )

            fila = fila_base + 3

            for ep in q["resultados"]:

                frame_ep = ctk.CTkFrame(
                    self.metricas_frame,
                    fg_color="#eef4ff",
                    corner_radius=12,
                    border_width=1,
                    border_color="#c7d7fe"
                )

                frame_ep.grid(
                    row=fila,
                    column=0,
                    columnspan=2,
                    sticky="ew",
                    padx=8,
                    pady=6
                )

                acciones = []

                for paso in ep["ruta"]:
                    acciones.append(
                        f"P{paso['pedido']}"
                    )

                acciones_txt = " ➜ ".join(acciones)

                texto = (
                    f"📘 Episodio {ep['episodio']}\n\n"
                    f"🚚 Entregas completadas: {ep['entregas_completadas']}\n"
                    f"🏆 Recompensa total: {ep['recompensa_total']}\n"
                    f"💰 Costo total: {ep['costo_total']}\n"
                    f"🧭 Acciones elegidas: {acciones_txt}"
                )

                ctk.CTkLabel(
                    frame_ep,
                    text=texto,
                    justify="left",
                    anchor="w",
                    font=ctk.CTkFont(
                        family="Courier New",
                        size=11
                    ),
                    text_color=C_TEXT
                ).pack(
                    fill="x",
                    padx=15,
                    pady=12
                )

                fila += 1


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":

    app = App()

    app.mainloop()