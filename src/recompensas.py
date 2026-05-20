"""
Módulo de cálculo de recompensas para el sistema de delivery con Q-Learning.

Este módulo implementa las funciones para calcular el costo de ruta (CR) y
las recompensas del agente basándose en las características de los pedidos.
"""

from typing import Dict, Union


def calcular_costo_ruta(pedido: Dict) -> float:
    """
    Calcula el Costo de Ruta (CR) para un pedido específico.
    
    El CR representa cuán costoso es entregar un pedido, considerando:
    - Distancia a recorrer
    - Tiempo estimado (normalizado)
    - Penalizaciones por tráfico alto, rutas bloqueadas, etc.
    - Bonificaciones por prioridad alta (para incentivar entregas prioritarias)
    
    Fórmula: CR = distancia + (tiempo / 10) + penalizaciones
    
    Args:
        pedido: Diccionario con los datos del pedido. Debe contener:
            - distancia_km (float): Distancia en kilómetros
            - tiempo_estimado_min (int): Tiempo estimado en minutos
            - trafico (str): Nivel de tráfico ("bajo", "medio", "alto")
            - ruta_bloqueada (bool): Si la ruta está bloqueada
            - prioridad (str, opcional): Prioridad del pedido ("alta", "media", "baja")
    
    Returns:
        float: Valor del Costo de Ruta (CR). Valores más bajos indican rutas más favorables.
    """
    # Extraer valores del pedido con valores por defecto para robustez
    distancia = pedido.get('distancia_km', 0)
    tiempo = pedido.get('tiempo_estimado_min', 0)
    trafico = pedido.get('trafico', 'bajo').lower()
    ruta_bloqueada = pedido.get('ruta_bloqueada', False)
    prioridad = pedido.get('prioridad', 'media').lower()
    
    # Calcular componentes base del costo
    costo_distancia = distancia
    costo_tiempo = tiempo / 10  # Normalizado para que no domine sobre distancia
    
    # Calcular penalizaciones
    penalizaciones = 0.0
    
    # Penalización por tráfico alto (más difícil navegar, mayor consumo)
    if trafico == "alto":
        penalizaciones += 5
    # Penalización por tráfico medio (moderadamente difícil)
    elif trafico == "medio":
        penalizaciones += 2
    
    # Penalización severa por ruta bloqueada (debe buscar ruta alternativa)
    if ruta_bloqueada:
        penalizaciones += 10
    
    # Ajustes por prioridad (incentivos para priorizar ciertos pedidos)
    if prioridad == "alta":
        # Bonificación: reduce el costo para incentivar entregas prioritarias
        penalizaciones -= 3
    elif prioridad == "baja":
        # Penalización leve para desincentivar pedidos de baja prioridad
        penalizaciones += 2
    
    # Calcular CR total
    cr = costo_distancia + costo_tiempo + penalizaciones
    
    return cr


def calcular_recompensa(pedido: Dict, entregado_exitosamente: bool) -> float:
    """
    Calcula la recompensa para el agente basándose en el costo de ruta y el resultado.
    
    Lógica de recompensa:
    - Si la entrega fue exitosa: recompensa = 100 - CR
      * Entregas con menor costo dan mayor recompensa
      * El valor base 100 asegura recompensas positivas para entregas exitosas
    - Si la entrega falló: recompensa = -CR
      * Penalización proporcional al costo de la ruta intentada
    
    Args:
        pedido: Diccionario con los datos del pedido.
        entregado_exitosamente: Booleano indicando si la entrega fue exitosa.
    
    Returns:
        float: Valor de la recompensa. Positivo para entregas exitosas, negativo para fallas.
    """
    cr = calcular_costo_ruta(pedido)
    
    if entregado_exitosamente:
        # Recompensa positiva: 100 menos el costo (incentiva entregas eficientes)
        recompensa = 100 - cr
    else:
        # Penalización: negativo del costo (penaliza intentos fallosos)
        recompensa = -cr
    
    return recompensa


def calcular_recompensa_por_tiempo(pedido: Dict, tiempo_real_min: int) -> float:
    """
    Calcula una recompensa adicional basada en la diferencia entre tiempo estimado y real.
    
    Esta función opcional permite dar bonificaciones por entregas más rápidas
    que lo estimado, o penalizaciones por entregas más lentas.
    
    Args:
        pedido: Diccionario con los datos del pedido.
        tiempo_real_min: Tiempo real que tomó la entrega en minutos.
    
    Returns:
        float: Ajuste de recompensa basado en el tiempo. Positivo si fue más rápido, negativo si fue más lento.
    """
    tiempo_estimado = pedido.get('tiempo_estimado_min', 0)
    diferencia = tiempo_estimado - tiempo_real_min
    
    # Si fue más rápido que lo estimado, dar bonificación
    # Si fue más lento, dar penalización
    ajuste = diferencia * 0.5  # Factor de ajuste
    
    return ajuste


if __name__ == "__main__":
    """
    Ejemplo de uso de las funciones de cálculo de recompensas.
    """
    print("=" * 70)
    print("EJEMPLO DE USO DEL MÓDULO DE RECOMPENSAS")
    print("=" * 70)
    
    # Definir pedidos de prueba con diferentes características
    pedidos_prueba = [
        {
            "id": 1,
            "cliente_nombre": "Juan Pérez",
            "distancia_km": 3.5,
            "tiempo_estimado_min": 15,
            "trafico": "bajo",
            "ruta_bloqueada": False,
            "prioridad": "alta"
        },
        {
            "id": 2,
            "cliente_nombre": "María García",
            "distancia_km": 8.2,
            "tiempo_estimado_min": 35,
            "trafico": "medio",
            "ruta_bloqueada": False,
            "prioridad": "media"
        },
        {
            "id": 3,
            "cliente_nombre": "Carlos Rodríguez",
            "distancia_km": 5.8,
            "tiempo_estimado_min": 25,
            "trafico": "alto",
            "ruta_bloqueada": False,
            "prioridad": "alta"
        },
        {
            "id": 4,
            "cliente_nombre": "Ana Martínez",
            "distancia_km": 12.4,
            "tiempo_estimado_min": 50,
            "trafico": "bajo",
            "ruta_bloqueada": False,
            "prioridad": "baja"
        },
        {
            "id": 5,
            "cliente_nombre": "Jorge Torres",
            "distancia_km": 11.8,
            "tiempo_estimado_min": 55,
            "trafico": "alto",
            "ruta_bloqueada": True,
            "prioridad": "baja"
        },
        {
            "id": 6,
            "cliente_nombre": "Roberto Díaz",
            "distancia_km": 1.8,
            "tiempo_estimado_min": 10,
            "trafico": "bajo",
            "ruta_bloqueada": False,
            "prioridad": "alta"
        }
    ]
    
    print("\n--- CÁLCULO DE COSTO DE RUTA (CR) ---")
    print(f"{'ID':<5} {'Cliente':<20} {'Dist':<8} {'Tiempo':<8} {'Tráfico':<8} {'Bloq':<6} {'Prior':<8} {'CR':<10}")
    print("-" * 80)
    
    for pedido in pedidos_prueba:
        cr = calcular_costo_ruta(pedido)
        print(f"{pedido['id']:<5} {pedido['cliente_nombre']:<20} "
              f"{pedido['distancia_km']:<8.1f} {pedido['tiempo_estimado_min']:<8} "
              f"{pedido['trafico']:<8} {str(pedido['ruta_bloqueada']):<6} "
              f"{pedido['prioridad']:<8} {cr:<10.2f}")
    
    print("\n--- CÁLCULO DE RECOMPENSAS (ENTREGA EXITOSA) ---")
    print(f"{'ID':<5} {'Cliente':<20} {'CR':<10} {'Recompensa':<12}")
    print("-" * 50)
    
    for pedido in pedidos_prueba:
        cr = calcular_costo_ruta(pedido)
        recompensa = calcular_recompensa(pedido, entregado_exitosamente=True)
        print(f"{pedido['id']:<5} {pedido['cliente_nombre']:<20} {cr:<10.2f} {recompensa:<12.2f}")
    
    print("\n--- CÁLCULO DE RECOMPENSAS (ENTREGA FALLIDA) ---")
    print(f"{'ID':<5} {'Cliente':<20} {'CR':<10} {'Recompensa':<12}")
    print("-" * 50)
    
    for pedido in pedidos_prueba:
        cr = calcular_costo_ruta(pedido)
        recompensa = calcular_recompensa(pedido, entregado_exitosamente=False)
        print(f"{pedido['id']:<5} {pedido['cliente_nombre']:<20} {cr:<10.2f} {recompensa:<12.2f}")
    
    print("\n--- ANÁLISIS DE ESCENARIOS ESPECÍFICOS ---")
    
    # Escenario 1: Pedido corto con prioridad alta (ideal)
    pedido_ideal = {
        "distancia_km": 2.0,
        "tiempo_estimado_min": 10,
        "trafico": "bajo",
        "ruta_bloqueada": False,
        "prioridad": "alta"
    }
    cr_ideal = calcular_costo_ruta(pedido_ideal)
    rec_ideal = calcular_recompensa(pedido_ideal, True)
    print(f"Pedido ideal (corto, prioridad alta, sin tráfico): CR = {cr_ideal:.2f}, Recompensa = {rec_ideal:.2f}")
    
    # Escenario 2: Pedido largo con ruta bloqueada (peor caso)
    pedido_peor = {
        "distancia_km": 15.0,
        "tiempo_estimado_min": 60,
        "trafico": "alto",
        "ruta_bloqueada": True,
        "prioridad": "baja"
    }
    cr_peor = calcular_costo_ruta(pedido_peor)
    rec_peor = calcular_recompensa(pedido_peor, True)
    print(f"Pedido peor (largo, bloqueado, tráfico alto): CR = {cr_peor:.2f}, Recompensa = {rec_peor:.2f}")
    
    # Escenario 3: Pedido medio con tráfico medio
    pedido_medio = {
        "distancia_km": 5.0,
        "tiempo_estimado_min": 20,
        "trafico": "medio",
        "ruta_bloqueada": False,
        "prioridad": "media"
    }
    cr_medio = calcular_costo_ruta(pedido_medio)
    rec_medio = calcular_recompensa(pedido_medio, True)
    print(f"Pedido medio (distancia y tráfico moderados): CR = {cr_medio:.2f}, Recompensa = {rec_medio:.2f}")
    
    print("\n--- AJUSTE POR TIEMPO REAL (FUNCIÓN OPCIONAL) ---")
    pedido_tiempo = pedidos_prueba[0]  # Pedido 1
    tiempo_estimado = pedido_tiempo['tiempo_estimado_min']
    
    print(f"Pedido {pedido_tiempo['id']}: Tiempo estimado = {tiempo_estimado} min")
    
    # Caso 1: Entrega más rápida
    tiempo_rapido = 12
    ajuste_rapido = calcular_recompensa_por_tiempo(pedido_tiempo, tiempo_rapido)
    print(f"  Tiempo real = {tiempo_rapido} min (más rápido): Ajuste = {ajuste_rapido:.2f}")
    
    # Caso 2: Entrega más lenta
    tiempo_lento = 20
    ajuste_lento = calcular_recompensa_por_tiempo(pedido_tiempo, tiempo_lento)
    print(f"  Tiempo real = {tiempo_lento} min (más lento): Ajuste = {ajuste_lento:.2f}")
    
    print("\n" + "=" * 70)
    print("FIN DEL EJEMPLO")
    print("=" * 70)
