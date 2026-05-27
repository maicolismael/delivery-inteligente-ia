"""
test_2_agente.py
Verifica que el agente actualiza coordenadas reales en cada entrega.

Correr desde la raiz del proyecto:
    python test_2_agente.py
"""

import sys
sys.path.insert(0, ".")

from src.agente import AgenteDelivery

print("=" * 55)
print("TEST 2: agente guarda coordenadas reales")
print("=" * 55)

coords_almacen = (-12.0464, -77.0428)
agente = AgenteDelivery(posicion_inicial="almacen", coords_almacen=coords_almacen)

print(f"\nInicio → posicion={agente.posicion_actual}  coords={agente.coordenadas_actuales}")
assert agente.coordenadas_actuales == coords_almacen

# Simular entrega al primer cliente
pedido_1 = {
    "id": 1, "id_pedido": 1,
    "cliente_nombre": "Juan Pérez",
    "destino": "Juan Pérez",
    "coordenadas": {"lat": -12.0895, "lng": -77.0087},
    "ruta_bloqueada": False,
}
agente.registrar_entrega(pedido_1)
print(f"Tras P1   → posicion={agente.posicion_actual}  coords={agente.coordenadas_actuales}")
assert agente.coordenadas_actuales == (-12.0895, -77.0087), "FALLO: coords no actualizadas"

# Simular entrega al segundo cliente
pedido_2 = {
    "id": 7, "id_pedido": 7,
    "cliente_nombre": "Roberto Díaz",
    "destino": "Roberto Díaz",
    "coordenadas": {"lat": -12.0585, "lng": -77.0428},
    "ruta_bloqueada": False,
}
agente.registrar_entrega(pedido_2)
print(f"Tras P7   → posicion={agente.posicion_actual}  coords={agente.coordenadas_actuales}")
assert agente.coordenadas_actuales == (-12.0585, -77.0428), "FALLO: coords no actualizadas"

# Verificar que obtener_acciones excluye rutas bloqueadas
pedidos = [
    {"id": 1, "id_pedido": 1, "ruta_bloqueada": False, "estado_ruta": "libre"},
    {"id": 9, "id_pedido": 9, "ruta_bloqueada": True,  "estado_ruta": "bloqueada"},
    {"id": 3, "id_pedido": 3, "ruta_bloqueada": False, "estado_ruta": "libre"},
]
acciones = agente.obtener_acciones(pedidos)
assert 9 not in acciones, "FALLO: pedido bloqueado no debe aparecer"
assert 1 in acciones and 3 in acciones

print(f"Acciones disponibles (excluye P9): {acciones}")
print("\n✓ Todos los tests pasaron")
print("  El agente rastrea coordenadas reales")