# polls/views.py


from django.http import HttpResponse
from .models import Celular, Pedido, Cliente
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import LoginForm
from django.contrib.auth import login, logout
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.backends import BaseBackend


def index(request):
    return render(request, 'polls/index.html')


def productos(request):
    if 'cliente_id' not in request.session:
        return redirect('login')

    id_cliente = request.session.get('cliente_id')
    celulares = Celular.objects.all()

    if request.method == "POST":
        tipo = request.POST.get("tipo")
        color = request.POST.get("color")
        modelo = request.POST.get("modelo")  # Este es el campo `modelo`, no `id_celular`

        try:
            celular = Celular.objects.get(modelo=modelo)
            pedido = Pedido.objects.create(
                id_cliente=id_cliente,
                id_celular=celular.id_celular,
                color=color,
                estado='pendiente',
                cantidad=1,
                aro_dedo=False  # O puedes leerlo de un checkbox si luego lo agregas
            )
            return HttpResponse(
                f"""
                <h1>¡Gracias por tu pedido!</h1>
                <p><strong>Tipo de carcasa:</strong> {tipo}</p>
                <p><strong>Color preferido:</strong> {color}</p>
                <p><strong>Modelo seleccionado:</strong> {celular.marca} {celular.modelo}</p>
                <p><strong>Pedido registrado con ID:</strong> {pedido.id_pedido}</p>
                """
            )
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