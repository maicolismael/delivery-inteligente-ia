"""
test_1_recompensas.py
Verifica que la recompensa cambia segun la posicion actual.
Si el fix es correcto, misma entrega desde distintas posiciones = distinto costo.

Correr desde la raiz del proyecto:
    python test_1_recompensas.py
"""

import sys
sys.path.insert(0, ".")

from src.recompensas import calcular_costo_ruta, calcular_recompensa

# Pedido de prueba: Juan Perez, lat=-12.0895, lng=-77.0087
pedido = {
    "id": 1,
    "cliente_nombre": "Juan Pérez",
    "distancia_km": 3.5,
    "tiempo_estimado_min": 15,
    "trafico": "bajo",
    "ruta_bloqueada": False,
    "prioridad": "alta",
    "coordenadas": {"lat": -12.0895, "lng": -77.0087}
}

print("=" * 55)
print("TEST 1: recompensa varía con la posición")
print("=" * 55)

# Caso A: desde el almacen (cerca del cliente)
pos_almacen = (-12.0464, -77.0428)
cr_almacen  = calcular_costo_ruta(pedido, pos_actual_coords=pos_almacen)
r_almacen   = calcular_recompensa(pedido, True, pos_actual_coords=pos_almacen)

# Caso B: desde un punto lejano (sur de la ciudad)
pos_lejana = (-12.1585, -76.9925)
cr_lejano  = calcular_costo_ruta(pedido, pos_actual_coords=pos_lejana)
r_lejano   = calcular_recompensa(pedido, True, pos_actual_coords=pos_lejana)

# Caso C: sin coordenadas (comportamiento anterior)
cr_sin_pos = calcular_costo_ruta(pedido, pos_actual_coords=None)
r_sin_pos  = calcular_recompensa(pedido, True, pos_actual_coords=None)

print(f"\nDesde almacén  → CR={cr_almacen:.2f}  | R={r_almacen:.2f}")
print(f"Desde lejos    → CR={cr_lejano:.2f}  | R={r_lejano:.2f}")
print(f"Sin coords     → CR={cr_sin_pos:.2f}  | R={r_sin_pos:.2f}  (compatibilidad)")

# Verificaciones
assert cr_lejano > cr_almacen, "FALLO: desde lejos debe costar mas"
assert r_lejano  < r_almacen,  "FALLO: desde lejos debe dar menor recompensa"
assert cr_sin_pos == 3.5 + 15/10 + (-3), "FALLO: sin coords usa distancia_km fija"

print("\n✓ Todos los tests pasaron")
print("  La recompensa ahora depende de la posición del agente")