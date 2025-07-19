import os

from .config import DOWNLOAD_PATH, SPREADSHEET_ID
from .db import obtener_inventario, obtener_proveedores, actualizar_cantidad_inventario, obtener_pedidos
from .google import leer_google_sheets, obtener_sheets_service, descargar_imagenes_drive_por_subcarpeta
from .pdf import crear_pdf
from .pdf3d import descargar_pdfs_drive_por_subcarpeta
from .correo import enviar_correo
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


    if len(pedidos_generados) > 0:
        descargar_imagenes_drive_por_subcarpeta(nombres_imagenes)
        descargar_pdfs_drive_por_subcarpeta(nombres_pdf)
    # Generar PDFs para pedidos generados
        for pedido in pedidos_generados:
            codigo = pedido[0]
            nombre_producto_pedido = pedido[1]

            cantidad_pedido = float(pedido[2])

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
            costo = float(pedido[2]) * 500
            tiempo_entrega = pedido[3]

            crear_pdf(
                nombre_archivo=codigo,
                texto_arriba=f"Tiempo proveedor: {tiempo_proveedor} días",
                texto_abajo="Gracias por su compra. Para cualquier consulta, contacte con soporte.",
                imagen_path=imagen_path,
                imagen_esquina_path="pruebas\\IMG-20250711-WA0012.jpg",
                carpeta_destino=carpeta_pedido,
                tiempo_entrega=tiempo_entrega,
                costo_total=costo
            )

            #unir_pdf_generado_y_existente(codigo, carpeta_pedido)
            for c in pedidos:
                if int(c[0])==int(codigo):
                    destinatario = c[2]
                    asunto = "Cotización de su pedido"
                    cuerpo = f"Estimado/a {c[3]} {c[4]},\n\n" \
                            "Le enviamos adjunta la cotización correspondiente a su pedido, así como el PDF con las vistas detalladas.\n\n" \
                            "Quedamos a su disposición para cualquier consulta o aclaración.\n\n" \
                            "Atentamente,\n" \
                            "El equipo de soporte"

                    enviar_correo(destinatario, asunto, cuerpo, "pedidos\\"+str(c[0])+"\\"+str(c[0])+".pdf")
        datos_sheets = leer_google_sheets()

        sheets_service = obtener_sheets_service()  # Inicializas el servicio de Sheets para modificar

        for idx, fila in enumerate(datos_sheets, start=2):  # start=2 porque el rango empieza en fila 2

            if len(fila) > 4 and fila[4].lower() == "generado":
                fila_a_actualizar = idx
                columna = 'E'  # La columna donde está "pagado"
                celda = f'pedidos!{columna}{fila_a_actualizar}'

                # Nuevo valor a escribir
                values = [['Por pagar']]  # O lo que quieras poner

                body = {'values': values}

                response = sheets_service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=celda,
                    valueInputOption='RAW',
                    body=body
                ).execute()

                print(f"Celda {celda} actualizada. Celdas modificadas: {response.get('updatedCells')}")


    if len(pedidos_pagados) > 0:
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
    while True:
        main()