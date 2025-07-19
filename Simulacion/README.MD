********************************************************************************
*			Computación Grafica-Proyecto final
*
*	Modulo de automatizacion de procesamiento de ordenes de pedidos 
*	registrados en la nube del proyecto (Gdrive)
********************************************************************************

código desarrollado en Python 3.13 con asistencia de IA Gemini


**librerías necesarias indicadas en requeriments.txt


**para ejecutar


-Desde consola Ejecutar la siguiente linea apuntando a la ubicación del proyecto

"C:\<ruta al directorio>\Proyecto\monitor_drive_excel_v2.py"


El script detecta automáticamente cambios en el archivo de Google sheet "pruebas"

-Si se detecta una nueva fila en el archivo se ejecuta el modulo "STL_Gcode_excel", el cual descarga la carpeta con el ID de pedido correspondiente (1, 2, 3, ...) y genera, a partir del archivo en formato .stl contenido en la carpeta, los correspondientes archivos de codigo G (.Gcode) necesario para la impresion y un reporte en formato excel (.xlsx); especificando el gasto de material y tiempo estimado del proceso de impresion.

-Si se detecta un cambio en alguna de las celdas de la columna estado, si alguna cambia a "pagado" se ejecuta en una nueva consola el script "simulate_print_v3.py" el cual despliega una ventana que permite visualizar el porceso de impresion. Una vez finalizada la simulacion (se puede adelantar la visualizacion mediante el boton "ir al final") la ventana y su respectiva consola se cerrara al presionar cualquier tecla señalando que se ha finalizado el proceso de impresion 3D.



