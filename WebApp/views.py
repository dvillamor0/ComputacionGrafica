# polls/views.py


from django.http import HttpResponse
from .models import Celular, Pedido, Cliente, Proveedor
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import LoginForm , ProveedorForm
from django.contrib.auth import login, logout
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.backends import BaseBackend

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from googleapiclient.discovery import build
from google.oauth2 import service_account

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from django.shortcuts import get_object_or_404

SERVICE_ACCOUNT_FILE = r"..\zinc-citron-369904-29288f9a2c6a.json"
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1T7DenpiTeuufp_MbVJmQWKnNcZ1fDSu1ozX9LB4J4d8'
SHEET_NAME = 'pedidos'

def index(request):
    return render(request, 'polls/index.html')

def append_row_to_sheet(values):
    # Autenticación
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SHEETS_SCOPES)
    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()

    # Valores que quieres añadir en la nueva fila
    # Ejemplo: ['valor1', 'valor2', 'valor3', 'valor4', 'valor5']
    
    body = {
        'values': [values]
    }

    # Append the row
    result = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:E",  # Rango donde añadir, puede ser toda la fila para que detecte el final
        valueInputOption="USER_ENTERED",  # Para que los datos se procesen como si los escribieras en la hoja
        insertDataOption="INSERT_ROWS",   # Para insertar una fila nueva
        body=body
    ).execute()

    print(f"{result.get('updates').get('updatedRows')} fila(s) añadida(s).")

def get_sheets_service():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SHEETS_SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service

def actualizar_estado_pagado(id_pedido):
    service = get_sheets_service()
    sheet = service.spreadsheets()

    # Leer todas las filas del rango A:E
    range_ = f"{SHEET_NAME}!A:E"
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_).execute()
    rows = result.get('values', [])

    # Iterar a través de las filas y buscar el ID del pedido
    for i, row in enumerate(rows):
        # Asumiendo que el ID del pedido está en la primera columna (índice 0)
        if row and row[0] == str(id_pedido):  # Compara el ID (convertido a string)
            # Actualizar el estado en la columna E (índice 4)
            row[4] = 'Pagado'

            # Actualizar la fila con el nuevo estado
            update_range = f"{SHEET_NAME}!A{i+1}:E{i+1}"  # La fila específica (i+1 porque las filas de Sheets empiezan en 1)
            body = {
                'values': [row]
            }
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=update_range,
                valueInputOption="USER_ENTERED",  # Para que los datos se procesen como si los escribieras en la hoja
                body=body
            ).execute()
            print(f"Estado del pedido {id_pedido} actualizado a 'Pagado'.")

            try:
                pedido = get_object_or_404(Pedido, id_pedido=id_pedido)  # Buscar el pedido en la base de datos
                pedido.estado = 'Pagado'  # Cambiar el estado
                pedido.save()  # Guardar los cambios en la base de datos
                print(f"Estado del pedido {id_pedido} actualizado a 'Pagado' en la base de datos.")
            except Pedido.DoesNotExist:
                print(f"Pedido con ID {id_pedido} no encontrado en la base de datos.")

            return  # Salir después de actualizar
            return  # Salir después de actualizar

    print(f"Pedido con ID {id_pedido} no encontrado.")

def marcar_como_pagado(request, id_pedido):
    actualizar_estado_pagado(id_pedido)
    return redirect('historial')

def productos(request):
    if 'cliente_id' not in request.session:
        return redirect('login')

    id_cliente = request.session.get('cliente_id')
    celulares = Celular.objects.all()

    if request.method == "POST":
        
        color = request.POST.get("color")
        modelo = request.POST.get("modelo")
        acce_medio_raw = request.POST.get("acce_medio")

        if acce_medio_raw in [None, '', 'null']:
            acce_medio = None
        else:
            try:
                acce_medio = int(acce_medio_raw)  # o float() si es decimal
            except ValueError:
                acce_medio = None  # o lanza error si prefieres
        cantidad=request.POST.get("cantidad")
        camara=request.POST.get("camara")
        KickStand=request.POST.get("KickStand")
        try:
            celular = Celular.objects.get(modelo=modelo)
            if camara=='si':
                acce_camara=2
            else:
                acce_camara=None


            if KickStand=="si":
                acce_inferio=5
            else:
                acce_inferio=None
            pedido = Pedido.objects.create(
                id_cliente=id_cliente,
                id_celular=celular.id_celular,
                color=color,
                estado='PENDIENTE',
                acce_medio=acce_medio,
                cantidad=cantidad,
                acce_inferio=acce_inferio,
                acce_camara=acce_camara
            )

            # --- Google Drive Setup ---
            SERVICE_ACCOUNT_FILE = r"C:\Users\Estudiante\Downloads\pruebas\pruebas\zinc-citron-369904-29288f9a2c6a.json"
            SCOPES = ['https://www.googleapis.com/auth/drive']
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            drive_service = build('drive', 'v3', credentials=creds)

            # ID del folder padre donde crearás las carpetas de pedidos
            FOLDER_ID = '1Va688GB3nRGIAolJncP-4yZgEdhDsCzz'

            # Crear carpeta con nombre = id_pedido
            folder_metadata = {
                'name': str(pedido.id_pedido),  # nombre carpeta = id_pedido
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [FOLDER_ID]  # carpeta padre
            }
            nueva_fila = [str(pedido.id_pedido), "Filamento PLA "+str(pedido.color), '', '', 'Pendiente']
            append_row_to_sheet(nueva_fila)

            folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')
            print(f"Carpeta creada en Drive con ID: {folder_id}")

            return redirect('historial')
        except Celular.DoesNotExist:
            return HttpResponse("<h2>Error: Modelo de celular no encontrado.</h2>")


    return render(request, 'polls/productos.html', {'celulares': celulares})

# Opcional: Backend personalizado (si quieres integrarlo al sistema auth)
class ClienteBackend(BaseBackend):
    def authenticate(self, request, correo=None, contraseña=None):
        try:
            cliente = Cliente.objects.get(correo=correo)
            if cliente.contraseña == contraseña: 
                return cliente
        except Cliente.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Cliente.objects.get(pk=user_id)
        except Cliente.DoesNotExist:
            return None
        
from django.contrib.auth.hashers import check_password

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo']
            contraseña = form.cleaned_data['contraseña']
            try:
                cliente = Cliente.objects.get(correo=correo)
                if check_password(contraseña, cliente.contraseña):  # 👈 Comparación correcta
                    request.session['cliente_id'] = cliente.id_cliente
                    request.session['cliente_nombre'] = cliente.nombre
                    return redirect('index')  # Asegúrate que esta URL existe
                else:
                    messages.error(request, 'Contraseña incorrecta.')
            except Cliente.DoesNotExist:
                messages.error(request, 'Correo no registrado.')
    else:
        form = LoginForm()

    return render(request, 'polls/login.html', {'form': form})

from .forms import RegistroForm
from django.contrib.auth.hashers import make_password

def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo']
            if Cliente.objects.filter(correo=correo).exists():
                messages.error(request, 'El correo ya está registrado.')
            else:
                cliente = Cliente(
                    nombre=form.cleaned_data['nombre'],
                    apellido=form.cleaned_data['apellido'],
                    correo=correo,
                    celular=form.cleaned_data['celular'],
                    direccion=form.cleaned_data['direccion'],
                    contraseña=make_password(form.cleaned_data['contraseña'])  # hash seguro
                )
                cliente.save()
                messages.success(request, 'Registro exitoso. Ya puedes iniciar sesión.')
                return redirect('login')  # Cambia esto al nombre real de tu URL de login
    else:
        form = RegistroForm()

    return render(request, 'polls/registro.html', {'form': form})


def logout_view(request):
    request.session.flush()
    return redirect('index')


def historial_pedidos(request):
    if 'cliente_id' not in request.session:
        return redirect('login')

    cliente_id = request.session['cliente_id']
    pedidos = Pedido.objects.filter(id_cliente=cliente_id).order_by('-fecha')

    # Puedes obtener también info del celular si usas ForeignKey, o con joins manuales
    celulares = {c.id_celular: f"{c.marca} {c.modelo}" for c in Celular.objects.all()}

    for p in pedidos:
        p.modelo_texto = celulares.get(p.id_celular, "Desconocido")

    return render(request, 'polls/historial.html', {'pedidos': pedidos})


def todos_los_pedidos(request):
    if request.session.get('cliente_nombre') != 'prueba':  
        return redirect('login')
    pedidos = Pedido.objects.all().order_by('-fecha')
    clientes = {c.id_cliente: f"{c.nombre} {c.apellido}" for c in Cliente.objects.all()}
    celulares = {c.id_celular: f"{c.marca} {c.modelo}" for c in Celular.objects.all()}

    for p in pedidos:
        p.cliente_nombre = clientes.get(p.id_cliente, "Desconocido")
        p.modelo_texto = celulares.get(p.id_celular, "Desconocido")

    return render(request, 'polls/admin_pedidos.html', {'pedidos': pedidos})

def lista_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'polls/lista_proveedores.html', {'proveedores': proveedores})

def registrar_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm()
    
    return render(request, 'polls/registro_proveedor.html', {'form': form})