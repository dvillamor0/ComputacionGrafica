# open_stl.py
# Este script está diseñado para ser ejecutado manualmente antes de iniciar el consumidor.
# Su propósito es asegurar que Inventor esté abierto y el archivo base 'CarcasaBase.ipt' esté cargado.

import os
import win32com.client
import time

from settings import INVENTOR_TEMPLATE_PATH

def ensure_inventor_and_document_open():
    """
    Intenta conectar con una instancia de Inventor y abre el archivo CarcasaBase.ipt
    si no está ya abierto.
    """
    inventor = None
    active_doc = None

    # Comprobar que el archivo de la plantilla existe
    if not os.path.exists(INVENTOR_TEMPLATE_PATH):
        print(f"[ERROR] El archivo de plantilla de Inventor no existe en la ruta: {INVENTOR_TEMPLATE_PATH}")
        print("[ERROR] Verifica la ruta en settings.py y asegúrate de que el archivo exista.")
        return False

    try:
        # Intenta conectar con una instancia existente de Inventor
        inventor = win32com.client.GetActiveObject("Inventor.Application")
        print("[STEP] Inventor ya está abierto.")
    except Exception:
        # Si no está abierto, inicia una nueva instancia
        print("[STEP] Inventor no estaba abierto. Iniciando nueva instancia...")
        inventor = win32com.client.Dispatch("Inventor.Application")
        inventor.Visible = True # Puedes ponerlo en False si no quieres ver la GUI

    # Comprobar si el archivo ya está abierto
    already_open = False
    for doc in inventor.Documents:
        # Comparamos las rutas en minúsculas para evitar problemas de mayúsculas/minúsculas
        if doc.FullFileName.lower() == INVENTOR_TEMPLATE_PATH.lower():
            print(f"[STEP] El archivo '{os.path.basename(INVENTOR_TEMPLATE_PATH)}' ya está abierto.")
            active_doc = doc
            already_open = True
            break

    # Si no está abierto, abrirlo
    if not already_open:
        print(f"[STEP] Abriendo el archivo: {INVENTOR_TEMPLATE_PATH}")
        active_doc = inventor.Documents.Open(INVENTOR_TEMPLATE_PATH)
        # Dar un pequeño tiempo para que Inventor cargue el documento
        time.sleep(2)

    if active_doc:
        print("[DONE] Documento base de Inventor listo.")
        return True
    else:
        print(f"[ERROR] No se pudo asegurar que el documento '{INVENTOR_TEMPLATE_PATH}' esté abierto en Inventor.")
        return False

def open_inventor():
    print("[INIT] Ejecutando script para asegurar que Inventor y CarcasaBase.ipt estén abiertos...")
    if ensure_inventor_and_document_open():
        print("[DONE] Inventor y el documento base están listos para el procesamiento.")
    else:
        print("[ERROR] Hubo un problema al preparar Inventor. Revisa los mensajes de error.")

if __name__ == "__main__":
    open_inventor()

