# db/database.py

import psycopg2

from settings import DB_HOST, DB_NAME, DB_USER, DB_PASS

def get_db_connection():
    """
    Establece y retorna una conexión a la base de datos PostgreSQL.
    """
    try:
        return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    except psycopg2.Error as e:
        print(f"[ERROR] Error al conectar a la base de datos: {e}")
        raise


def update_order_status(order_id: int, new_status: str) -> None:
    """
    Actualiza el estado de un pedido.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE public.pedidos SET estado = %s WHERE id_pedido = %s;",
            (new_status, order_id)
        )
        conn.commit()
        print(f"[STEP] Pedido ID {order_id} actualizado a estado: '{new_status}'.")
    except psycopg2.Error as e:
        print(f"[ERROR] Error actualizando Pedido ID {order_id} a '{new_status}': {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_order_details(order_id: int) -> dict | None:
    """
    Obtiene los detalles completos de un pedido y su celular asociado.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                p.id_pedido, p.id_cliente, p.id_celular, p.color, p.fecha, p.estado,
                p.cantidad, p.acce_camara, p.acce_medio, p.acce_inferio,
                c.marca, c.modelo, c.alto, c.ancho, c.grosor, c.radioesquina,
                c.xcamara, c.ycamara, c.radiocamara, c.anchocamara, c.altocamara,
                c.xii, c.xif, c.xsi, c.xsf, c.ydi, c.ydf, c.yii, c.yif,
                c.xhuella, c.yhuella, c.radiohuella, c.anchohuella, c.altohuella, c.radioesquinahuella
            FROM public.pedidos p
            JOIN public.celulares c ON p.id_celular = c.id_celular
            WHERE p.id_pedido = %s;
        """, (order_id,))

        row = cur.fetchone()
        if row:
            columns = [
                # Datos del pedido
                "id_pedido", "id_cliente", "id_celular", "color", "fecha", "estado",
                "cantidad", "acce_camara", "acce_medio", "acce_inferio",
                # Datos del celular
                "marca", "modelo", "alto", "ancho", "grosor", "radioesquina",
                "xcamara", "ycamara", "radiocamara", "anchocamara", "altocamara",
                "xii", "xif", "xsi", "xsf", "ydi", "ydf", "yii", "yif",
                "xhuella", "yhuella", "radiohuella", "anchohuella", "altohuella", "radioesquinahuella"
            ]
            return dict(zip(columns, row))

        return None

    except psycopg2.Error as e:
        print(f"[ERROR] Error obteniendo detalles del Pedido ID {order_id}: {e}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
