"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Chatbot API",
        default_version='v1',
        description="""
        ## API de Chatbot con RAG y Búsqueda Web

        Esta API proporciona acceso a un sistema de chatbot inteligente que utiliza:
        
        ### Características principales:
        - **RAG (Retrieval Augmented Generation)**: Sistema de generación aumentada por recuperación
        - **Múltiples Modelos de IA**: Soporte para Cohere, AWS Bedrock, DeepSeek y Llama
        - **Búsqueda Web**: Integración con Tavily para búsquedas web en tiempo real
        - **Procesamiento de Documentos**: Capacidad de procesar documentos PDF
        - **Logging de Interacciones**: Registro completo de conversaciones
        
        ### Funcionalidades:
        - Envío de mensajes al chatbot
        - Procesamiento de consultas complejas
        - Búsqueda web contextual
        - Respuestas basadas en documentos
        
        ### Seguridad:
        - Protección CSRF integrada
        - Headers de seguridad configurados
        - Cors configurado para dominios específicos
        """,
        terms_of_service="https://www.example.com/policies/terms/",
        contact=openapi.Contact(email="contact@chatbot.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('chatbot.urls')),
    
    # Swagger UI y documentación API
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API endpoints documentados
    path('api/', include('chatbot.api_urls')),
]
