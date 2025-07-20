# settings.py


import os
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
# Asegúrate de tener 'python-dotenv' instalado: pip install python-dotenv
load_dotenv()

# --- Configuración de la Base de Datos PostgreSQL ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "your_database_name") 
DB_USER = os.getenv("DB_USER", "your_username")     
DB_PASS = os.getenv("DB_PASS", "your_password")   

# --- Configuración de RabbitMQ ---
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
QUEUE_NAME = "order_processing_queue" # Nombre de la cola de RabbitMQ

# --- Configuración de Google Drive ---
# Alcances (scopes) necesarios para acceder a Google Drive
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive']
# ID de la carpeta de Google Drive principal
PARENT_FOLDER_ID = os.getenv("PARENT_FOLDER_ID", "1Va688GB3nRGIAolJncP-4yZgEdhDsCzz")

# --- Rutas y otros settings ---
# Directorio donde se guardarán los archivos generados (Excel, STL, IPT)
# Usamos os.path.abspath para asegurar que la ruta sea absoluta y no dependa del directorio de ejecución.
GENERATED_FILES_DIR = r"C:\Users\Sala CAD\Desktop\Proyecto\ProyectoComp\files\generated_files"
# Directorio base de origen para copiar carpetas de pedidos
SOURCE_BASE_DIR = GENERATED_FILES_DIR
# Directorio destino para copiar carpetas de pedidos
TARGET_BASE_DIR = r"G:\Mi unidad\computacion grafica"
# Ruta a la plantilla de Excel
EXCEL_TEMPLATE_PATH = os.path.join("files", "Bases", "DataInventor.xlsx")
# Ruta a la plantilla de Inventor (CarcasaBase.ipt)
INVENTOR_TEMPLATE_PATH = os.path.abspath(os.path.join("files", "Bases", "CarcasaBase.ipt"))