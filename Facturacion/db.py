import psycopg2
from .db import POSTGRES_CONFIG, POSTGRES_QUERY_INVENTARIO, POSTGRES_QUERY_PROVEEDORES, POSTGRES_QUERY_PEDIDOS
# === FUNCIONES PARA BASE DE DATOS ===

def consultar_postgres(query):
    try:
        with psycopg2.connect(**POSTGRES_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
    except Exception as e:
        print(f"❌ Error en PostgreSQL: {e}")
        return []

def obtener_inventario():
    return consultar_postgres(POSTGRES_QUERY_INVENTARIO)

def obtener_proveedores():
    return consultar_postgres(POSTGRES_QUERY_PROVEEDORES)


def obtener_pedidos():
    return consultar_postgres(POSTGRES_QUERY_PEDIDOS)

def actualizar_cantidad_inventario(id_producto, nueva_cantidad):
    """
    Actualiza la cantidad del producto en la tabla inventario según su id.
   
    :param id_producto: int - ID del producto a actualizar.
    :param nueva_cantidad: int - Nueva cantidad a establecer.
    """
    update_query = """
        UPDATE inventario
        SET cantidad = %s
        WHERE id_producto = %s;
    """

    try:
        with psycopg2.connect(**POSTGRES_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(update_query, (nueva_cantidad, id_producto))
                conn.commit()
                print(f"✅ Cantidad actualizada para el producto {id_producto}: {nueva_cantidad}")
    except Exception as e:
        print(f"❌ Error al actualizar inventario: {e}")