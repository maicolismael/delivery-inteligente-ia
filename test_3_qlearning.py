"""
test_3_qlearning.py
Verifica que epsilon decae y que el desempate es aleatorio.

Correr desde la raiz del proyecto:
    python test_3_qlearning.py
"""

import sys
sys.path.insert(0, ".")

from src.qlearning import QLearningDelivery

print("=" * 55)
print("TEST 3: epsilon decay y desempate aleatorio")
print("=" * 55)

ql = QLearningDelivery(alpha=0.1, gamma=0.9, epsilon=0.50)

# -- Test decaimiento de epsilon --
epsilon_inicio = ql.epsilon
for _ in range(200):
    ql.decaer_epsilon(tasa=0.99, minimo=0.05)

print(f"\nEpsilon inicio : {epsilon_inicio:.3f}")
print(f"Epsilon tras 200 episodios (tasa=0.99): {ql.epsilon:.4f}")
assert ql.epsilon < epsilon_inicio, "FALLO: epsilon no decayo"
assert ql.epsilon >= 0.05,          "FALLO: epsilon bajo el minimo"
print("✓ Epsilon decayó correctamente")

# -- Test desempate con tabla vacia --
# Todos los Q = 0, la eleccion debe variar entre episodios
ql2     = QLearningDelivery(epsilon=0.0)  # sin exploracion para aislar el test
estado  = ("almacen", (1, 2, 3, 4, 5))
acciones = [1, 2, 3, 4, 5]

elegidos = set()
for _ in range(100):
    d = ql2.elegir_accion_detallada(estado, acciones)
    elegidos.add(d["accion"])

print(f"\nAcciones elegidas en 100 llamadas con Q=0: {sorted(elegidos)}")
assert len(elegidos) > 1, "FALLO: con Q=0 siempre elige lo mismo (sin desempate)"
print("✓ Desempate aleatorio funciona")

# -- Test que Q crece con buenas recompensas --
ql3 = QLearningDelivery(alpha=0.1, gamma=0.9, epsilon=0.0)
est  = ("almacen", (1,))
est2 = ("Juan", ())

for _ in range(20):
    ql3.actualizar_q(est, 1, recompensa=90.0, nuevo_estado=est2, nuevas_acciones=[])

q_final = ql3.obtener_valor_q(est, 1)
print(f"\nQ tras 20 actualizaciones con R=90: {q_final:.4f}")
assert q_final > 0, "FALLO: Q no creció con recompensas positivas"
print("✓ Tabla Q aprende con recompensas positivas")

print("\n✓ Todos los tests pasaron")