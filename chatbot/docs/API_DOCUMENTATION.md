# Documentación de la API del Chatbot

## Introducción

Esta API proporciona acceso a un sistema de chatbot inteligente que utiliza tecnologías avanzadas de IA como RAG (Retrieval Augmented Generation) y búsqueda web para generar respuestas precisas y actualizadas.

## Acceso a la Documentación

### Swagger UI
La documentación interactiva está disponible en:
- **URL**: `/swagger/`
- **Descripción**: Interfaz interactiva para probar todos los endpoints
- **Funciones**: Ejecutar peticiones, ver ejemplos, descargar esquemas

### ReDoc
Documentación alternativa con mejor formato visual:
- **URL**: `/redoc/`
- **Descripción**: Documentación estática con mejor diseño
- **Funciones**: Vista de solo lectura, mejor para referencia

### Esquemas JSON/YAML
Acceso directo a los esquemas de la API:
- **JSON**: `/swagger.json`
- **YAML**: `/swagger.yaml`

## Endpoints Principales

### 1. Envío de Mensajes
**Endpoint**: `POST /api/send_message/`

Procesa mensajes del usuario y devuelve respuestas generadas por el chatbot.

#### Características:
- Utiliza RAG para respuestas contextuales
- Búsqueda web automática cuando es necesario
- Soporte para múltiples modelos de IA
- Logging automático de interacciones

#### Ejemplo de uso:
```bash
curl -X POST http://localhost:8000/api/send_message/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: your-csrf-token" \
  -d '{"message": "¿Cuáles son las últimas noticias sobre IA?"}'
```

### 2. Información del Sistema
**Endpoint**: `GET /api/system_info/`

Obtiene información sobre la configuración actual del sistema.

#### Ejemplo de respuesta:
```json
{
  "bot_type": "cohere",
  "api_version": "v1.0",
  "status": "active",
  "features": ["rag", "web_search", "document_processing"],
  "available_models": ["cohere", "aws_bedrock", "deepseek", "llama"]
}
```

### 3. Health Check
**Endpoint**: `GET /api/health/`

Verificación simple de que la API está funcionando.

## Seguridad

### Protección CSRF
Todos los endpoints que modifican datos requieren un token CSRF válido:
- **Header**: `X-CSRFToken`
- **Obtención**: Desde las cookies del navegador o meta tags HTML

### Configuraciones de Seguridad
- Headers de seguridad configurados
- CORS habilitado para dominios específicos
- Logging de todas las interacciones

## Modelos de IA Soportados

### 1. Cohere (Por defecto)
- Excelente para conversaciones generales
- Respuestas rápidas y coherentes
- Buena comprensión del contexto

### 2. AWS Bedrock
- Acceso a modelos Claude de Anthropic
- Capacidades avanzadas de razonamiento
- Integración con servicios AWS

### 3. DeepSeek
- Especializado en razonamiento y código
- Excelente para consultas técnicas
- Análisis profundo de problemas complejos

### 4. Llama
- Modelo open-source de Meta
- Gran versatilidad
- Buena relación rendimiento/recursos

## Funcionalidades del RAG

### Retrieval Augmented Generation
El sistema utiliza RAG para:
- Acceder a documentos almacenados
- Combinar información con conocimiento del modelo
- Generar respuestas más precisas y actualizadas

### Búsqueda Web
Integración con Tavily para:
- Obtener información actualizada
- Verificar datos en tiempo real
- Expandir el conocimiento base

## Configuración

### Variables de Entorno Requeridas
```bash
DJANGO_SECRET_KEY=your-secret-key
TAVILY_API_KEY=your-tavily-key  # Para búsqueda web
AWS_ACCESS_KEY_ID=your-aws-key  # Para AWS Bedrock
AWS_SECRET_ACCESS_KEY=your-aws-secret
COHERE_API_KEY=your-cohere-key  # Para Cohere
```

### Archivo de Configuración
La configuración se gestiona mediante `chatbot/rag/config/config.json`:
```json
{
  "bot_type": "cohere",
  "bot_config": {
    "cohere": {
      "model": "command-r-plus",
      "temperature": 0.7
    }
  },
  "websearch": {
    "country": "colombia",
    "max_results": 3,
    "search_depth": "advanced"
  }
}
```

## Logging y Monitoreo

### Registro de Interacciones
Todas las conversaciones se registran en:
- **Archivo**: `chatbot/rag/database/log_message_interaction.csv`
- **Campos**: CSRF Token, Mensaje, Respuesta, Timestamp

### Logs del Sistema
Configuración de logging en múltiples niveles:
- **Django**: INFO level
- **Chatbot**: DEBUG level
- **WebSearch**: DEBUG level

## Errores Comunes

### 400 Bad Request
- Mensaje vacío o faltante
- Formato JSON inválido
- Datos de entrada inválidos

### 403 Forbidden
- Token CSRF faltante o inválido
- Permisos insuficientes

### 405 Method Not Allowed
- Método HTTP incorrecto
- Solo POST permitido en `/send_message/`

### 500 Internal Server Error
- Error en el modelo de IA
- Problema de conexión con servicios externos
- Error de configuración

## Mejores Prácticas

### Para el Cliente
1. Siempre incluir el token CSRF
2. Validar datos antes de enviar
3. Manejar errores apropiadamente
4. No enviar mensajes extremadamente largos

### Para el Desarrollo
1. Revisar logs regularmente
2. Monitorear uso de API externa
3. Actualizar modelos según necesidades
4. Implementar rate limiting si es necesario

## Ejemplos de Integración

### JavaScript/AJAX
```javascript
function sendMessage(message) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/api/send_message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({message: message})
    })
    .then(response => response.json())
    .then(data => {
        console.log('Respuesta:', data.response);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
```

### Python requests
```python
import requests

def send_message(message, csrf_token):
    url = 'http://localhost:8000/api/send_message/'
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token
    }
    data = {'message': message}
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()
```

## Soporte y Contacto

Para soporte técnico o preguntas sobre la API, contactar:
- **Email**: contact@chatbot.local
- **Documentación**: Esta documentación y Swagger UI
- **Issues**: Sistema de tickets interno
