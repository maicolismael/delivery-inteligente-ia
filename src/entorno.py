"""
Entorno básico para el sistema de delivery con Q-Learning.

Este módulo define la clase EntornoDelivery que gestiona la carga y acceso
a los datos de pedidos simulados desde un archivo JSON.
"""

import json
import os
from typing import Dict, List, Optional


class EntornoDelivery:
    """
    Clase que representa el entorno de delivery.
    
    Gestiona la carga de pedidos desde un archivo JSON y proporciona métodos
    para acceder y modificar el estado de los pedidos.
    """
    
    def __init__(self, ruta_json: str = "data/pedidos_simulados.json"):
        """
        Constructor de la clase EntornoDelivery.
        
        Args:
            ruta_json: Ruta al archivo JSON que contiene los pedidos simulados.
        """
        self.ruta_json = ruta_json
        self.datos = None
        self.pedidos = []
        self.almacen = None
        self.cargar_pedidos()
    
    def cargar_pedidos(self) -> List[Dict]:
        """
        Carga los pedidos desde el archivo JSON.
        
        Returns:
            Lista de diccionarios con los datos de los pedidos.
        """
        # Obtener la ruta absoluta del archivo JSON
        ruta_absoluta = os.path.join(os.path.dirname(__file__), "..", self.ruta_json)
        ruta_absoluta = os.path.abspath(ruta_absoluta)
        
        try:
            with open(ruta_absoluta, 'r', encoding='utf-8') as archivo:
                self.datos = json.load(archivo)
                self.pedidos = self.datos.get('pedidos', [])
                self.almacen = self.datos.get('almacen', None)
                print(f"✓ Cargados {len(self.pedidos)} pedidos desde {ruta_absoluta}")
                return self.pedidos
        except FileNotFoundError:
            print(f"✗ Error: No se encontró el archivo {ruta_absoluta}")
            return []
        except json.JSONDecodeError as e:
            print(f"✗ Error al decodificar el JSON: {e}")
            return []
    
    def obtener_pedidos_pendientes(self) -> List[Dict]:
        """
        Filtra y retorna los pedidos con estado 'pendiente'.
        
        Returns:
            Lista de diccionarios con los pedidos pendientes.
        """
        pendientes = [p for p in self.pedidos if p.get('estado') == 'pendiente']
        return pendientes
    
    def obtener_almacen(self) -> Optional[Dict]:
        """
        Retorna la ubicación del almacén.
        
        Returns:
            Diccionario con la dirección y coordenadas del almacén, o None si no existe.
        """
        return self.almacen
    
    def obtener_datos_pedido(self, pedido_id: int) -> Optional[Dict]:
        """
        Accede a un pedido específico por su ID.
        
        Args:
            pedido_id: ID del pedido a buscar.
            
        Returns:
            Diccionario con los datos del pedido, o None si no se encuentra.
        """
        for pedido in self.pedidos:
            if pedido.get('id') == pedido_id:
                return pedido
        return None
    
    def actualizar_estado_pedido(self, pedido_id: int, nuevo_estado: str) -> bool:
        """
        Actualiza el estado de un pedido específico.
        
        Args:
            pedido_id: ID del pedido a actualizar.
            nuevo_estado: Nuevo estado del pedido (ej: 'entregado', 'en_camino').
            
        Returns:
            True si se actualizó correctamente, False si no se encontró el pedido.
        """
        pedido = self.obtener_datos_pedido(pedido_id)
        if pedido:
            pedido['estado'] = nuevo_estado
            print(f"✓ Pedido {pedido_id} actualizado a estado: {nuevo_estado}")
            return True
        else:
            print(f"✗ No se encontró el pedido con ID {pedido_id}")
            return False
    
    def obtener_todos_los_pedidos(self) -> List[Dict]:
        """
        Retorna todos los pedidos cargados.
        
        Returns:
            Lista de diccionarios con todos los pedidos.
        """
        return self.pedidos
    
    def guardar_pedidos(self) -> bool:
        """
        Guarda los cambios en el archivo JSON.
        
        Returns:
            True si se guardó correctamente, False en caso contrario.
        """
        if self.datos is None:
            return False
        
        ruta_absoluta = os.path.join(os.path.dirname(__file__), "..", self.ruta_json)
        ruta_absoluta = os.path.abspath(ruta_absoluta)
        
        try:
            with open(ruta_absoluta, 'w', encoding='utf-8') as archivo:
                json.dump(self.datos, archivo, indent=2, ensure_ascii=False)
                print(f"✓ Pedidos guardados en {ruta_absoluta}")
                return True
        except Exception as e:
            print(f"✗ Error al guardar los pedidos: {e}")
            return False


if __name__ == "__main__":
    """
    Ejemplo de uso de la clase EntornoDelivery.
    """
    print("=" * 60)
    print("EJEMPLO DE USO DEL ENTORNO DE DELIVERY")
    print("=" * 60)
    
    # Crear instancia del entorno
    entorno = EntornoDelivery()
    
    # Mostrar información del almacén
    print("\n--- INFORMACIÓN DEL ALMACÉN ---")
    almacen = entorno.obtener_almacen()
    if almacen:
        print(f"Dirección: {almacen.get('direccion')}")
        print(f"Coordenadas: {almacen.get('coordenadas')}")
    
    # Mostrar todos los pedidos
    print("\n--- TODOS LOS PEDIDOS ---")
    todos_los_pedidos = entorno.obtener_todos_los_pedidos()
    for pedido in todos_los_pedidos:
        print(f"ID: {pedido['id']}, Cliente: {pedido['cliente_nombre']}, "
              f"Distancia: {pedido['distancia_km']}km, Estado: {pedido['estado']}")
    
    # Mostrar solo los pedidos pendientes
    print("\n--- PEDIDOS PENDIENTES ---")
    pendientes = entorno.obtener_pedidos_pendientes()
    print(f"Cantidad de pedidos pendientes: {len(pendientes)}")
    for pedido in pendientes:
        print(f"ID: {pedido['id']}, Cliente: {pedido['cliente_nombre']}, "
              f"Prioridad: {pedido['prioridad']}, Tráfico: {pedido['trafico']}")
    
    # Obtener datos de un pedido específico
    print("\n--- DATOS DE UN PEDIDO ESPECÍFICO (ID: 1) ---")
    pedido_especifico = entorno.obtener_datos_pedido(1)
    if pedido_especifico:
        print(f"Cliente: {pedido_especifico['cliente_nombre']}")
        print(f"Dirección: {pedido_especifico['direccion']}")
        print(f"Distancia: {pedido_especifico['distancia_km']} km")
        print(f"Tiempo estimado: {pedido_especifico['tiempo_estimado_min']} min")
        print(f"Prioridad: {pedido_especifico['prioridad']}")
        print(f"Tráfico: {pedido_especifico['trafico']}")
        print(f"Ruta bloqueada: {pedido_especifico['ruta_bloqueada']}")
    
    # Actualizar estado de un pedido
    print("\n--- ACTUALIZAR ESTADO DE UN PEDIDO ---")
    entorno.actualizar_estado_pedido(1, "entregado")
    
    # Verificar que el estado cambió
    print("\n--- PEDIDOS PENDIENTES DESPUÉS DE ACTUALIZACIÓN ---")
    pendientes_actualizados = entorno.obtener_pedidos_pendientes()
    print(f"Cantidad de pedidos pendientes: {len(pendientes_actualizados)}")
    
    print("\n" + "=" * 60)
    print("FIN DEL EJEMPLO")
    print("=" * 60)
