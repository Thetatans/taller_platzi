from django import forms
import requests


class ProductForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        label='Nombre del Producto',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa el nombre del producto',
            'id': 'title'
        })
    )
    
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        label='Precio',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0',
            'id': 'price'
        })
    )
    
    description = forms.CharField(
        label='Descripción',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describe el producto...',
            'id': 'description'
        })
    )
    
    category_id = forms.ChoiceField(
        label='Categoría',
        choices=[],  # Se llenarán dinámicamente
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'category_id'
        })
    )
    
    # Campo para múltiples imágenes (URLs)
    images = forms.CharField(
        required=False,
        label='Imágenes del Producto (URLs separadas por comas)',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'https://ejemplo.com/imagen1.jpg, https://ejemplo.com/imagen2.jpg',
            'id': 'images'
        }),
        help_text='Ingresa las URLs de las imágenes separadas por comas'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtener categorías dinámicamente
        self.fields['category_id'].choices = self.get_category_choices()
    
    def get_category_choices(self):
        """Obtiene las categorías disponibles desde la API"""
        try:
            response = requests.get('https://api.escuelajs.co/api/v1/categories', timeout=10)
            if response.status_code == 200:
                categories = response.json()
                choices = [('', 'Selecciona una categoría')]
                choices.extend([(cat['id'], cat['name']) for cat in categories])
                return choices
        except requests.exceptions.RequestException:
            pass
        
  
    
    def clean_price(self):
        """Validación personalizada para el precio"""
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError('El precio debe ser mayor que cero.')
        return price
    
    def clean_images(self):
        """Validación y procesamiento de las URLs de imágenes"""
        images_text = self.cleaned_data.get('images', '').strip()
        
        if not images_text:
            # Imagen por defecto si no se proporciona ninguna
            return ['https://via.placeholder.com/640x480?text=No+Image']
        
        # Separar URLs por comas y limpiar espacios
        urls = [url.strip() for url in images_text.split(',') if url.strip()]
        
        # Validar que sean URLs válidas
        validated_urls = []
        for url in urls:
            if not url.startswith(('http://', 'https://')):
                raise forms.ValidationError(f'URL inválida: {url}. Debe comenzar con http:// o https://')
            validated_urls.append(url)
        
        return validated_urls if validated_urls else ['https://via.placeholder.com/640x480?text=No+Image']
    
    def clean_category_id(self):
        """Validación para la categoría"""
        category_id = self.cleaned_data.get('category_id')
        if not category_id:
            raise forms.ValidationError('Debes seleccionar una categoría.')
        try:
            return int(category_id)
        except (ValueError, TypeError):
            raise forms.ValidationError('ID de categoría inválido.')

