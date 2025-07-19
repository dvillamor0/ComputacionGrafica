from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import build
import os
import io

from .config import SERVICE_ACCOUNT_FILE, SPREADSHEET_ID, SHEET_RANGE, FOLDER_ID, DOWNLOAD_PATH, SHEETS_SCOPES, DRIVE_SCOPES

# === FUNCIONES PARA GOOGLE SHEETS ===

def leer_google_sheets():
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SHEETS_SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=SHEET_RANGE).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"❌ Error en Google Sheets: {e}")
        return []


# === FUNCIONES PARA GOOGLE DRIVE ===

def descargar_imagenes_drive_por_subcarpeta(nombres_permitidos):
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=DRIVE_SCOPES)
        service = build('drive', 'v3', credentials=creds)

        # Obtener subcarpetas de la carpeta principal
        query_subcarpetas = f"'{FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        resultados_subcarpetas = service.files().list(
            q=query_subcarpetas, fields="files(id, name)", pageSize=100).execute()
        subcarpetas = resultados_subcarpetas.get('files', [])
        dict_subcarpetas = {c['name']: c['id'] for c in subcarpetas}

        for nombre_imagen in nombres_permitidos:
            codigo = os.path.splitext(nombre_imagen)[0]
            if codigo not in dict_subcarpetas:
                print(f"⚠️ No existe subcarpeta para código {codigo}")
                continue

            subfolder_id = dict_subcarpetas[codigo]

            query_imagen = f"'{subfolder_id}' in parents and name = '{nombre_imagen}' and trashed = false"
            resultados_imagen = service.files().list(
                q=query_imagen, fields="files(id, name)", pageSize=1).execute()
            archivos = resultados_imagen.get('files', [])

            if not archivos:
                print(f"⚠️ No se encontró la imagen {nombre_imagen} en la subcarpeta {codigo}")
                continue

            archivo = archivos[0]
            file_id = archivo['id']
            file_name = archivo['name']

            carpeta_pedido = os.path.join(DOWNLOAD_PATH, codigo)
            os.makedirs(carpeta_pedido, exist_ok=True)

            file_path = os.path.join(carpeta_pedido, file_name)

            request = service.files().get_media(fileId=file_id)
            with io.FileIO(file_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        print(f"Descargando {file_name}: {int(status.progress() * 100)}%")

        print("✅ Descarga de imágenes completada.")
    except Exception as e:
        print(f"❌ Error descargando imágenes de Drive: {e}")
        
def obtener_sheets_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return build('sheets', 'v4', credentials=creds)