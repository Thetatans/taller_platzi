import requests
import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from .forms import UserRegistrationForm, UserLoginForm

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer
)


# URL base de tu API (configurable desde settings)
API_BASE_URL = "http://127.0.0.1:8000/api/"

@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    """
    Vista API para el registro de nuevos usuarios.
    
    Endpoint: POST /api/register/
    
    Parámetros esperados:
    - username: nombre de usuario único
    - email: correo electrónico válido
    - password: contraseña (mínimo 8 caracteres)
    - password2: confirmación de contraseña
    - first_name: nombre (opcional)
    - last_name: apellido (opcional)
    
    Respuestas:
    - 201: Usuario creado exitosamente
    - 400: Error en validación de datos
    """
    if request.method == 'POST':
        # Creamos el serializer con los datos recibidos
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            # Guardamos el nuevo usuario
            user = serializer.save()
            
            # Creamos o obtenemos el token de autenticación para el usuario
            token, created = Token.objects.get_or_create(user=user)
            
            # Preparamos la respuesta con los datos del usuario y su token
            response_data = {
                'success': True,
                'message': 'Usuario registrado satisfactoriamente',
                'user': UserSerializer(user).data,
                'token': token.key
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        # Si hay errores de validación, los devolvemos
        return Response({
            'success': False,
            'message': 'Error en el registro',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """
    Vista API para el inicio de sesión de usuarios.
    
    Endpoint: POST /api/login/
    
    Parámetros esperados:
    - username: nombre de usuario
    - password: contraseña
    
    Respuestas:
    - 200: Autenticación exitosa
    - 400: Error en credenciales
    """
    if request.method == 'POST':
        # Creamos el serializer con los datos de login
        serializer = UserLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Obtenemos el usuario validado
            user = serializer.validated_data['user']
            
            # Iniciamos sesión en Django (opcional, para mantener sesión)
            login(request, user)
            
            # Creamos o obtenemos el token de autenticación
            token, created = Token.objects.get_or_create(user=user)
            
            # Preparamos la respuesta exitosa
            response_data = {
                'success': True,
                'message': 'Autenticación satisfactoria',
                'user': UserSerializer(user).data,
                'token': token.key
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        # Si hay errores de autenticación
        return Response({
            'success': False,
            'message': 'Error en la autenticación',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """
    Vista API para cerrar sesión.
    
    Endpoint: POST /api/logout/
    Requiere: Token de autenticación en headers
    
    Respuestas:
    - 200: Sesión cerrada exitosamente
    - 401: No autorizado (sin token válido)
    """
    if request.method == 'POST':
        try:
            # Eliminamos el token del usuario
            request.user.auth_token.delete()
            
            # Cerramos la sesión de Django
            logout(request)
            
            return Response({
                'success': True,
                'message': 'Sesión cerrada exitosamente'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al cerrar sesión',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_api(request):
    """
    Vista API para obtener el perfil del usuario actual.
    
    Endpoint: GET /api/profile/
    Requiere: Token de autenticación en headers
    
    Respuestas:
    - 200: Datos del usuario
    - 401: No autorizado (sin token válido)
    """
    if request.method == 'GET':
        # Devolvemos los datos del usuario autenticado
        serializer = UserSerializer(request.user)
        
        return Response({
            'success': True,
            'user': serializer.data
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def check_username_api(request):
    """
    Vista API para verificar disponibilidad de nombre de usuario.
    
    Endpoint: GET /api/check-username/?username=nombreusuario
    
    Parámetros de query:
    - username: nombre de usuario a verificar
    
    Respuestas:
    - 200: Información sobre disponibilidad
    """
    username = request.GET.get('username', '')
    
    if not username:
        return Response({
            'success': False,
            'message': 'Debe proporcionar un nombre de usuario'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verificamos si el username existe
    exists = User.objects.filter(username=username).exists()
    
    return Response({
        'success': True,
        'available': not exists,
        'message': 'Nombre de usuario no disponible' if exists else 'Nombre de usuario disponible'
    }, status=status.HTTP_200_OK)

@csrf_protect
@never_cache
def register_view(request):
    """Vista para mostrar y procesar el formulario de registro"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        # Validaciones
        if not username or not email or not password:
            messages.error(request, 'Por favor, completa todos los campos obligatorios.')
            return render(request, 'register.html')
        
        # Verificar que las contraseñas coincidan
        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'register.html')
        
        # Verificar longitud mínima de contraseña
        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return render(request, 'register.html')
        
        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Este nombre de usuario ya está en uso.')
            return render(request, 'register.html')
        
        # Verificar si el email ya existe
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Este email ya está registrado.')
            return render(request, 'register.html')
        
        try:
            # Crear el usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            messages.success(request, '¡Cuenta creada exitosamente! Ya puedes iniciar sesión.')
            return redirect('platziapp:home')  # Redirigir al login después del registro exitoso
            
        except Exception as e:
            messages.error(request, 'Error al crear la cuenta. Inténtalo de nuevo.')
            return render(request, 'register.html')
    
    # Si es GET, mostrar el formulario de registro
    return render(request, 'register.html')

@csrf_protect
@never_cache
def login_view(request):
    """Vista para mostrar y procesar el formulario de login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Validar que los campos no estén vacíos
        if not username or not password:
            messages.error(request, 'Por favor, completa todos los campos.')
            return render(request, 'login.html')
        
        # Autenticar usuario
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.username}!')
            # Redirigir a la página deseada después del login
            return redirect('platziapp:home')
        else:
            messages.error(request, 'Credenciales incorrectas. Inténtalo de nuevo.')
            return render(request, 'login.html')
    
    # Si es GET, mostrar el formulario de login
    return render(request, 'login.html')

def logout_view(request):
    """
    Vista para cerrar sesión
    """
    username = request.user.username if request.user.is_authenticated else None
    
    # Opcional: llamar al endpoint de logout de la API
    if 'api_token' in request.session:
        try:
            requests.post(
                f"{API_BASE_URL}logout/",
                json={'refresh_token': request.session.get('refresh_token', '')},
                headers={
                    'Authorization': f'Bearer {request.session["api_token"]}',
                    'Content-Type': 'application/json'
                },
                timeout=5
            )
        except:
            pass  # Si falla, continuar con el logout local
        
        # Limpiar tokens de la sesión
        del request.session['api_token']
        if 'refresh_token' in request.session:
            del request.session['refresh_token']
    
    # Cerrar sesión en Django
    logout(request)
    
    if username:
        messages.success(request, f'Has cerrado sesión exitosamente, {username}. ¡Hasta pronto!')
    else:
        messages.success(request, 'Has cerrado sesión exitosamente.')
    
    return redirect('accounts:login')