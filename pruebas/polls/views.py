# polls/views.py

from django.shortcuts import render
from django.http import HttpResponse
from .models import Celular

def index(request):
    return render(request, 'polls/index.html')

from django.shortcuts import render
from django.http import HttpResponse
from .models import Celular

def productos(request):
    celulares = Celular.objects.all()
    print("Celulares:", list(celulares))  # Revisa en consola/terminal
    if request.method == "POST":
        tipo = request.POST.get("tipo")
        color = request.POST.get("color")
        modelo_id = request.POST.get("modelo")

        try:
            celular = Celular.objects.get(id=modelo_id)
            modelo_nombre = f"{celular.marca} {celular.modelo}"
        except Celular.DoesNotExist:
            modelo_nombre = "Modelo no encontrado"

        return HttpResponse(
            f"""
            <h1>¡Gracias por participar!</h1>
            <p><strong>Tipo de carcasa:</strong> {tipo}</p>
            <p><strong>Color preferido:</strong> {color}</p>
            <p><strong>Modelo seleccionado:</strong> {modelo_nombre}</p>
            """
        )

    return render(request, 'polls/productos.html', {'celulares': celulares})

