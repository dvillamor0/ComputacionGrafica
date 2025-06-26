import os
import io
import psycopg2
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from fpdf import FPDF
# === Configuraciones ===

# PostgreSQL
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "recontra"
}
POSTGRES_QUERY = """
SELECT p.id_producto, p.nombre, i.cantidad, p.unidad
FROM productos p
JOIN inventario i ON i.id_producto = p.id_producto;
"""

# Google Sheets
SERVICE_ACCOUNT_FILE = r"C:\Users\Estudiante\Downloads\pruebas\zinc-citron-369904-29288f9a2c6a.json"
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1T7DenpiTeuufp_MbVJmQWKnNcZ1fDSu1ozX9LB4J4d8'
SHEET_RANGE = 'pedidos!A2:E'

# Google Drive
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = '1Va688GB3nRGIAolJncP-4yZgEdhDsCzz'
DOWNLOAD_PATH = r"C:\Users\Estudiante\Downloads\pruebas\pedidos"


# === Funciones ===

def consultar_postgres():
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        cur.execute(POSTGRES_QUERY)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"❌ Error en PostgreSQL: {e}")
        return []


def leer_google_sheets():
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SHEETS_SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=SHEET_RANGE).execute()
        values = result.get('values', [])
        return values
    except Exception as e:
        print(f"❌ Error en Google Sheets: {e}")
        return []



def descargar_imagenes_drive(nombres_permitidos=None):
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=DRIVE_SCOPES)
        service = build('drive', 'v3', credentials=creds)

        if not os.path.exists(DOWNLOAD_PATH):
            os.makedirs(DOWNLOAD_PATH)

        query = f"'{FOLDER_ID}' in parents and mimeType contains 'image/' and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            pageSize=100
        ).execute()

        files = results.get('files', [])

        if not files:
            print('No se encontraron imágenes en la carpeta.')
            return

        # Mostrar todas las imágenes encontradas
        print("Imágenes encontradas:")
        for file in files:
            print(f"- {file['name']}")

        # Si no se especifica lista, descargar todas
        if nombres_permitidos is None:
            nombres_permitidos = [file['name'] for file in files]

        # Descargar solo las que están en la lista
        files_a_descargar = [f for f in files if f['name'] in nombres_permitidos]

        if not files_a_descargar:
            print("No hay imágenes que coincidan con los nombres especificados.")
            return

        print(f"\nDescargando {len(files_a_descargar)} imágenes seleccionadas...")

        for file in files_a_descargar:
            file_id = file['id']
            file_name = file['name']
            print(f"Descargando {file_name}...")

            request = service.files().get_media(fileId=file_id)
            fh = io.FileIO(os.path.join(DOWNLOAD_PATH, file_name), 'wb')
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"Descargando {file_name}: {int(status.progress() * 100)}%")

            fh.close()

        print("Descarga completada.")
    except Exception as e:
        print(f"❌ Error descargando imágenes de Drive: {e}")


# === Función principal ===

def main():
    print("=== Consultando base de datos PostgreSQL ===")
    datos_postgres = consultar_postgres()
    print(f"Datos PostgreSQL obtenidos ({len(datos_postgres)} filas):")
    for fila in datos_postgres:
        print(fila)

    print("\n=== Leyendo datos de Google Sheets ===")
    datos_sheets = leer_google_sheets()
    print(f"Datos Google Sheets obtenidos ({len(datos_sheets)} filas):")
    for fila in datos_sheets:
        # Filtrar filas que no estén entregadas
        if len(fila) > 4 and fila[4].lower() != "entregado":
            print(fila)
            descargar_imagenes_drive(fila[0]+".jpg")
            class PDF(FPDF):
                def header(self):
                    # Puedes agregar encabezado si quieres
                    pass

                def footer(self):
                    # Puedes agregar pie de página si quieres
                    pass

            pdf = PDF()
            pdf.add_page()

            # Texto arriba
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 50, "Este es un texto arriba de la imagen", ln=True, align="C")

            # Obtener ancho y alto de la página
            page_width = pdf.w - 2*pdf.l_margin
            page_height = pdf.h - 2*pdf.t_margin

            # Ruta de la imagen
            image_path = "C:\\Users\\Estudiante\\Downloads\\pruebas\\pedidos\\"+fila[0]+".jpg"  # Cambia esto por el path de tu imagen

            # Tamaño de la imagen para que no sea muy grande (por ejemplo 100x100)
            img_width = 100
            img_height = 100

            # Posición para centrar la imagen en la mitad vertical de la página
            x = (pdf.w - img_width) / 2
            y = (pdf.h - img_height) / 2

            pdf.image(image_path, x=x, y=y, w=img_width, h=img_height)

            # Texto abajo de la imagen (ajustamos la posición y)
            pdf.set_xy(pdf.l_margin, y + img_height + 10)
            pdf.cell(0, 10, "Texto debajo de la imagen", ln=True, align="C")

            # Guardar PDF
            pdf.output("C:\\Users\\Estudiante\\Downloads\\pruebas\\pedidos\\"+fila[0]+".pdf")

            print("PDF creado con éxito.")   


            

    
    

if __name__ == '__main__':
    main()
