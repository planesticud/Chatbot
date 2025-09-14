# ./chatbot/serializers.py

from rest_framework import serializers

class MessageRequestSerializer(serializers.Serializer):
    """
    Serializer para las solicitudes de mensajes al chatbot.
    """
    message = serializers.CharField(
        max_length=5000,
        help_text="El mensaje del usuario que será procesado por el chatbot. Puede contener preguntas, consultas o comandos.",
        style={'base_template': 'textarea.html', 'rows': 4}
    )
    
    def validate_message(self, value):
        """
        Valida que el mensaje no esté vacío y tenga contenido útil.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("El mensaje no puede estar vacío.")
        
        if len(value.strip()) < 2:
            raise serializers.ValidationError("El mensaje debe tener al menos 2 caracteres.")
        
        return value.strip()

class MessageResponseSerializer(serializers.Serializer):
    """
    Serializer para las respuestas del chatbot.
    """
    response = serializers.CharField(
        help_text="La respuesta generada por el chatbot utilizando RAG y/o búsqueda web"
    )

class SystemInfoSerializer(serializers.Serializer):
    """
    Serializer para la información del sistema.
    """
    bot_type = serializers.CharField(
        help_text="Tipo de bot actualmente configurado"
    )
    api_version = serializers.CharField(
        help_text="Versión de la API"
    )
    status = serializers.CharField(
        help_text="Estado del sistema"
    )
    features = serializers.ListField(
        child=serializers.CharField(),
        help_text="Lista de funcionalidades habilitadas"
    )
    available_models = serializers.ListField(
        child=serializers.CharField(),
        help_text="Modelos de IA disponibles"
    )

class HealthCheckSerializer(serializers.Serializer):
    """
    Serializer para el health check.
    """
    status = serializers.CharField(
        help_text="Estado del servicio"
    )
    timestamp = serializers.CharField(
        help_text="Timestamp de la verificación"
    )

class ErrorResponseSerializer(serializers.Serializer):
    """
    Serializer para respuestas de error.
    """
    error = serializers.CharField(
        help_text="Mensaje de error descriptivo"
    )
