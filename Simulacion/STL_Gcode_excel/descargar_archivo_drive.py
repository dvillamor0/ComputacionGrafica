import os
import io
import gdown
from google.oauth2 import service_account
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs

# === Configuraciones ===

# Ruta al archivo de credenciales de la cuenta de servicio
SERVICE_ACCOUNT_FILE = r"zinc-citron-369904-29288f9a2c6a.json" # Asegúrate de que esta ruta sea correcta en tu entorno.
                                                            # Si el JSON está en una subcarpeta 'pruebas', debería ser r"pruebas\zinc-citron-369904-29288f9a2c6a.json"
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Obtener la ruta absoluta del directorio donde se encuentra el script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# La carpeta base para las descargas 'pedidos' se encuentra en el mismo directorio que el script
DOWNLOAD_PATH_BASE = os.path.join(SCRIPT_DIR, "pedidos")
os.makedirs(DOWNLOAD_PATH_BASE, exist_ok=True) # Asegura que la carpeta base 'pedidos' exista

# === Funciones ===

def get_drive_service_from_service_account():
    """Autentica y devuelve el servicio de Google Drive usando una cuenta de servicio."""
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=DRIVE_SCOPES)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f" Error al autenticar con la cuenta de servicio: {e}")
        print(f"Asegúrate de que el archivo de credenciales '{SERVICE_ACCOUNT_FILE}' exista y sea válido.")
        return None

def find_folder_by_name(service, folder_name):
    """Busca una carpeta (orden) por su nombre en Google Drive."""
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"

    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name, parents)').execute()
    items = results.get('files', [])
    return items[0] if items else None

def download_gdrive_folder(folder_id, target_output_path, order_number):
    """
    Descarga una carpeta de Google Drive por su ID usando gdown.
    Los archivos se guardarán directamente en target_output_path.
    """
    print(f"Iniciando descarga de la orden (ID: {folder_id})...")
    print(f"Los archivos se guardarán en: {target_output_path}")

    folder_url = f"https://drive.google.com/drive/folders/{folder_id}"

    try:
        gdown.download_folder(url=folder_url, output=target_output_path, quiet=False , use_cookies=False) # quiet=False paar generar mensaje de progreso de descarga
        print(f"Orden Numero {order_number} procesada exitosamente.")
    except Exception as e:
        print(f"\nOcurrió un error durante la descarga con gdown: {e}")
        print("Asegúrate de que el ID de la orden sea correcto y la cuenta de servicio tenga acceso.")

def main():
    print("=== Descarga de Orden de Google Drive ===")

    service = get_drive_service_from_service_account()
    if not service:
        return

    nombre_carpeta_a_descargar = input("Código de orden a procesar: ")

    print(f"Buscando la orden '{nombre_carpeta_a_descargar}' en Google Drive...")
    found_folder = find_folder_by_name(service, nombre_carpeta_a_descargar)

    if found_folder:
        folder_id = found_folder['id']
        folder_name = found_folder['name']
        print(f"Orden '{folder_name}' encontrada (ID: {folder_id}).")

        output_folder_path = os.path.join(DOWNLOAD_PATH_BASE, folder_name)
        os.makedirs(output_folder_path, exist_ok=True)

        download_gdrive_folder(folder_id, output_folder_path, folder_name)
    else:
        print(f"Error: No se encontró ninguna orden con el nombre '{nombre_carpeta_a_descargar}' en Google Drive.")
        print("Verifica el código de orden e intenta de nuevo.")

if __name__ == "__main__":
    main()
