import os
import io
import psycopg2
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from fpdf import FPDF

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# === CONFIGURACIÓN ===
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "recontra"
}

POSTGRES_QUERY_INVENTARIO = """
SELECT p.id_producto, p.nombre, i.cantidad, p.unidad
FROM productos p
JOIN inventario i ON i.id_producto = p.id_producto;
"""

POSTGRES_QUERY_PROVEEDORES = """
SELECT p.id_proveedor, p.nombre, p.correo, PP.precio, PP.tiempo_entrega, i.nombre
FROM proveedores p
JOIN proveedor_producto PP ON PP.id_proveedor = p.id_proveedor 
JOIN productos i ON i.id_producto = PP.id_producto;
"""

SERVICE_ACCOUNT_FILE = r"pruebas\zinc-citron-369904-29288f9a2c6a.json"
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1T7DenpiTeuufp_MbVJmQWKnNcZ1fDSu1ozX9LB4J4d8'
SHEET_RANGE = 'pedidos!A2:E'

DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = '1Va688GB3nRGIAolJncP-4yZgEdhDsCzz'
DOWNLOAD_PATH = r"C:\Users\Estudiante\Downloads\pruebas\pedidos"

SMTP_CONFIG = {
    "host": "smtp.gmail.com",
    "port": 587,
    "user": "coolcasessa@gmail.com",
    "password": "xefc pzpz laeg iuws"  # Contraseña o app password
}


# === FUNCIONES PARA BASE DE DATOS ===

def consultar_postgres(query):
    try:
        with psycopg2.connect(**POSTGRES_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
    except Exception as e:
        print(f"❌ Error en PostgreSQL: {e}")
        return []

def obtener_inventario():
    return consultar_postgres(POSTGRES_QUERY_INVENTARIO)

def obtener_proveedores():
    return consultar_postgres(POSTGRES_QUERY_PROVEEDORES)


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


# === FUNCIONES PARA PDF ===

class PDF(FPDF):
    def header(self):
        pass
    def footer(self):
        pass

def crear_pdf(nombre_archivo, texto_arriba, texto_abajo, imagen_path, carpeta_destino):
    if not os.path.exists(imagen_path):
        print(f"❌ Imagen no encontrada: {imagen_path}")
        return

    pdf = PDF()
    pdf.add_page()

    pdf.set_font("Arial", size=12)
    pdf.cell(0, 50, texto_arriba, ln=True, align="C")

    img_width, img_height = 100, 100
    x = (pdf.w - img_width) / 2
    y = (pdf.h - img_height) / 2
    pdf.image(imagen_path, x=x, y=y, w=img_width, h=img_height)

    pdf.set_xy(pdf.l_margin, y + img_height + 10)
    pdf.cell(0, 10, texto_abajo, ln=True, align="C")

    output_path = os.path.join(carpeta_destino, f"{nombre_archivo}.pdf")
    pdf.output(output_path)
    print(f"✅ PDF creado: {output_path}")


# === FUNCIONES PARA ENVÍO DE CORREOS ===

def enviar_correo(destinatario, asunto, cuerpo):
    remitente = SMTP_CONFIG['user']
    password = SMTP_CONFIG['password']

    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto
    mensaje.attach(MIMEText(cuerpo, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_CONFIG['host'], SMTP_CONFIG['port'])
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, mensaje.as_string())
        print(f"Correo enviado a {destinatario}")
    except Exception as e:
        print(f"Error al enviar correo a {destinatario}: {e}")
    finally:
        server.quit()


# === LÓGICA PRINCIPAL ===

def main():
    print("=== 📦 Consultando base de datos PostgreSQL ===")
    inventario = obtener_inventario()
    proveedores = obtener_proveedores()

    print(f"Inventario: {len(inventario)} productos obtenidos.")
    print(f"Proveedores: {len(proveedores)} proveedores obtenidos.")

    print("\n=== 📄 Leyendo pedidos desde Google Sheets ===")
    datos_sheets = leer_google_sheets()

    pedidos_generados = [fila for fila in datos_sheets if len(fila) > 4 and fila[4].lower() == "generado"]
    pedidos_pagados = [fila for fila in datos_sheets if len(fila) > 4 and fila[4].lower() == "pagado"]

    print(f"Pedidos generados: {len(pedidos_generados)}")
    print(f"Pedidos pagados: {len(pedidos_pagados)}")

    # Descargar imágenes de pedidos generados
    nombres_imagenes = [f"{fila[0]}.jpg" for fila in pedidos_generados]
    descargar_imagenes_drive_por_subcarpeta(nombres_imagenes)

    # Generar PDFs para pedidos generados
    for pedido in pedidos_generados:
        codigo = pedido[0]
        nombre_producto_pedido = pedido[1]
        cantidad_pedido = int(pedido[2])

        # Buscar inventario para el producto
        inventario_producto = next((item for item in inventario if item[1] == nombre_producto_pedido), None)

        tiempo_proveedor = 0
        if inventario_producto and inventario_producto[2] < cantidad_pedido:
            # Buscar proveedor para producto
            proveedor_producto = next((p for p in proveedores if p[5] == nombre_producto_pedido), None)
            if proveedor_producto:
                tiempo_proveedor = proveedor_producto[4]

        carpeta_pedido = os.path.join(DOWNLOAD_PATH, codigo)
        imagen_path = os.path.join(carpeta_pedido, f"{codigo}.jpg")

        crear_pdf(
            nombre_archivo=codigo,
            texto_arriba=f"Tiempo proveedor: {tiempo_proveedor}",
            texto_abajo="Texto debajo de la imagen",
            imagen_path=imagen_path,
            carpeta_destino=carpeta_pedido
        )

    # Procesar pedidos pagados que requieren notificación
    for pedido in pedidos_pagados:
        nombre_producto_pedido = pedido[1]
        cantidad_pedido = int(pedido[2])

        inventario_producto = next((item for item in inventario if item[1] == nombre_producto_pedido), None)
        if inventario_producto and inventario_producto[2] < cantidad_pedido:
            faltante = cantidad_pedido - inventario_producto[2]
            proveedor_producto = next((p for p in proveedores if p[5] == nombre_producto_pedido), None)
            if proveedor_producto:
                destinatario = proveedor_producto[2]
                asunto = "Prueba de correo desde Python"
                cuerpo = f"Hola, necesito: {faltante} de {nombre_producto_pedido}"

                enviar_correo(destinatario, asunto, cuerpo)


if __name__ == '__main__':
    main()
