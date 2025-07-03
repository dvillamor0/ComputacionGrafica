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


def index(request):
    return render(request, 'polls/index.html')



def productos(request):
    if 'cliente_id' not in request.session:
        return redirect('login')

    id_cliente = request.session.get('cliente_id')
    celulares = Celular.objects.all()

    if request.method == "POST":
        
        color = request.POST.get("color")
        modelo = request.POST.get("modelo")
        acce_medio = request.POST.get("acce_medio")
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
                estado='pendiente',
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