# .chatbot/RAG/aws_client.py

import boto3
import logging

# Configuración del logger
logger = logging.getLogger(__name__)

def get_client():
    """Create and return a Boto3 client for the Bedrock Runtime service.

    This function initializes a Boto3 client specifically for the 
    Bedrock Runtime service in the 'us-east-1' region.

    Returns:
        botocore.client.BaseClient: A Boto3 client for the Bedrock Runtime service.

    Raises:
        RuntimeError: If unable to establish a connection with the client.
    """
    try:
        client = boto3.client('bedrock-runtime', region_name='us-east-1')
        logger.info("Cliente de Bedrock Runtime cargado correctamente.")
        return client
    except Exception as e:
        logger.error("Error al conectar con el cliente de Bedrock Runtime: %s", e)
        raise RuntimeError("No se pudo establecer la conexión con el cliente de Bedrock Runtime.") from e
