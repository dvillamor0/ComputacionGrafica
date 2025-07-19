import openpyxl
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials


CARPETA_PEDIDOS = r"C:\Users\Estudiante\Downloads\modulo automatizado 2025_07_14\modulo automatizado 2025_07_14\STL_Gcode_excel\Pedidos"

GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1T7DenpiTeuufp_MbVJmQWKnNcZ1fDSu1ozX9LB4J4d8"     #recordar rutas
GOOGLE_SHEET_NAME = "pedidos"  # Nombre de la hoja en Google Sheets
COLUMNAS_DESTINO = ["C", "D"] # Columnas destino en Google Sheets

CREDENCIALES_JSON = r"C:\Users\Estudiante\Downloads\modulo automatizado 2025_07_14\modulo automatizado 2025_07_14\STL_Gcode_excel\zinc-citron-369904-29288f9a2c6a.json" # Archivo de credenciales #recordar rutas

# --- 1. Encontrar la subcarpeta más reciente y el Excel ---
def encontrar_excel_reciente():
    # Listar todas las subcarpetas en 'pedidos'
    subcarpetas = [d for d in os.listdir(CARPETA_PEDIDOS) if os.path.isdir(os.path.join(CARPETA_PEDIDOS, d))]
    
    if not subcarpetas:
        raise FileNotFoundError("No hay subcarpetas en 'pedidos'")
    
    # Ordenar subcarpetas por fecha de creación (la más reciente primero)
    subcarpetas.sort(key=lambda d: os.path.getmtime(os.path.join(CARPETA_PEDIDOS, d)), reverse=True)
    ultima_subcarpeta = os.path.join(CARPETA_PEDIDOS, subcarpetas[0])
    
    # Buscar el primer archivo .xlsx en la subcarpeta
    for archivo in os.listdir(ultima_subcarpeta):
        if archivo.endswith(".xlsx"):
            return os.path.join(ultima_subcarpeta, archivo)
    
    raise FileNotFoundError(f"No hay archivos Excel en {ultima_subcarpeta}")

# --- 2. Leer datos del Excel ---
def leer_excel(ruta_excel):
    libro = openpyxl.load_workbook(ruta_excel)
    hoja = libro["Reporte"]  # Ajusta el nombre de la hoja
    datos = [hoja["A2"].value,hoja["D2"].value, hoja["E2"].value]  # Celdas a leer
    libro.close()
    return datos

# --- 3. Escribir en Google Sheets ---
def escribir_google_sheets(datos):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENCIALES_JSON, scope)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_url(GOOGLE_SHEET_URL).worksheet(GOOGLE_SHEET_NAME)
        
        # Convertir datos a strings
        datos = [str(d) if d is not None else "" for d in datos]
        
        # Buscar fila
        columna_a = sheet.col_values(1)
        fila_objetivo = next((i for i, v in enumerate(columna_a, 1) if str(v) == datos[0]), None)
        
        if not fila_objetivo:
            raise ValueError(f"Valor {datos[0]} no encontrado en columna A")
        
        # Actualizar en formato correcto (lista de listas)
        sheet.update(f'C{fila_objetivo}', [[datos[1]]])  # Dato D2 → Col C
        sheet.update(f'D{fila_objetivo}', [[datos[2]]])  # Dato E2 → Col D
        sheet.update(f'E{fila_objetivo}', [["generado"]])
        
        print(f"Fila {fila_objetivo} actualizada: A={datos[0]}, C={datos[1]}, D={datos[2]}")
    
    except Exception as e:
        print(f"Error al actualizar Sheet: {e}")
        raise

# --- Ejecución ---
if __name__ == "__main__":
    try:
        ruta_excel = encontrar_excel_reciente()
        print(f"Excel encontrado: {ruta_excel}")
        datos = leer_excel(ruta_excel)
        print(f"Datos leídos: {datos}")
        escribir_google_sheets(datos)
        print("¡Datos transferidos exitosamente!")
    except Exception as e:
        print(f"Error: {e}")