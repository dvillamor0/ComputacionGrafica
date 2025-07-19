import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from urllib.parse import urlparse

# === Configuraciones ===

# Ruta al archivo de credenciales de la cuenta de servicio
SERVICE_ACCOUNT_FILE = r"zinc-citron-369904-29288f9a2c6a.json" # Ajusta esta ruta si tu JSON está en otro lugar, ej: r"pruebas\zinc-citron-369904-29288f9a2c6a.json"

# SCOPES para Google Drive: 'drive.file' permite subir y administrar archivos creados por la app.
# Si necesitas subir a cualquier carpeta sin importar quién la creó, podrías necesitar 'https://www.googleapis.com/auth/drive'
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# URL de la carpeta principal de Google Drive de destino (AHORA ES UNA CONSTANTE)
GDRIVE_MAIN_FOLDER_URL = "https://drive.google.com/drive/folders/1Va688GB3nRGIAolJncP-4yZgEdhDsCzz"

# Obtener la ruta absoluta del directorio donde se encuentra el script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# La carpeta base local para las órdenes descargadas (donde están los archivos a subir)
LOCAL_ORDERS_BASE_PATH = os.path.join(SCRIPT_DIR, "pedidos") # Carpeta 'pedidos' en el mismo directorio del script
os.makedirs(LOCAL_ORDERS_BASE_PATH, exist_ok=True) # Asegura que la carpeta base 'pedidos' exista

# === Funciones de Google Drive ===

def get_drive_service_from_service_account():
    """Autentica y devuelve el servicio de Google Drive usando una cuenta de servicio."""
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f" Error al autenticar con la cuenta de servicio: {e}")
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
        folder = service.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()
        print(f" Carpeta '{folder_name}' creada con ID: {folder.get('id')}")
        return folder.get('id')
    except Exception as e:
        print(f" Error al crear la carpeta '{folder_name}': {e}")
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
        file = service.files().create(body=file_metadata, media_body=media, fields='id, name', supportsAllDrives=True).execute()
        print(f" Archivo '{file.get('name')}' subido exitosamente a Drive con ID: {file.get('id')}")
    except Exception as e:
        print(f" Error al subir el archivo '{file_name}': {e}")

# === Función Principal ===

def main():
    print("=== Subida de Archivos de Orden a Google Drive ===")

    service = get_drive_service_from_service_account()
    if not service:
        return # Salir si la autenticación falla

    # 1. Solicitar el código de orden al usuario
    codigo_orden = input("Código de orden a procesar (ej. 'ORDEN123'): ")

    # 2. Construir la ruta local a la carpeta de la orden
    local_order_path = os.path.join(LOCAL_ORDERS_BASE_PATH, codigo_orden)

    # 3. Validar que la carpeta de la orden exista localmente
    if not os.path.isdir(local_order_path):
        print(f" Error: La carpeta de la orden local '{local_order_path}' no existe.")
        print("Asegúrate de que el código de orden sea correcto y la carpeta exista en './pedidos/'.")
        return

    # 4. Buscar archivos .gcode y .xlsx en la carpeta local de la orden
    files_to_upload = []
    print(f"Buscando archivos .gcode y .xlsx en '{local_order_path}'...")
    for item in os.listdir(local_order_path):
        item_path = os.path.join(local_order_path, item)
        if os.path.isfile(item_path):
            if item.lower().endswith(('.gcode', '.xlsx')):
                files_to_upload.append(item_path)

    if not files_to_upload:
        print(f" No se encontraron archivos .gcode o .xlsx en la orden local '{codigo_orden}'.")
        return

    print(f"Archivos encontrados para subir: {', '.join([os.path.basename(f) for f in files_to_upload])}")

    # 5. Obtener el ID de la carpeta principal de Google Drive de destino desde la constante
    gdrive_parent_folder_id = get_folder_id_from_url(GDRIVE_MAIN_FOLDER_URL)

    if not gdrive_parent_folder_id:
        print(" Error: No se pudo obtener el ID de la carpeta principal de Drive desde la URL constante.")
        print("Asegúrate de que la URL constante 'GDRIVE_MAIN_FOLDER_URL' sea una URL de carpeta de Drive válida.")
        return

    # 6. Buscar o crear la subcarpeta de destino en Google Drive con el nombre de la orden
    target_gdrive_order_folder_name = codigo_orden # El nombre de la carpeta en Drive será el código de la orden
    target_folder = find_folder_by_name_in_parent(service, gdrive_parent_folder_id, target_gdrive_order_folder_name)

    target_folder_id = None
    if target_folder:
        target_folder_id = target_folder['id']
        print(f"Orden de destino '{target_gdrive_order_folder_name}' encontrada en Drive con ID: {target_folder_id}")
    else:
        print(f"Orden de destino '{target_gdrive_order_folder_name}' no encontrada en Drive. Creando nueva orden (carpeta)...")
        target_folder_id = create_folder(service, target_gdrive_order_folder_name, parent_id=gdrive_parent_folder_id)
        if not target_folder_id:
            print(" Error: No se pudo crear la orden de destino en Google Drive.")
            return

    # 7. Subir los archivos encontrados a la carpeta de Drive de destino
    if target_folder_id:
        print(f"\nSubiendo archivos a la orden '{target_gdrive_order_folder_name}' en Google Drive...")
        for file_path in files_to_upload:
            upload_file(service, file_path, target_folder_id)
    else:
        print(" No se pudo determinar la carpeta de destino en Google Drive para subir los archivos.")

if __name__ == "__main__":
    main()
