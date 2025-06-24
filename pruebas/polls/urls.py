from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('productos/', views.productos, name='productos'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    path('historial/', views.historial_pedidos, name='historial'),
    path('admin/pedidos/', views.todos_los_pedidos, name='admin_pedidos'),
]