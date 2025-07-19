from __future__ import annotations
import os
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from PyPDF2 import PdfMerger

from .config import SERVICE_ACCOUNT_FILE, DRIVE_SCOPES, FOLDER_ID, DOWNLOAD_PATH

def descargar_pdfs_drive_por_subcarpeta(nombres_permitidos):
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=DRIVE_SCOPES)
        service = build('drive', 'v3', credentials=creds)

        query_subcarpetas = f"'{FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        resultados_subcarpetas = service.files().list(
            q=query_subcarpetas, fields="files(id, name)", pageSize=100).execute()
        subcarpetas = resultados_subcarpetas.get('files', [])
        dict_subcarpetas = {c['name']: c['id'] for c in subcarpetas}

        for nombre_pdf in nombres_permitidos:
            codigo = os.path.splitext(nombre_pdf)[0]
            if codigo not in dict_subcarpetas:
                print(f"⚠️ No existe subcarpeta para código {codigo}")
                continue

            subfolder_id = dict_subcarpetas[codigo]

            query_pdf = f"'{subfolder_id}' in parents and name = '{nombre_pdf}' and mimeType='application/pdf' and trashed = false"
            resultados_pdf = service.files().list(
                q=query_pdf, fields="files(id, name)", pageSize=1).execute()
            archivos = resultados_pdf.get('files', [])

            if not archivos:
                print(f"⚠️ No se encontró el PDF {nombre_pdf} en la subcarpeta {codigo}")
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

        print("✅ Descarga de PDFs completada.")
    except Exception as e:
        print(f"❌ Error descargando PDFs de Drive: {e}")


def unir_pdf_generado_y_existente(codigo, carpeta_pedido):
    pdf_generado = os.path.join(carpeta_pedido, f"{codigo}.pdf")
    pdf_existente = os.path.join(carpeta_pedido, f"{codigo}.pdf")  # mismo nombre, pero asumimos que el otro está en la carpeta

    # Aquí asumimos que el pdf_existente es otro archivo PDF descargado, 
    # si ambos tienen exactamente el mismo nombre, necesitas que tengan nombres diferentes para no sobrescribir.

    # Por ejemplo, si el pdf descargado se llama "codigo_original.pdf" y el generado "codigo_generado.pdf":
    pdf_existente = os.path.join(carpeta_pedido, f"{codigo}.pdf")  # cambia el nombre si es necesario
    pdf_generado = os.path.join(carpeta_pedido, f"{codigo}_generado.pdf")  # si quieres renombrar al crearlo

    if not os.path.exists(pdf_generado):
        print(f"❌ PDF generado no encontrado: {pdf_generado}")
        return
    if not os.path.exists(pdf_existente):
        print(f"❌ PDF existente no encontrado: {pdf_existente}")
        return

    merger = PdfMerger()
    merger.append(pdf_generado)
    merger.append(pdf_existente)
    

    output_path = os.path.join(carpeta_pedido, f"{codigo}_final.pdf")
    merger.write(output_path)
    merger.close()

    print(f"✅ PDFs unidos en: {output_path}")