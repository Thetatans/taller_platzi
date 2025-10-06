from django.urls import path
from . import views

app_name = 'platziapp'

urlpatterns = [
    # Página de inicio
    path('', views.inicio, name='inicio'),
    
    
    path('/home', views.home,  name='home'),
    # Lista de productos (API endpoint)
    path('api/products/', views.products_list, name='products_list'),
    
    # Detalle de producto específico
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    
    # Crear nuevo producto
    path('product/create/', views.create_product, name='create_product'),
    
    # NUEVAS FUNCIONES
    # Editar producto
    path('product/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    
    # Borrar producto
    path('product/delete/<int:product_id>/', views.delete_product, name='delete_product'),
]