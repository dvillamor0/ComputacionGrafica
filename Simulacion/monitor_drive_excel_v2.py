import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import os
import subprocess
import io
import datetime
import sys

# --- Configuración ---
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'zinc-citron-369904-29288f9a2c6a.json'
DRIVE_FILE_ID = '1T7DenpiTeuufp_MbVJmQWKnNcZ1fDSu1ozX9LB4J4d8'
LOCAL_TEMP_FILE = 'temp_excel_file.xlsx'
COLUMN_TO_MONITOR = 'Estado'

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

SCRIPT_1_PATH = os.path.join(CURRENT_DIR, 'STL_Gcode_excel', 'master_workflow.py')
SCRIPT_PRINT_PATH = os.path.join(CURRENT_DIR, 'simulate_print_v3.py') # Apunta al script de visualización

POLLING_INTERVAL_SECONDS = 30

# --- Funciones Auxiliares ---

def authenticate_drive():
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error de autenticación con Google Drive: {e}")
        return None

def download_excel_from_drive(service, file_id, destination_path):
    try:
        request = service.files().export_media(
            fileId=file_id,
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        fh = io.FileIO(destination_path, 'wb')
        downloader = request
        response = downloader.execute()
        fh.write(response)
        fh.close()
        print(f"Archivo '{file_id}' (Google Sheet) exportado y descargado a '{destination_path}'")
        return True
    except HttpError as error:
        print(f"Error al exportar/descargar el archivo de Drive: {error}")
        return False
    except Exception as e:
        print(f"Error inesperado al exportar/descargar: {e}")
        return False

def load_excel_data(file_path):
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}")
        return None

def detect_changes(old_df, new_df, column_to_monitor):
    detected_change_types = {
        'new_rows': False,
        'status_changed_to_pagado': False,
        'new_row_ids': [],
        'pagado_row_ids': []
    }

    id_column = 'Id_pedido'

    if old_df is None:
        print("No hay datos previos para comparar. Se considerará el nuevo archivo como la base.")
        detected_change_types['new_rows'] = True
        if 'Id_pedido' in new_df.columns:
            detected_change_types['new_row_ids'] = new_df['Id_pedido'].tolist()
        return detected_change_types

    if column_to_monitor not in new_df.columns:
        print(f"Error: La columna a monitorear '{column_to_monitor}' no se encontró en el nuevo archivo.")
        return detected_change_types

    if column_to_monitor not in old_df.columns:
        print(f"Advertencia: La columna a monitorear '{column_to_monitor}' no se encontró en el archivo anterior. No se pueden comparar los cambios en esta columna.")
        return detected_change_types

    if id_column not in new_df.columns or id_column not in old_df.columns:
        print(f"Advertencia: La columna '{id_column}' (asumida como ID) no se encontró en ambos DataFrames. La detección de cambios por fila puede ser imprecisa.")
        return detected_change_types


    # --- 1. Detectar nuevas filas ---
    old_ids = set(old_df[id_column]) if id_column in old_df.columns else set()
    new_ids = set(new_df[id_column]) if id_column in new_df.columns else set()

    new_rows_ids = list(new_ids - old_ids)
    if new_rows_ids:
        for new_id in new_rows_ids:
            print(f"Se ha detectado un nuevo pedido: orden Numero {new_id}--------->Procesando Orden")
        detected_change_types['new_rows'] = True
        detected_change_types['new_row_ids'] = new_rows_ids


    # --- 2. Detectar cambios en la columna 'estado' a 'pagado' ---
    merged_df = pd.merge(old_df[[id_column, column_to_monitor]],
                         new_df[[id_column, column_to_monitor]],
                         on=id_column,
                         suffixes=('_old', '_new'),
                         how='inner')

    changed_to_pagado = merged_df[
        (merged_df[f'{column_to_monitor}_old'] != 'pagado') &
        (merged_df[f'{column_to_monitor}_new'] == 'pagado')
    ]

    if not changed_to_pagado.empty:
        for index, row in changed_to_pagado.iterrows():
            first_cell_value = row[id_column]
            print(f"Se ha detectado una orden pagada: Orden Numero {first_cell_value}--------->Iniciando Impresión")
            detected_change_types['pagado_row_ids'].append(first_cell_value)
        detected_change_types['status_changed_to_pagado'] = True

    return detected_change_types

def execute_another_script(script_path, *args, open_new_console=False):
    """Ejecuta otro script de Python con argumentos opcionales.
    Si open_new_console es True, intenta abrir una nueva ventana de consola.
    """
    command = [sys.executable, script_path] + list(args)
    
    print(f"Ejecutando script: {' '.join(command)}...")

    if open_new_console:
        if sys.platform.startswith('win'):
            try:
                subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
                print(f"Script '{os.path.basename(script_path)}' iniciado en una nueva ventana de consola.")
            except Exception as e:
                print(f"Error al intentar abrir '{script_path}' en nueva consola (Windows): {e}")
                try:
                    result = subprocess.run(command, capture_output=True, text=True, check=True)
                    print("Salida del script (fallback):")
                    print(result.stdout)
                    if result.stderr:
                        print("Errores del script (fallback):")
                        print(result.stderr)
                except subprocess.CalledProcessError as e:
                    print(f"Error al ejecutar el script '{script_path}' (fallback):")
                    print(f"Código de retorno: {e.returncode}")
                    print(f"Salida estándar: {e.stdout}")
                    print(f"Salida de error: {e.stderr}")
        else:
            print(f"Advertencia: Abrir una nueva consola visible en {sys.platform} requiere un emulador de terminal específico (ej. xterm, gnome-terminal).")
            print("El script se ejecutará en segundo plano.")
            try:
                subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
            except Exception as e:
                print(f"Error al intentar ejecutar '{script_path}' en segundo plano: {e}")
                try:
                    result = subprocess.run(command, capture_output=True, text=True, check=True)
                    print("Salida del script (fallback):")
                    print(result.stdout)
                    if result.stderr:
                        print("Errores del script (fallback):")
                        print(result.stderr)
                except subprocess.CalledProcessError as e:
                    print(f"Error al ejecutar el script '{script_path}' (fallback):")
                    print(f"Código de retorno: {e.returncode}")
                    print(f"Salida estándar: {e.stdout}")
                    print(f"Salida de error: {e.stderr}")
    else:
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print(result.stdout)
            if result.stderr:
                print("Errores del script:")
                print(result.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Error al ejecutar el script '{script_path}':")
            print(f"Código de retorno: {e.returncode}")
            print(f"Salida estándar: {e.stdout}")
            print(f"Salida de error: {e.stderr}")
        except FileNotFoundError:
            print(f"Error: El script '{script_path}' no se encontró. Asegúrate de que la ruta es correcta.")
        except Exception as e:
            print(f"Error inesperado al intentar ejecutar el script: {e}")

# --- Bucle Principal ---
def main():
    drive_service = authenticate_drive()
    if not drive_service:
        print("No se pudo autenticar con Google Drive. Saliendo.")
        return

    previous_df = None

    if os.path.exists(LOCAL_TEMP_FILE):
        print(f"Cargando archivo temporal existente: {LOCAL_TEMP_FILE}")
        previous_df = load_excel_data(LOCAL_TEMP_FILE)
    else:
        print("No se encontró archivo temporal previo. La primera descarga será la base.")

    while True:
        print(f"\nConsultando archivo de Drive: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        success = download_excel_from_drive(drive_service, DRIVE_FILE_ID, LOCAL_TEMP_FILE)

        if success:
            current_df = load_excel_data(LOCAL_TEMP_FILE)
            if current_df is not None:
                if previous_df is not None:
                    detected_changes = detect_changes(previous_df, current_df, COLUMN_TO_MONITOR)

                    if detected_changes['new_rows']:
                        print("Ejecutando master_workflow.py para nuevas filas.")
                        for new_id in detected_changes['new_row_ids']:
                            execute_another_script(SCRIPT_1_PATH, str(new_id))

                    if detected_changes['status_changed_to_pagado']:
                        print("Ejecutando simulate_print_v3.py para cambios de estado a 'pagado'.")
                        # Iterar sobre cada ID pagado y ejecutar el script para cada uno
                        for paid_id in detected_changes['pagado_row_ids']:
                            execute_another_script(SCRIPT_PRINT_PATH, str(paid_id), open_new_console=True)

                    if not detected_changes['new_rows'] and not detected_changes['status_changed_to_pagado']:
                        print("No se detectaron cambios que requieran acción.")

                    previous_df = current_df.copy()

                else:
                    print("Primera carga de datos exitosa. Estableciendo la base para futuras comparaciones.")
                    previous_df = current_df.copy()
            else:
                print("No se pudieron cargar los datos del archivo Excel descargado.")
        else:
            print("No se pudo descargar el archivo de Drive. Reintentando en el próximo ciclo.")

        time.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
