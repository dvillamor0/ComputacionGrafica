import win32com.client
import os
import time
from settings import INVENTOR_TEMPLATE_PATH

def run_inventor_vba_macro():
    """
    Ejecuta una macro de VBA específica de un documento de Inventor desde Python.

    Args:
        No requiere argumentos, los parámetros se definen internamente.
    """
    inventor_app = None
    document = None

    # Definir parámetros internos
    inventor_document_path = INVENTOR_TEMPLATE_PATH
    vba_project_name = "ThisDocument"
    module_name = "Module1"
    macro_name = "CambiarColorYGuardarImagen"

    try:
        # Intentar conectar a una instancia de Inventor existente
        try:
            inventor_app = win32com.client.GetObject("Inventor.Application")
            print("[STEP] Conectado a una instancia existente de Inventor.")
        except Exception:
            print("[STEP] No se encontró una instancia de Inventor. Iniciando una nueva...")
            inventor_app = win32com.client.Dispatch("Inventor.Application")
            inventor_app.Visible = True # Haz Inventor visible

        # Abrir el documento de Inventor
        # Asegurarse de que el documento no esté ya abierto
        doc_opened = False
        for doc in inventor_app.Documents:
            if os.path.normpath(doc.FullFileName) == os.path.normpath(inventor_document_path):
                document = doc
                doc_opened = True
                print(f"[STEP] El documento '{os.path.basename(inventor_document_path)}' ya está abierto.")
                break

        if not doc_opened:
            print(f"[STEP] Abriendo documento: {inventor_document_path}")
            # Solo se admiten documentos de pieza según tu macro VBA
            file_extension = os.path.splitext(inventor_document_path)[1].lower()
            if file_extension == ".ipt":
                # False para no hacer visible el documento al abrir si Inventor ya estaba abierto
                document = inventor_app.Documents.Open(inventor_document_path, False)
            else:
                raise ValueError("Este macro solo funciona con documentos de pieza (.ipt).")
            print(f"[STEP] Documento '{os.path.basename(inventor_document_path)}' abierto exitosamente.")

        # Pausa pequeña para asegurar que el documento se cargue completamente en la UI
        # Esto puede ser útil especialmente si Inventor se acaba de iniciar
        time.sleep(1)

        # Acceder al proyecto VBA del documento
        vba_project = None
        try:
            # En Inventor, las macros incrustadas en el documento suelen estar en el VBAProject del documento.
            # El nombre de este proyecto es a menudo el nombre del archivo de Inventor sin extensión,
            # o "ThisDocument" si no tiene un nombre explícito.
            # Para la mayoría de los casos de macros incrustadas, acceder directamente a document.VBAProject es la forma correcta.
            vba_project = document.VBAProject
            # Si el vba_project_name proporcionado no coincide con el nombre real del proyecto,
            # aún así usamos el proyecto del documento si se encontró.
            if vba_project_name != vba_project.Name:
                print(f"[WARN] Se solicitó el proyecto VBA '{vba_project_name}', pero el proyecto del documento es '{vba_project.Name}'. Se utilizará el proyecto del documento.")
            print(f"[STEP] Accediendo al proyecto VBA incrustado en el documento: {vba_project.Name}")
        except Exception as e:
            raise ValueError(f"No se pudo acceder al proyecto VBA del documento '{document.FullFileName}': {e}")


        if not vba_project:
            raise ValueError(f"No se pudo encontrar el proyecto VBA '{vba_project_name}'.")

        # Acceder al módulo VBA
        vba_module = None
        for component in vba_project.InventorVBAComponents:
            if component.Name == module_name:
                vba_module = component
                print(f"[STEP] Módulo VBA '{module_name}' encontrado.")
                break
        if not vba_module:
            raise ValueError(f"No se encontró el módulo VBA '{module_name}' en el proyecto '{vba_project.Name}'.")

        # Acceder a la macro
        vba_member = None
        for member in vba_module.InventorVBAMembers:
            if member.Name == macro_name:
                vba_member = member
                print(f"[STEP] Macro '{macro_name}' encontrada en el módulo '{module_name}'.")
                break
        if not vba_member:
            raise ValueError(f"No se encontró la macro '{macro_name}' en el módulo '{module_name}'.")

        # Ejecutar la macro
        print(f"[STEP] Ejecutando la macro '{macro_name}'...")
        vba_member.Execute() # Tu macro no espera argumentos de Python

        print(f"[DONE] Macro '{macro_name}' ejecutada exitosamente.")

    except Exception as e:
        print(f"[ERROR] Se produjo un error en la macro de Inventor: {e}")
    finally:
        # Aquí puedes decidir qué hacer al finalizar.
        # Por seguridad, no cerramos Inventor automáticamente a menos que lo desees explícitamente.
        # Si quieres que Inventor se cierre al finalizar (solo si tu script lo abrió), descomenta la siguiente línea
        # if 'inventor_app' in locals() and inventor_app is not None and not doc_opened: # Solo si lo iniciamos nosotros
        #    inventor_app.Quit()
        pass

# --- EJEMPLO DE USO ---

if __name__ == "__main__":
    # Define la ruta a tu documento de Inventor
    # ¡Esta es la ruta específica que proporcionaste!
    inventor_doc_path = r"C:\Users\Lenovo LOQ\Escritorio\ProyectoComp\files\bases\CarcasaBase.ipt"

    # Define los detalles de tu macro VBA
    # "ThisDocument" es el nombre común del proyecto VBA incrustado en el documento.
    vba_project_name = "ThisDocument"
    module_name = "Module1"
    macro_name = "CambiarColorYGuardarImagen"

    print("[STEP] Ejecutando la macro de Inventor...")
    run_inventor_vba_macro(
        inventor_document_path=inventor_doc_path,
        vba_project_name=vba_project_name,
        module_name=module_name,
        macro_name=macro_name
    )

    print("[DONE] Programa Python finalizado.")