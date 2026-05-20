
---

## docs/informe.md → Punto V

```md
# V. Interfaz gráfica y visualización de resultados

## 5.1 Descripción general

Se desarrolló una interfaz gráfica moderna utilizando la librería CustomTkinter para visualizar el funcionamiento del sistema de despacho inteligente.

La interfaz permite:

- Visualizar pedidos registrados
- Ejecutar simulaciones
- Mostrar resultados del agente Q-Learning
- Presentar métricas de desempeño
- Analizar recompensas y costos

---

# 5.2 Componentes principales

## Panel de pedidos

Muestra todos los pedidos cargados desde el archivo JSON con información como:

- ID
- Cliente
- Dirección
- Prioridad
- Tráfico
- Distancia
- Tiempo estimado
- Estado de entrega

Inicialmente los pedidos aparecen como:

```text
pendiente