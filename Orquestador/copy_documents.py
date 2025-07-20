
import shutil
import os
from settings import SOURCE_BASE_DIR, TARGET_BASE_DIR

def copy_order_folder(order_id):
    """
    Copia la carpeta correspondiente al pedido actual a la carpeta destino.
    Args:
        order_id (int): ID del pedido.
        source_base_dir (str): Directorio base donde están las carpetas de pedidos.
        target_base_dir (str): Directorio destino donde se copiará la carpeta.
    """
    folder_name = str(order_id)
    source_folder = os.path.join(SOURCE_BASE_DIR, folder_name)
    target_folder = os.path.join(TARGET_BASE_DIR, folder_name)
    if not os.path.exists(source_folder):
        print(f"[ERROR] La carpeta de pedido '{source_folder}' no existe.")
        return False
    try:
        shutil.copytree(source_folder, target_folder, dirs_exist_ok=True)
        print(f"[DONE] Carpeta de pedido '{folder_name}' copiada a '{TARGET_BASE_DIR}'.")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo copiar la carpeta: {e}")
        return False
