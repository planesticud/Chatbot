# ./chatbot/api_views.py

import json
import os

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from chatbot.rag.handlers.factory import get_qa_handler
from chatbot.rag.utils.utils import log_message_interaction

# Load the configuration file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'rag/config/config.json')

with open(CONFIG_PATH, 'r') as config_file:
    config = json.load(config_file)

# Determine the bot type based on the configuration
BOT_TYPE = config.get('bot_type', 'cohere')  # Default value: "cohere"
BOT_CONFIG = config.get('bot_config', {}).get(BOT_TYPE, {})

# Inicializar el handler correcto basado en el tipo de bot y sus configuraciones
qa_handler = get_qa_handler(BOT_TYPE, BOT_CONFIG)
print(f'INFO: Ejecución tipo {BOT_TYPE}')

# Definir los esquemas para la documentación de Swagger
message_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['message'],
    properties={
        'message': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='El mensaje del usuario que será procesado por el chatbot. Puede contener preguntas, consultas o comandos.',
            example='¿Cuáles son las últimas noticias sobre inteligencia artificial?'
        ),
    },
    description='Datos requeridos para enviar un mensaje al chatbot'
)

message_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'response': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='La respuesta generada por el chatbot utilizando RAG y/o búsqueda web',
            example='Basándome en las últimas búsquedas web, aquí tienes las noticias más recientes sobre IA...'
        ),
    },
    description='Respuesta exitosa del chatbot'
)

error_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Mensaje de error descriptivo',
            example='Método no permitido'
        ),
    },
    description='Respuesta de error'
)

csrf_token_header = openapi.Parameter(
    'X-CSRFToken',
    openapi.IN_HEADER,
    description='Token CSRF requerido para la protección contra ataques CSRF. Se puede obtener desde las cookies o meta tags del frontend.',
    type=openapi.TYPE_STRING,
    required=True
)

@swagger_auto_schema(
    method='post',
    operation_summary='Enviar mensaje al chatbot',
    operation_description="""
    ## Envío de mensaje al chatbot con RAG
    
    Este endpoint procesa mensajes del usuario y devuelve respuestas generadas por el sistema de chatbot.
    
    ### Funcionalidades:
    - **RAG (Retrieval Augmented Generation)**: Utiliza documentos y contexto para generar respuestas más precisas
    - **Múltiples Modelos**: Soporte para diferentes providers de IA (Cohere, AWS Bedrock, DeepSeek, Llama)
    - **Búsqueda Web**: Integración con Tavily para obtener información actualizada de internet
    - **Logging**: Registro automático de todas las interacciones para análisis posterior
    
    ### Proceso de la consulta:
    1. Recibe el mensaje del usuario
    2. Analiza el contexto y determina si necesita búsqueda web
    3. Utiliza el modelo de IA configurado para generar la respuesta
    4. Registra la interacción en el sistema de logging
    5. Devuelve la respuesta procesada
    
    ### Modelos soportados:
    - **Cohere**: Modelo por defecto, excelente para conversaciones generales
    - **AWS Bedrock**: Acceso a modelos Claude y otros modelos de Amazon
    - **DeepSeek**: Modelo especializado en razonamiento y código
    - **Llama**: Modelo open-source de Meta
    
    ### Consideraciones de seguridad:
    - Requiere token CSRF válido
    - Las interacciones son registradas para auditoría
    - Filtros de contenido aplicados automáticamente
    """,
    request_body=message_request_schema,
    responses={
        200: openapi.Response(
            description='Respuesta exitosa del chatbot',
            schema=message_response_schema,
            examples={
                'application/json': {
                    'response': 'Hola! Soy tu asistente de IA. Puedo ayudarte con preguntas generales, búsquedas web, análisis de documentos y mucho más. ¿En qué puedo ayudarte hoy?'
                }
            }
        ),
        400: openapi.Response(
            description='Error en la solicitud - datos inválidos',
            schema=error_response_schema,
            examples={
                'application/json': {
                    'error': 'El campo message es requerido'
                }
            }
        ),
        403: openapi.Response(
            description='Error de autenticación - Token CSRF inválido o faltante',
            schema=error_response_schema,
            examples={
                'application/json': {
                    'error': 'CSRF token inválido'
                }
            }
        ),
        405: openapi.Response(
            description='Método no permitido - Solo se acepta POST',
            schema=error_response_schema,
            examples={
                'application/json': {
                    'error': 'Método no permitido'
                }
            }
        ),
        500: openapi.Response(
            description='Error interno del servidor',
            schema=error_response_schema,
            examples={
                'application/json': {
                    'error': 'Error interno del servidor'
                }
            }
        )
    },
    manual_parameters=[csrf_token_header],
    tags=['Chatbot'],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def send_message_api(request):
    """
    Vista de API documentada para enviar mensajes al chatbot.
    
    Esta vista mantiene la misma funcionalidad que send_message pero con 
    documentación completa para Swagger/OpenAPI.
    """
    try:
        csrf_token = request.META.get('HTTP_X_CSRFTOKEN', 'No CSRF token found')
        
        if not hasattr(request, 'data') or 'message' not in request.data:
            return Response(
                {'error': 'El campo message es requerido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_message = request.data.get('message')
        
        if not user_message or not user_message.strip():
            return Response(
                {'error': 'El mensaje no puede estar vacío'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        response = qa_handler.get_answer(user_message)
        
        try:
            log_message_interaction(str(csrf_token), user_message, response)
        except Exception as e:
            print(f"Error logging interaction: {e}")
        
        return Response({'response': response}, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response(
            {'error': 'Formato JSON inválido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        print(f"Error in send_message_api: {e}")
        return Response(
            {'error': 'Error interno del servidor'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_summary='Obtener información del sistema',
    operation_description="""
    ## Información del sistema de chatbot
    
    Endpoint que proporciona información sobre la configuración actual del sistema de chatbot.
    
    ### Información proporcionada:
    - Tipo de bot actualmente configurado
    - Estado del sistema
    - Versión de la API
    - Modelos disponibles
    - Funcionalidades habilitadas
    
    ### Uso:
    Útil para verificar el estado del sistema y conocer qué modelo de IA está siendo utilizado.
    """,
    responses={
        200: openapi.Response(
            description='Información del sistema',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'bot_type': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Tipo de bot actualmente configurado',
                        example='cohere'
                    ),
                    'api_version': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Versión de la API',
                        example='v1.0'
                    ),
                    'status': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Estado del sistema',
                        example='active'
                    ),
                    'features': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING),
                        description='Lista de funcionalidades habilitadas',
                        example=['rag', 'web_search', 'document_processing', 'conversation_logging']
                    ),
                    'available_models': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING),
                        description='Modelos de IA disponibles',
                        example=['cohere', 'aws_bedrock', 'deepseek', 'llama']
                    )
                }
            ),
            examples={
                'application/json': {
                    'bot_type': 'cohere',
                    'api_version': 'v1.0',
                    'status': 'active',
                    'features': ['rag', 'web_search', 'document_processing', 'conversation_logging'],
                    'available_models': ['cohere', 'aws_bedrock', 'deepseek', 'llama']
                }
            }
        )
    },
    tags=['Sistema'],
)
@api_view(['GET'])
@permission_classes([AllowAny])
def system_info(request):
    """
    Vista para obtener información del sistema de chatbot.
    """
    return Response({
        'bot_type': BOT_TYPE,
        'api_version': 'v1.0',
        'status': 'active',
        'features': [
            'rag',
            'web_search', 
            'document_processing',
            'conversation_logging'
        ],
        'available_models': [
            'cohere',
            'aws_bedrock',
            'deepseek', 
            'llama'
        ]
    }, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_summary='Health check del sistema',
    operation_description="""
    ## Health Check
    
    Endpoint simple para verificar que la API está funcionando correctamente.
    
    ### Uso:
    - Monitoreo de servicios
    - Verificación de disponibilidad
    - Tests de conectividad
    """,
    responses={
        200: openapi.Response(
            description='Sistema funcionando correctamente',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Estado del servicio',
                        example='healthy'
                    ),
                    'timestamp': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Timestamp de la verificación',
                        example='2024-01-15T10:30:00Z'
                    )
                }
            )
        )
    },
    tags=['Sistema'],
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint para monitoreo del sistema.
    """
    from datetime import datetime
    return Response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }, status=status.HTTP_200_OK)
