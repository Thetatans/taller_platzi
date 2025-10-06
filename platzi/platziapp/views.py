from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import redirect
import requests
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q


@login_required(login_url='accounts:login')
# Vista principal para mostrar todos los productos
def products_list(request):
    if request.method == 'GET':
        try:
            # Hacer petición a la API
            response = requests.get('https://api.escuelajs.co/api/v1/products', timeout=10)
            
            # Verificar el status code
            if response.status_code == 200:
                products = response.json()
                
                # Mostrar información de la respuesta
                datos = {
                    'success': True,
                    'nombre': products[0]['title'],
                    'precio': products[0]['price'],
                    'descripcion': products[0]['description'],
                    'imagen': products[0]['images'][0],
                    'categoria': products[0]['category']['name']
                }
                return JsonResponse(datos)
                
            elif response.status_code == 422:
                return JsonResponse({'success': False, 'error': 'No se pudo cargar los productos. Intenta más tarde.'})
            else:
                return JsonResponse({'success': False, 'error': 'Error al cargar los productos'})
                
        except requests.exceptions.RequestException as e:
            return JsonResponse({'success': False, 'error': 'Error de conexión con la API'})
        except (IndexError, KeyError) as e:
            return JsonResponse({'success': False, 'error': 'Error al procesar los datos de la API'})
    
    # Si no es GET, retornar error
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


# Vista para mostrar el detalle de un producto específico
@login_required(login_url='accounts:login')
def product_detail(request, product_id):
    try:
        # Obtener el producto principal
        response = requests.get(f'https://api.escuelajs.co/api/v1/products/{product_id}', timeout=10)
        
        if response.status_code == 200:
            product = response.json()
            
            # Obtener productos relacionados por categoría
            related_products = []
            
            # Si el producto tiene categoría, buscar otros productos de la misma categoría
            if product.get('category') and product.get('category', {}).get('id'):
                category_id = product['category']['id']
                
                try:
                    # Obtener productos de la misma categoría
                    category_response = requests.get(
                        f'https://api.escuelajs.co/api/v1/categories/{category_id}/products',
                        timeout=10
                    )
                    
                    if category_response.status_code == 200:
                        category_products = category_response.json()
                        
                        # Filtrar el producto actual y limitar a 4 productos relacionados
                        related_products = [
                            p for p in category_products 
                            if p.get('id') != product.get('id')
                        ][:4]
                        
                except requests.exceptions.RequestException:
                    # Si falla la petición de categoría, obtener productos aleatorios
                    try:
                        all_products_response = requests.get(
                            'https://api.escuelajs.co/api/v1/products?limit=20',
                            timeout=10
                        )
                        if all_products_response.status_code == 200:
                            all_products = all_products_response.json()
                            # Filtrar el producto actual y tomar 4 aleatorios
                            related_products = [
                                p for p in all_products 
                                if p.get('id') != product.get('id')
                            ][:4]
                    except requests.exceptions.RequestException:
                        related_products = []
            
            else:
                # Si no tiene categoría, obtener productos aleatorios
                try:
                    all_products_response = requests.get(
                        'https://api.escuelajs.co/api/v1/products?limit=20',
                        timeout=10
                    )
                    if all_products_response.status_code == 200:
                        all_products = all_products_response.json()
                        # Filtrar el producto actual y tomar 4 aleatorios
                        related_products = [
                            p for p in all_products 
                            if p.get('id') != product.get('id')
                        ][:4]
                except requests.exceptions.RequestException:
                    related_products = []
            
            context = {
                'product': product,
                'related_products': related_products
            }
            return render(request, 'product_detalles.html', context)
            
        else:
            context = {'error': 'Producto no encontrado'}
            return render(request, 'product_detalles.html', context)
    
    except requests.exceptions.RequestException as e:
        context = {'error': 'Error al cargar el producto'}
        return render(request, 'product_detalles.html', context)




# Vista para la página de inicio
@login_required(login_url='accounts:login')
def inicio(request):
    return render(request, 'inicio.html')
    

@login_required(login_url='accounts:login')
def home(request):
#aparecer inicio.html
    try:
        # Obtener los ultimos productos creados
        response = requests.get('https://api.escuelajs.co/api/v1/products', timeout=10)
        
        if response.status_code == 200:
            all_products = response.json()
            context = {'all_products': all_products}
            return render(request, 'home.html', context)
        else:
            context = {'all_products': []}
            return render(request, 'home.html', context)
                # Obtener los ultimos productos creados


            
    except requests.exceptions.RequestException as e:

        return render(request, 'home.html', context)
    



     #mostrar productos relacionados por categoría en la pagina detalle del producto
@login_required(login_url='accounts:login')
# Vista para crear un nuevo producto
@csrf_exempt
def create_product(request):
    if request.method == 'GET':
        # Obtener categorías disponibles para el formulario
        try:
            response = requests.get('https://api.escuelajs.co/api/v1/categories', timeout=10)
            if response.status_code == 200:
                categories = response.json()
                context = {'categories': categories}
            else:
                context = {'categories': []}
        except requests.exceptions.RequestException:
            context = {'categories': []}
        
        return render(request, 'create_product.html', context)
    
    elif request.method == 'POST':
        try:
            # Obtener datos del formulario
            title = request.POST.get('title')
            price = request.POST.get('price')
            description = request.POST.get('description')
            category_id = request.POST.get('category_id')
            images = request.POST.getlist('images')  # Lista de URLs de imágenes
            
            # Validar datos requeridos
            if not all([title, price, description, category_id]):
                messages.error(request, 'Todos los campos son requeridos')
                return render(request, 'create_product.html')
            
            # Preparar datos para enviar a la API
            product_data = {
                "title": title,
                "price": int(price),
                "description": description,
                "categoryId": int(category_id),
                "images": images if images else ["https://via.placeholder.com/640x480?text=No+Image"]
            }
            
            # Enviar petición POST a la API
            response = requests.post(
                'https://api.escuelajs.co/api/v1/products',
                json=product_data,
                timeout=10
            )
            
            
            if response.status_code == 201:
                new_product = response.json()
                messages.success(request, f'Producto "{title}" creado exitosamente')
                return redirect('platziapp:product_detail', new_product['id'])
                
       
            else:
                messages.error(request, 'Error al crear el producto en la API')
                return JsonResponse({
                    'success': False, 
                    'error': 'Error al crear el producto'
                })
                
        except requests.exceptions.RequestException as e:
            messages.error(request, 'Error de conexión con la API')
            return JsonResponse({
                'success': False, 
                'error': 'Error de conexión con la API'
            })
        except ValueError as e:
            messages.error(request, 'Error en los datos proporcionados')
            return JsonResponse({
                'success': False, 
                'error': 'Error en los datos proporcionados'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})
@login_required(login_url='accounts:login')
@csrf_exempt
def edit_product(request, product_id):
    if request.method == 'GET':
        try:
            # Obtener el producto actual desde la API
            response = requests.get(f'https://api.escuelajs.co/api/v1/products/{product_id}', timeout=10)
            
            if response.status_code == 200:
                product = response.json()
                
                # Obtener categorías para el formulario
                categories_response = requests.get('https://api.escuelajs.co/api/v1/categories', timeout=10)
                categories = categories_response.json() if categories_response.status_code == 200 else []
                
                # Preparar datos iniciales para el formulario
                initial_data = {
                    'title': product.get('title', ''),
                    'price': product.get('price', ''),
                    'description': product.get('description', ''),
                    'category_id': product.get('category', {}).get('id', ''),
                    'images': ', '.join(product.get('images', []))
                }
                
                context = {
                    'product': product,
                    'categories': categories,
                    'initial_data': initial_data,
                    'product_id': product_id
                }
                return render(request, 'edit_product.html', context)
            else:
                messages.error(request, 'Producto no encontrado')
                return redirect('platziapp:products_list')
                
        except requests.exceptions.RequestException as e:
            messages.error(request, 'Error al cargar el producto')
            return redirect('platziapp:products_list')
    
    elif request.method == 'POST':
        try:
            # Obtener datos del formulario
            title = request.POST.get('title')
            price = request.POST.get('price')
            description = request.POST.get('description')
            category_id = request.POST.get('category_id')
            images_text = request.POST.get('images', '').strip()
            
            # Validar datos requeridos
            if not all([title, price, description, category_id]):
                messages.error(request, 'Todos los campos son requeridos')
                return redirect('platziapp:edit_product', product_id=product_id)
            
            # Procesar imágenes
            if images_text:
                images = [url.strip() for url in images_text.split(',') if url.strip()]
            else:
                images = ["https://via.placeholder.com/640x480?text=No+Image"]
            
            # Preparar datos para enviar a la API
            product_data = {
                "title": title,
                "price": int(float(price)),
                "description": description,
                "categoryId": int(category_id),
                "images": images
            }
            
            # Enviar petición PUT a la API para actualizar
            response = requests.put(
                f'https://api.escuelajs.co/api/v1/products/{product_id}',
                json=product_data,
                timeout=10
            )
            
            if response.status_code == 200:
                updated_product = response.json()
                messages.success(request, f'Producto "{title}" actualizado exitosamente')
                return redirect('platziapp:product_detail', product_id=product_id)
            else:
                messages.error(request, 'Error al actualizar el producto en la API')
                return redirect('platziapp:edit_product', product_id=product_id)
                
        except requests.exceptions.RequestException as e:
            messages.error(request, 'Error de conexión con la API')
            return redirect('platziapp:edit_product', product_id=product_id)
        except ValueError as e:
            messages.error(request, 'Error en los datos proporcionados')
            return redirect('platziapp:edit_product', product_id=product_id)
    
    return redirect('platziapp:products_list')

@login_required(login_url='accounts:login')
# Vista para borrar un producto
@csrf_exempt
def delete_product(request, product_id):
    if request.method == 'GET':
        # Mostrar página de confirmación
        try:
            response = requests.get(f'https://api.escuelajs.co/api/v1/products/{product_id}', timeout=10)
            
            if response.status_code == 200:
                product = response.json()
                context = {'product': product}
                return render(request, 'delete_product.html', context)
            else:
                messages.error(request, 'Producto no encontrado')
                return redirect('platziapp:products_list')
                
        except requests.exceptions.RequestException as e:
            messages.error(request, 'Error al cargar el producto')
            return redirect('platziapp:products_list')
    
    elif request.method == 'POST':
        try:
            # Obtener el nombre del producto antes de eliminarlo
            product_response = requests.get(f'https://api.escuelajs.co/api/v1/products/{product_id}', timeout=10)
            product_name = "el producto"
            
              
              
            # peticion de delete ya no va a json sino retorna a home.html 
            if product_response.status_code == 200:
                product = product_response.json()
                product_name = product.get('title', 'el producto')
                return redirect('platziapp:home')
            
            # Enviar petición DELETE a la API
            response = requests.delete(
                f'https://api.escuelajs.co/api/v1/products/{product_id}',
                timeout=10
            )
            
            if response.status_code == 200:
                messages.success(request, f'Producto "{product_name}" eliminado exitosamente')
                return redirect('platziapp:products_list')
            else:
                messages.error(request, 'Error al eliminar el producto')
                return redirect('platziapp:product_detail', product_id=product_id)
                
        except requests.exceptions.RequestException as e:
            messages.error(request, 'Error de conexión con la API')
            return redirect('platziapp:product_detail', product_id=product_id)
    
    return redirect('platziapp:products_list')


