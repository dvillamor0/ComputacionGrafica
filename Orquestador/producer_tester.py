import psycopg2
import pika
import json

# Importa tus configuraciones (ajusta según tu proyecto)
from settings import DB_HOST, DB_NAME, DB_USER, DB_PASS, RABBITMQ_HOST, QUEUE_NAME


def create_order_and_publish():
    """
    Inserta un pedido con la estructura nueva y publica el ID en RabbitMQ.
    """
    conn_db = None
    conn_mq = None
    cur = None

    try:
        # 1. Conectar a la base de datos PostgreSQL
        print("Conectando a la base de datos...")
        conn_db = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn_db.cursor()
        print("Conexión a la base de datos exitosa.")

        # --- Manejo del Cliente (asegurando que exista para la clave foránea) ---
        id_cliente = 1 # Usas id_cliente = 1
        nombre_cliente = 'Cliente Base' # Nombre de ejemplo para el cliente 1
        email_cliente = 'cliente.base@example.com' # Email de ejemplo para el cliente 1

        print(f"Verificando si el cliente {id_cliente} existe...")
        cur.execute("SELECT id_cliente FROM public.clientes WHERE id_cliente = %s;", (id_cliente,))
        cliente_existente = cur.fetchone()

        if not cliente_existente:
            print(f"Cliente {id_cliente} no encontrado. Insertando nuevo cliente...")
            # ASEGÚRATE QUE ESTOS CAMPOS ('id_cliente', 'nombre', 'email') COINCIDAN CON TU TABLA 'clientes'
            cur.execute("""
                INSERT INTO public.clientes (id_cliente, nombre, email)
                VALUES (%s, %s, %s);
            """, (id_cliente, nombre_cliente, email_cliente))
            conn_db.commit() # Confirma la inserción del cliente
            print(f"Cliente {id_cliente} insertado con éxito.")
        else:
            print(f"Cliente {id_cliente} ya existe.")
        # --- Fin Manejo del Cliente ---
        
        celular_id = 1
        color = '222,000,000'
        cantidad = 2
        acce_camara = 2  # Esto se insertará como NULL
        acce_medio = 4   # Esto se insertará como NULL
        acce_inferio = 3 # Esto se insertará como NULL

        # 3. Insertar pedido
        print("Insertando nuevo pedido en la base de datos...")
        cur.execute("""
            INSERT INTO public.pedidos
                (id_cliente, id_celular, color, cantidad, acce_camara, acce_medio, acce_inferio)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id_pedido;
        """, (id_cliente, celular_id, color, cantidad, acce_camara, acce_medio, acce_inferio))

        order_id = cur.fetchone()[0]
        conn_db.commit()
        print(f"Pedido {order_id} insertado con éxito.")

        # 4. Conectarse a RabbitMQ
        print("Conectando a RabbitMQ...")
        connection_params = pika.ConnectionParameters(host=RABBITMQ_HOST)
        conn_mq = pika.BlockingConnection(connection_params)
        channel = conn_mq.channel()
        print("Conexión a RabbitMQ exitosa.")

        # 5. Declarar la cola
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        # 6. Publicar mensaje
        message = {'order_id': order_id}
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f"Mensaje publicado en RabbitMQ con Pedido ID: {order_id}")

    except psycopg2.Error as db_err:
        print(f"Error de base de datos: {db_err}")
        if conn_db:
            conn_db.rollback()
    except pika.exceptions.AMQPConnectionError as mq_conn_err:
        print(f"Error de conexión a RabbitMQ: {mq_conn_err}")
    except Exception as e:
        print(f"Error inesperado: {e}")
    finally:
        if cur:
            cur.close()
        if conn_db:
            conn_db.close()
            print("Conexión a la base de datos cerrada.")
        if conn_mq:
            conn_mq.close()
            print("Conexión a RabbitMQ cerrada.")


if __name__ == "__main__":
    create_order_and_publish()