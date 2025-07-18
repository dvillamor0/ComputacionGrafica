import os
import io
import psycopg2
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import build
from fpdf import FPDF
from PyPDF2 import PdfMerger
from email.mime.text import MIMEText

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


POSTGRES_QUERY_PEDIDOS = """
SELECT p.id_pedido, p.id_cliente, c.correo, c.nombre, c.apellido, c.direccion
FROM pedidos p
JOIN clientes c ON p.id_cliente = c.id_cliente;
"""

SERVICE_ACCOUNT_FILE = r"pruebas\zinc-citron-369904-29288f9a2c6a.json"
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1T7DenpiTeuufp_MbVJmQWKnNcZ1fDSu1ozX9LB4J4d8'
SHEET_RANGE = 'pedidos!A2:E'

DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = '1Va688GB3nRGIAolJncP-4yZgEdhDsCzz'
DOWNLOAD_PATH = r"\pruebas\pedidos"

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


def obtener_pedidos():
    return consultar_postgres(POSTGRES_QUERY_PEDIDOS)

def actualizar_cantidad_inventario(id_producto, nueva_cantidad):
    """
    Actualiza la cantidad del producto en la tabla inventario según su id.
   
    :param id_producto: int - ID del producto a actualizar.
    :param nueva_cantidad: int - Nueva cantidad a establecer.
    """
    update_query = """
        UPDATE inventario
        SET cantidad = %s
        WHERE id_producto = %s;
    """

    try:
        with psycopg2.connect(**POSTGRES_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(update_query, (nueva_cantidad, id_producto))
                conn.commit()
                print(f"✅ Cantidad actualizada para el producto {id_producto}: {nueva_cantidad}")
    except Exception as e:
        print(f"❌ Error al actualizar inventario: {e}")

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

import os
from fpdf import FPDF

class PDF(FPDF):
    pass  # Asegúrate de tener esta clase definida o usa directamente FPDF()

def crear_pdf(nombre_archivo, texto_arriba, texto_abajo, imagen_path, imagen_esquina_path, carpeta_destino):
    if not os.path.exists(imagen_path):
        print(f"❌ Imagen principal no encontrada: {imagen_path}")
        return
    if not os.path.exists(imagen_esquina_path):
        print(f"❌ Imagen de esquina no encontrada: {imagen_esquina_path}")
        return

    pdf = PDF()
    pdf.add_page()

    # Texto arriba
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 50, texto_arriba, ln=True, align="C")

    # Imagen principal centrada
    img_width, img_height = 100, 100
    x = (pdf.w - img_width) / 2
    y = (pdf.h - img_height) / 2
    pdf.image(imagen_path, x=x, y=y, w=img_width, h=img_height)

    # Imagen quemada en esquina superior derecha (más pequeña)
    esquina_w, esquina_h = 30, 30  # Tamaño pequeño para la esquina
    # Posición: un poco dentro del margen superior derecho
    x_esquina = pdf.w - pdf.r_margin - esquina_w
    y_esquina = pdf.t_margin
    pdf.image(imagen_esquina_path, x=x_esquina, y=y_esquina, w=esquina_w, h=esquina_h)

    # Texto abajo, debajo de la imagen principal
    pdf.set_xy(pdf.l_margin, y + img_height + 10)
    pdf.cell(0, 10, texto_abajo, ln=True, align="C")

    # Guardar PDF
    output_path = os.path.join(carpeta_destino, f"{nombre_archivo}_generado.pdf")
    pdf.output(output_path)
    print(f"✅ PDF creado: {output_path}")



# === FUNCIONES PARA ENVÍO DE CORREOS ===

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

def enviar_correo(destinatario, asunto, cuerpo, archivo_pdf=None):
    remitente = SMTP_CONFIG['user']
    password = SMTP_CONFIG['password']

    # Crear el mensaje
    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto
    mensaje.attach(MIMEText(cuerpo, 'plain'))

    # Adjuntar el archivo PDF si se pasa como argumento
    if archivo_pdf and os.path.isfile(archivo_pdf):
        try:
            with open(archivo_pdf, 'rb') as file:
                adjunto_pdf = MIMEApplication(file.read(), _subtype='pdf')
                adjunto_pdf.add_header('Content-Disposition', 'attachment', filename=os.path.basename(archivo_pdf))
                mensaje.attach(adjunto_pdf)
        except Exception as e:
            print(f"Error al adjuntar el archivo PDF: {e}")

    try:
        # Configurar el servidor SMTP
        server = smtplib.SMTP(SMTP_CONFIG['host'], SMTP_CONFIG['port'])
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, mensaje.as_string())
        print(f"Correo enviado a {destinatario}")
    except Exception as e:
        print(f"Error al enviar correo a {destinatario}: {e}")
    finally:
        server.quit()


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



def obtener_sheets_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return build('sheets', 'v4', credentials=creds)




# === LÓGICA PRINCIPAL ===

def main():
    
    print("=== 📦 Consultando base de datos PostgreSQL ===")
    inventario = obtener_inventario()
    proveedores = obtener_proveedores()
    pedidos=obtener_pedidos()
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
    nombres_pdf = [f"{fila[0]}.pdf" for fila in pedidos_generados]
    descargar_imagenes_drive_por_subcarpeta(nombres_imagenes)
    descargar_pdfs_drive_por_subcarpeta(nombres_pdf)


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
            texto_abajo="Texto debajo de la imagen",
            texto_arriba=f"Tiempo proveedor: {tiempo_proveedor}",
            imagen_path=imagen_path,
            imagen_esquina_path="pruebas\\logosinayudadegptkappa.png",
            carpeta_destino=carpeta_pedido
        )

        unir_pdf_generado_y_existente(codigo, carpeta_pedido)
        for c in pedidos:
            if int(c[0])==int(codigo):
                destinatario = c[2]
                asunto = "Prueba de correo desde Python"
                cuerpo = f"Hola, {c[3]} {c[4]} le en enviamos la cotizacion de su pedido con el pdf de las vistas porfavor abrir en adobe crobat"
                enviar_correo(destinatario, asunto, cuerpo, "pedidos\\2\\"+str(c[0])+"_final.pdf")


                print(c[2])
    # Procesar pedidos pagados que requieren notificación
    for pedido in pedidos_pagados:
        nombre_producto_pedido = pedido[1]
        cantidad_pedido = int(pedido[2])

        # Buscar el producto en el inventario
        inventario_producto = next((item for item in inventario if item[1] == nombre_producto_pedido), None)
        
        if inventario_producto:
            cantidad_disponible = inventario_producto[2]

            # Verificar si hay suficiente inventario
            if cantidad_disponible < cantidad_pedido:
                faltante = (cantidad_pedido - cantidad_disponible) * 10  # Suponiendo que el faltante es la cantidad extra multiplicada por 10
                nueva_cantidad = faltante + cantidad_disponible
                proveedor_producto = next((p for p in proveedores if p[5] == nombre_producto_pedido), None)
                
                # Si encontramos el proveedor, enviamos un correo
                if proveedor_producto:
                    destinatario = proveedor_producto[2]
                    asunto = "Prueba de correo desde Python"
                    cuerpo = f"Hola, necesito: {faltante} de {nombre_producto_pedido}"
                    enviar_correo(destinatario, asunto, cuerpo)

                # Actualizamos el inventario con la nueva cantidad después de recibir más stock
                # Convertimos inventario_producto a lista para poder modificarlo
                inventario_producto = list(inventario_producto)  
                inventario_producto[2] = nueva_cantidad  # Ahora podemos modificar la cantidad
                inventario_producto = list(inventario_producto)  
                inventario_producto[2] -= cantidad_pedido  # Restamos del inventario
                actualizar_cantidad_inventario(inventario_producto[0], inventario_producto[2])
                # Reemplazamos el producto actualizado en el inventario
                for idx, item in enumerate(inventario):
                    if item[0] == inventario_producto[0]:  # Verificamos por el ID del producto
                        inventario[idx] = tuple(inventario_producto)  # Reemplazamos el item en el inventario con la nueva cantidad

            # Si hay suficiente inventario, simplemente restamos la cantidad
            else:
                # Convertimos inventario_producto a lista para poder modificarlo
                inventario_producto = list(inventario_producto)  
                inventario_producto[2] -= cantidad_pedido  # Restamos del inventario
                actualizar_cantidad_inventario(inventario_producto[0],inventario_producto[2])
                # Reemplazamos el producto actualizado en el inventario
                for idx, item in enumerate(inventario):
                    if item[0] == inventario_producto[0]:  # Verificamos por el ID del producto
                        inventario[idx] = tuple(inventario_producto)  # Reemplazamos el item en el inventario con la nueva cantidad

            # Imprimir el inventario actualizado
            print(inventario_producto[2])



    
    
    
    
    datos_sheets = leer_google_sheets()

    sheets_service = obtener_sheets_service()  # Inicializas el servicio de Sheets para modificar

    # Iteramos con índice para saber la fila exacta
    
    for idx, fila in enumerate(datos_sheets, start=2):  # start=2 porque el rango empieza en fila 2

        if len(fila) > 4 and fila[4].lower() == "pagado":
            fila_a_actualizar = idx
            columna = 'E'  # La columna donde está "pagado"
            celda = f'pedidos!{columna}{fila_a_actualizar}'

            # Nuevo valor a escribir
            values = [['Entregado']]  # O lo que quieras poner

            body = {'values': values}

            response = sheets_service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=celda,
                valueInputOption='RAW',
                body=body
            ).execute()

            print(f"Celda {celda} actualizada. Celdas modificadas: {response.get('updatedCells')}")



if __name__ == '__main__':
    main()
