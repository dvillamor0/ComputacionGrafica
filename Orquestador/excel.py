# excel/excel_generator.py

import os
import openpyxl # Importa la librería para trabajar con archivos Excel

from settings import EXCEL_TEMPLATE_PATH # Solo necesitamos la ruta de la plantilla

def generate_order_excel(order_data: dict, order_id: int) -> str:
    """
    Inserta los datos del pedido y del celular en el archivo Excel 'DataInventor.xlsx'
    """
    # La ruta de salida ahora es directamente la ruta de la plantilla
    output_file_path = EXCEL_TEMPLATE_PATH

    print(f"[STEP] Cargando Excel para sobreescribir datos en: {output_file_path}")
    try:
        # Carga el libro de trabajo (workbook) existente desde la plantilla
        workbook = openpyxl.load_workbook(output_file_path)
        sheet = workbook.active # Obtiene la hoja activa
    except FileNotFoundError:
        print(f"[ERROR] Archivo Excel 'DataInventor.xlsx' no encontrado en: {output_file_path}")
        print("[ERROR] Asegúrate de que 'files/DataInventor.xlsx' exista y sea accesible.")
        raise # Relanza el error si el archivo no existe

    print(f"[STEP] Insertando datos para Pedido ID {order_id} en DataInventor.xlsx...")

    # Mapeo de los campos de la base de datos a las celdas de Excel (Columna B)
    # Basado en el formato de la imagen proporcionada.
    data_map = {
        'alto': 'B1',
        'ancho': 'B2',
        'grosor': 'B3',
        'radioesquina': 'B4',
        'xcamara': 'B5',
        'ycamara': 'B6',
        'radiocamara': 'B7',
        'anchocamara': 'B8',
        'altocamara': 'B9',
        'xii': 'B10',
        'xif': 'B11',
        'xsi': 'B12',
        'xsf': 'B13',
        'ydi': 'B14',
        'ydf': 'B15',
        'yii': 'B16',
        'yif': 'B17',
        'xhuella': 'B18',
        'yhuella': 'B19',
        'radiohuella': 'B20',
        'anchohuella': 'B21',
        'altohuella': 'B22',
        'radioesquinahuella': 'B23',
        'R': 'B24',
        'G': 'B25',
        'B': 'B26',
        'Wallet': 'B35',
        'Pop': 'B36',
        'Kick': 'B37',
        'TapaCamara': 'B38',
        'Anillo': 'B39',
        'Pedido': 'B40',
    }

    # Iterar sobre el mapa y asignar los valores a las celdas correspondientes
    color_str = order_data.get('color', '')
    r, g, b = ('', '', '')
    
    if color_str:
        try:
            r, g, b = color_str.split(',')
        except Exception:
            print(f"[WARN] Color mal formado: {color_str}")

    for db_field, cell_address in data_map.items():
        if db_field == 'R':
            sheet[cell_address] = r
        elif db_field == 'G':
            sheet[cell_address] = g
        elif db_field == 'B':
            sheet[cell_address] = b
        elif db_field == 'Pedido':
            sheet[cell_address] = order_id
        else:
            value = order_data.get(db_field)
            # Formatear valores numéricos a una cadena con ",mm" si no son None
            # y reemplazar el punto decimal por coma para el formato español
            if value is not None and isinstance(value, (int, float)):
                sheet[cell_address] = f"{value:.3f} mm".replace('.', ',') 
            else:
                # Si el valor es None, dejar la celda vacía o con una cadena vacía
                sheet[cell_address] = value if value is not None else "" 

    try:
        # Guarda el libro de trabajo modificado. Esto sobreescribe el archivo original.
        workbook.save(output_file_path)
        print(f"[DONE] Datos insertados y DataInventor.xlsx sobreescrito.")
        return output_file_path
    except Exception as e:
        print(f"[ERROR] No se pudo guardar el archivo Excel: {e}")
        raise # Relanza el error si no se puede guardar
