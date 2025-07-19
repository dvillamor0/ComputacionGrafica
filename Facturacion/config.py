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

SERVICE_ACCOUNT_FILE = r"../zinc-citron-369904-29288f9a2c6a.json"
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1T7DenpiTeuufp_MbVJmQWKnNcZ1fDSu1ozX9LB4J4d8'
SHEET_RANGE = 'pedidos!A2:E'

DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_ID = '1Va688GB3nRGIAolJncP-4yZgEdhDsCzz'
DOWNLOAD_PATH = r"pedidos"

SMTP_CONFIG = {
    "host": "smtp.gmail.com",
    "port": 587,
    "user": "coolcasessa@gmail.com",
    "password": "xefc pzpz laeg iuws"  # Contraseña o app password
}