# consumers/order_consumer.py

import pika
import json
import os # Para verificar/crear el directorio de salida
import time

# Importa las funciones y configuraciones de tus módulos
from settings import RABBITMQ_HOST, QUEUE_NAME, GENERATED_FILES_DIR
from database import update_order_status, get_order_details
from excel import generate_order_excel
from inventor import run_inventor_vba_macro
from inventor_open import open_inventor

# Asegúrate de que el directorio de salida exista
if not os.path.exists(GENERATED_FILES_DIR):
    os.makedirs(GENERATED_FILES_DIR)
    print(f"[INIT] Directorio de salida creado: {GENERATED_FILES_DIR}")

def process_order(ch, method, properties, body):
    """
    Función de callback que se ejecuta cuando se recibe un mensaje.
    Orquesta el procesamiento del pedido.
    """
    order_data_mq = json.loads(body)
    order_id = order_data_mq['order_id']
    print(f"[MSG] Pedido recibido | ID: {order_id}")

    # Variables para almacenar rutas de archivos generados
    excel_file_path = None
    stl_file_path = None
    ipt_file_path = None
    image_file_path = None
    tiempo_espera = 1  # Tiempo de espera antes de ejecutar Inventor
    try:
        tiempo_total_inicio = time.time()
        # 1. Obtener detalles completos del pedido y del celular de la base de datos
        order_details = get_order_details(order_id)
        if not order_details:
            print(f"[ERROR] No se encontraron detalles para el Pedido ID: {order_id}. Saltando procesamiento.")
            ch.basic_ack(delivery_tag=method.delivery_tag) # Acknowledge para no reintentar un pedido no existente
            print('[WAIT] Esperando mensajes. Para salir, presiona CTRL+C')
            return
        
        # Imprimir todos los detalles del pedido y del celular (para depuración)
        print(f"[INFO] Detalles completos del Pedido ID {order_id} (desde DB):")
        for key, value in order_details.items():
            print(f"    - {key}: {value}")

        # Crear carpeta de pedido local
        order_folder_path = os.path.join(GENERATED_FILES_DIR, str(order_id))
        if not os.path.exists(order_folder_path):
            os.makedirs(order_folder_path)
            print(f"[INIT] Carpeta creada para Pedido ID {order_id}: {order_folder_path}")
        else:
            print(f"[SKIP] Carpeta ya existe para Pedido ID {order_id}: {order_folder_path}")
            
        # 2. Simular el procesamiento y actualizar el estado
        # Etapa: Generación de Excel

        update_order_status(order_id, 'PROCESANDO_EXCEL')
        print(f"[WAIT] Esperando {tiempo_espera} segundos antes de generar Excel...")
        time.sleep(tiempo_espera)
        print(f"[STEP] Generando archivo Excel para Pedido ID: {order_id}")
        excel_file_path = generate_order_excel(order_details, order_id)

        # 3. Ejecutar macro de Inventor
        print(f"[WAIT] Esperando {tiempo_espera} segundos antes de ejecutar Inventor...")
        time.sleep(tiempo_espera)
        open_inventor()
        print(f"[STEP] Ejecutando macro de Inventor para Pedido ID: {order_id}")
        run_inventor_vba_macro()

        # 3.5 Copiar carpeta del pedido a destino
        print(f"[WAIT] Esperando {tiempo_espera} segundos antes de copiar la carpeta del pedido...")
        time.sleep(tiempo_espera)
        from copy_documents import copy_order_folder
        copy_order_folder(order_id)

        # 4. Marcar como COMPLETADO
        print(f"[DONE] Pedido ID {order_id} procesado y COMPLETADO exitosamente.")
        update_order_status(order_id, 'COMPLETADO')

        # 5. Enviar confirmación (ACK) a RabbitMQ
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[ACK] Mensaje confirmado para Pedido ID: {order_id}")
        tiempo_total_fin = time.time()
        print(f"[TIME] Tiempo total de procesamiento del pedido {order_id}: {tiempo_total_fin - tiempo_total_inicio:.2f} segundos")
        print('[WAIT] Esperando mensajes. Para salir, presiona CTRL+C')

    except Exception as e:
        print(f"[ERROR] Error al procesar Pedido ID {order_id}: {e}")
        # Aquí puedes decidir qué hacer: reencolar, mover a una cola de mensajes muertos (DLQ), etc.
        # Por simplicidad, lo reencolamos.
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        print(f"[NACK] Mensaje rechazado y reencolado para Pedido ID: {order_id}")
        print('[WAIT] Esperando mensajes. Para salir, presiona CTRL+C')
    finally:
        pass # No hacemos nada por ahora en el finally


def start_consumer():
    """
    Inicia el consumidor de RabbitMQ.
    """
    connection = None
    try:
        print("[INIT] Conectando a RabbitMQ para consumir mensajes...")
        connection_params = pika.ConnectionParameters(host=RABBITMQ_HOST)
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        print("[INIT] Conexión a RabbitMQ exitosa.")

        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        print(f"[INIT] Cola '{QUEUE_NAME}' declarada.")
        print('[WAIT] Esperando mensajes. Para salir, presiona CTRL+C')

        channel.basic_qos(prefetch_count=1) # Procesa un mensaje a la vez

        channel.basic_consume(queue=QUEUE_NAME, on_message_callback=process_order)
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as mq_conn_err:
        print(f"[ERROR] Error de conexión a RabbitMQ: {mq_conn_err}")
        print("[ERROR] Asegúrate de que RabbitMQ esté corriendo y accesible.")
    except KeyboardInterrupt:
        print("[STOP] Deteniendo consumidor...")
    except Exception as e:
        print(f"[ERROR] Ocurrió un error inesperado en el consumidor principal: {e}")
    finally:
        if connection:
            connection.close()
            print("[STOP] Conexión a RabbitMQ cerrada.")

if __name__ == "__main__":
    start_consumer()
