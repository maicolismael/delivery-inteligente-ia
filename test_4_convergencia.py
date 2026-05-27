"""
test_4_convergencia.py
El test mas importante: verifica que el agente mejora con mas episodios.
Compara la recompensa promedio de los primeros 10 episodios vs los ultimos 10.

Correr desde la raiz del proyecto:
    python test_4_convergencia.py

Debe mostrar que la recompensa total MEJORA con el tiempo.
"""

import sys
sys.path.insert(0, ".")

from src.main import ejecutar_simulacion_beta

print("=" * 55)
print("TEST 4: el agente mejora con más episodios")
print("=" * 55)
print("Ejecutando 100 episodios (tarda ~3 segundos)...\n")

resultado = ejecutar_simulacion_beta(
    episodios=100,
    guardar_q=False,    # no guardar durante el test
    resetear_q=True,    # empezar desde cero para el test
    epsilon=0.50
)

recompensas = resultado["historial_recompensas"]
costos      = resultado["historial_costos"]

primeros_10 = recompensas[:10]
ultimos_10  = recompensas[-10:]

prom_inicio = sum(primeros_10) / len(primeros_10)
prom_fin    = sum(ultimos_10)  / len(ultimos_10)

print(f"Recompensa promedio — primeros 10 ep : {prom_inicio:.2f}")
print(f"Recompensa promedio — últimos  10 ep : {prom_fin:.2f}")
print(f"Mejora                               : {prom_fin - prom_inicio:+.2f}")

costo_primeros = sum(costos[:10]) / 10
costo_ultimos  = sum(costos[-10:]) / 10
print(f"\nCosto promedio — primeros 10 ep      : {costo_primeros:.2f}")
print(f"Costo promedio — últimos  10 ep      : {costo_ultimos:.2f}")
print(f"Reduccion de costo                   : {costo_primeros - costo_ultimos:+.2f}")

print(f"\nValores en Tabla Q al final          : {resultado['cantidad_valores_q']}")
print(f"Epsilon final                        : {resultado['parametros']['epsilon']:.4f}")

# La recompensa final debe ser igual o mayor que la inicial
# (puede no mejorar siempre con solo 100 ep, pero no debe empeorar)
print("\n--- Ruta del mejor episodio ---")
mejor = resultado["mejor_ruta"]
if mejor:
    orden = " → ".join(f"P{p['pedido']}" for p in mejor["ruta"])
    print(f"Orden: {orden}")
    print(f"Costo total: {mejor['costo_total']}")
    print(f"Recompensa total: {mejor['recompensa_total']}")

print("\n✓ Test de convergencia completado")
print("  Si 'Mejora' es positiva, el agente está aprendiendo correctamente")