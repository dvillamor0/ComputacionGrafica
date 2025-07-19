python -m ensurepip --default-pip
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from urllib.parse import urlparse, parse_qs # parse_qs from descargar_archivo_drive, not strictly needed but kept for completeness
import sys # Para importar módulos desde otras rutas si fuera necesario

# === Configuraciones Globales ===
# Asegúrate de que estas rutas sean correctas en tu entorno.
# Se asume que 'zinc-citron-369904-29288f9a2c6a.json' está en el mismo directorio que este script.
SERVICE_ACCOUNT_FILE = r"zinc-citron-369904-29288f9a2c6a.json"

# SCOPES para Google Drive: 'drive.file' permite subir y administrar archivos creados por la app,
# y acceder a archivos a los que la cuenta de servicio tiene acceso.
# Es un permiso más seguro que 'drive' completo.
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.readonly'] # Necesitamos lectura para descargar y escritura para subir

# URL de la carpeta principal de Google Drive de destino para las subidas
GDRIVE_UPLOAD_MAIN_FOLDER_URL = "https://drive.google.com/drive/folders/1Va688GB3nRGIAolJncP-4yZgEdhDsCzz"

# Ruta absoluta del directorio donde se encuentra este script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# La carpeta base para las órdenes locales (donde se descargan y se encuentran los archivos para subir)
ORDERS_BASE_PATH = os.path.join(SCRIPT_DIR, "pedidos")
os.makedirs(ORDERS_BASE_PATH, exist_ok=True) # Asegura que la carpeta base 'pedidos' exista

# === Importar funciones de los otros scripts ===
# Para importar desde archivos en el mismo directorio, simplemente los tratamos como módulos.
# Asegúrate de que los nombres de los archivos Python sean correctos.

# Importar funciones de descargar_archivo_drive.py
try:
    from descargar_archivo_drive import find_folder_by_name, download_gdrive_folder
except ImportError as e:
    print(f"❌ Error al importar de 'descargar_archivo_drive.py': {e}")
    print("Asegúrate de que 'descargar_archivo_drive.py' esté en el mismo directorio.")
    sys.exit(1)

# Importar la función modificada slice_model_and_report de STL_Gcode_EXCEL.py
try:
    from STL_Gcode_EXCEL import slice_model_and_report
except ImportError as e:
    print(f"❌ Error al importar de 'STL_Gcode_EXCEL.py': {e}")
    print("Asegúrate de que 'STL_Gcode_EXCEL.py' esté en el mismo directorio y esté actualizado.")
    sys.exit(1)

# === Funciones de Google Drive (desde subir_a_drive.py, con ajustes para ser genéricas) ===

def get_drive_service_from_service_account():
    """Autentica y devuelve el servicio de Google Drive usando una cuenta de servicio."""
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ Error al autenticar con la cuenta de servicio: {e}")
        print(f"Asegúrate de que el archivo de credenciales '{SERVICE_ACCOUNT_FILE}' exista y sea válido.")
        return None

def get_folder_id_from_url(url):
    """Extrae el ID de la carpeta de una URL de Google Drive."""
    parsed_url = urlparse(url)
    if "drive.google.com" in parsed_url.netloc and "folders" in parsed_url.path:
        path_parts = parsed_url.path.split('/')
        try:
            return path_parts[path_parts.index('folders') + 1]
        except ValueError:
            pass
    return None

def find_folder_by_name_in_parent(service, parent_id, folder_name):
    """Busca una carpeta por nombre dentro de una carpeta padre en Google Drive."""
    query = f"'{parent_id}' in parents and name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)').execute()
    items = results.get('files', [])
    return items[0] if items else None

def create_folder(service, folder_name, parent_id=None):
    """Crea una carpeta en Google Drive."""
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]

    try:
        folder = service.files().create(body=file_metadata, fields='id').execute()
        print(f"✅ Carpeta '{folder_name}' creada con ID: {folder.get('id')}")
        return folder.get('id')
    except Exception as e:
        print(f"❌ Error al crear la carpeta '{folder_name}': {e}")
        return None

def upload_file(service, file_path, target_folder_id):
    """Sube un archivo local a la carpeta especificada en Google Drive."""
    file_name = os.path.basename(file_path)

    file_metadata = {
        'name': file_name,
        'parents': [target_folder_id] # Especifica el ID de la carpeta de destino
    }
    media = MediaFileUpload(file_path, resumable=True)

    try:
        file = service.files().create(body=file_metadata, media_body=media, fields='id, name').execute()
        print(f"✅ Archivo '{file.get('name')}' subido exitosamente a Drive con ID: {file.get('id')}")
        return True
    except Exception as e:
        print(f"❌ Error al subir el archivo '{file_name}': {e}")
        return False

# === Funciones de orquestación de la orden ===

def download_order_folder(service, order_number):
    """
    Descarga la carpeta de la orden desde Google Drive.
    Retorna True si la descarga fue exitosa, False en caso contrario.
    """
    print(f"\n--- Paso 1: Descargando orden '{order_number}' de Google Drive ---")
    found_folder = find_folder_by_name(service, order_number) # Reutiliza find_folder_by_name de descargar_archivo_drive

    if found_folder:
        folder_id = found_folder['id']
        folder_name = found_folder['name'] # Debería ser igual a order_number
        print(f"Orden '{folder_name}' encontrada en Drive (ID: {folder_id}).")

        output_folder_path = os.path.join(ORDERS_BASE_PATH, folder_name)
        os.makedirs(output_folder_path, exist_ok=True)
        
        # Llama a la función de descarga de descargar_archivo_drive.py
        download_gdrive_folder(folder_id, output_folder_path, folder_name)
        return True
    else:
        print(f"❌ Error: No se encontró la orden '{order_number}' en Google Drive para descargar.")
        return False

def process_order_with_slicer(order_number):
    """
    Ejecuta el proceso de 'slicing' y generación de reporte para la orden.
    Retorna True si la operación fue exitosa, False en caso contrario.
    """
    print(f"\n--- Paso 2: Procesando orden '{order_number}' con PrusaSlicer y generando reporte ---")
    # Llama a la función modificada de STL_Gcode_EXCEL.py
    return slice_model_and_report(order_number)

def upload_order_files(service, order_number):
    """
    Sube los archivos .gcode y .xlsx de la orden a Google Drive.
    Retorna True si la subida fue exitosa, False en caso contrario.
    """
    print(f"\n--- Paso 3: Subiendo archivos de la orden '{order_number}' a Google Drive ---")

    local_order_path = os.path.join(ORDERS_BASE_PATH, order_number)

    if not os.path.isdir(local_order_path):
        print(f"❌ Error: La carpeta local de la orden '{local_order_path}' no existe.")
        return False

    files_to_upload = []
    print(f"Buscando archivos .gcode y .xlsx en '{local_order_path}' para subir...")
    for item in os.listdir(local_order_path):
        item_path = os.path.join(local_order_path, item)
        if os.path.isfile(item_path):
            if item.lower().endswith(('.gcode', '.xlsx')):
                files_to_upload.append(item_path)

    if not files_to_upload:
        print(f"ℹ️ No se encontraron archivos .gcode o .xlsx en la orden local '{order_number}' para subir.")
        return True # Consideramos éxito si no hay archivos pero el proceso no falló

    print(f"Archivos encontrados para subir: {', '.join([os.path.basename(f) for f in files_to_upload])}")

    gdrive_parent_folder_id = get_folder_id_from_url(GDRIVE_UPLOAD_MAIN_FOLDER_URL)
    if not gdrive_parent_folder_id:
        print("❌ Error: No se pudo obtener el ID de la carpeta principal de Drive desde la URL constante para la subida.")
        return False

    target_gdrive_order_folder_name = order_number
    target_folder = find_folder_by_name_in_parent(service, gdrive_parent_folder_id, target_gdrive_order_folder_name)

    target_folder_id = None
    if target_folder:
        target_folder_id = target_folder['id']
        print(f"Orden de destino '{target_gdrive_order_folder_name}' encontrada en Drive con ID: {target_folder_id}")
    else:
        print(f"Orden de destino '{target_gdrive_order_folder_name}' no encontrada en Drive. Creando nueva orden (carpeta)...")
        target_folder_id = create_folder(service, target_gdrive_order_folder_name, parent_id=gdrive_parent_folder_id)
        if not target_folder_id:
            print("❌ Error: No se pudo crear la orden de destino en Google Drive para la subida.")
            return False
    
    all_uploads_successful = True
    if target_folder_id:
        print(f"\nIniciando subida de archivos a la orden '{target_gdrive_order_folder_name}' en Google Drive...")
        for file_path in files_to_upload:
            if not upload_file(service, file_path, target_folder_id):
                all_uploads_successful = False
                # Continuar intentando subir otros archivos aunque uno falle
    else:
        print("❌ No se pudo determinar la carpeta de destino en Google Drive para subir los archivos.")
        return False
    
    return all_uploads_successful

# === Función Principal del Flujo de Trabajo ===

def main_workflow():
    print("=== 🚀 Flujo de Trabajo de Sincronización de Órdenes ===")

    # 0. Autenticar con Google Drive una vez
    drive_service = get_drive_service_from_service_account()
    if not drive_service:
        print("Flujo de trabajo terminado debido a error de autenticación.")
        return

    # 1. Solicitar el número de orden al usuario
    order_number = input("Ingresa el CÓDIGO DE ORDEN a procesar (ej. 'ORDEN123'): ").strip()
    if not order_number:
        print("Código de orden no puede estar vacío. Terminando el flujo de trabajo.")
        return

    # 2. Descargar la carpeta de la orden de Google Drive
    if not download_order_folder(drive_service, order_number):
        print("Flujo de trabajo terminado: Falló la descarga de la orden.")
        return

    # 3. Ejecutar el script STL_Gcode_EXCEL (slicing y reporte)
    if not process_order_with_slicer(order_number):
        print("Flujo de trabajo terminado: Falló el procesamiento del STL y/o la generación del reporte.")
        return

    # 4. Subir los archivos resultantes a Google Drive
    if not upload_order_files(drive_service, order_number):
        print("Flujo de trabajo terminado: Falló la subida de los archivos resultantes.")
        return

    print(f"\n=== ✅ Flujo de Trabajo para la orden '{order_number}' COMPLETADO EXITOSAMENTE ===")

if __name__ == "__main__":
    main_workflow()
