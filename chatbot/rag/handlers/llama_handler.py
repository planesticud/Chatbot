# ./chatbot/rag/handlers/llama_handler.py

import re
import random
import logging
import requests
import json
from langchain_core.prompts import PromptTemplate
from chatbot.rag.utils.singleton_meta import SingletonMeta
from chatbot.rag.handlers.base_handler import BaseQAHandler
from chatbot.rag.utils.patterns import (
    prompt_template,
    greetings,
    greeting_messages,
    farewell,
    farewell_messages,
    gratefulness,
    gratefulness_messages,
)
from websearch.search import search_web

logger = logging.getLogger(__name__)

class QA_LlamaHandler(BaseQAHandler, metaclass=SingletonMeta):
    """
    Handler to manage interactions with the Llama model via REST API
    for generating responses based exclusively on web search results using Tavily.
    """
    
    def __init__(self, api_url: str, model: str, temperature: float = 0.7, max_tokens: int = 500):
        """
        Initializes the handler with API parameters and prompt template.
        Uses web search for context retrieval.

        Args:
            api_url (str): The API endpoint URL for Llama model.
            model (str): The model name to use.
            temperature (float): Level of randomness for response generation.
            max_tokens (int): Maximum number of tokens in the generated response.
        """
        # Avoid multiple initializations
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        # API configuration
        self.api_url = api_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        logger.info(f'Llama API URL: {api_url}')
        logger.info(f'Model: {model}')
        logger.info(f'Temperature: {temperature}')
        logger.info(f'Max Tokens: {max_tokens}')

        # Load prompt template
        self.load_prompt_template()
        
        logger.info('Llama Handler creado correctamente (búsqueda web + API REST).')
        
    def load_prompt_template(self):
        """
        Loads the prompt template for generating queries.
        """
        try:
            self.prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )
            logger.info('PromptTemplate cargado correctamente.')
        except Exception as e:
            logger.error('Ha ocurrido un error al cargar el PromptTemplate.', exc_info=True)

    def get_web_context(self, web_results: list) -> str:
        """
        Optimiza el contexto web combinando múltiples resultados de manera inteligente.
        
        Args:
            web_results (list): Lista de resultados de búsqueda web
            
        Returns:
            str: Contexto web optimizado para el prompt
        """
        if not web_results:
            return ""
        
        context_parts = []
        total_length = 0
        max_context_length = 3000  # Límite para la API de Llama
        
        for i, result in enumerate(web_results):
            # Preferir raw_content sobre content
            content = result.get('raw_content', result.get('content', ''))
            
            if content:
                # Agregar metadatos útiles
                source_info = f"[Fuente {i+1}: {result.get('title', 'Sin título')} - {result.get('url', '')}]"
                formatted_content = f"{source_info}\n{content}\n"
                
                # Control inteligente de longitud
                if total_length + len(formatted_content) <= max_context_length:
                    context_parts.append(formatted_content)
                    total_length += len(formatted_content)
                else:
                    # Incluir parcialmente si queda espacio
                    remaining_space = max_context_length - total_length - len(source_info) - 20
                    if remaining_space > 100:  # Solo si vale la pena
                        truncated_content = content[:remaining_space] + "..."
                        context_parts.append(f"{source_info}\n{truncated_content}\n")
                    break
        
        return "\n".join(context_parts)

    def call_llama_api(self, prompt: str) -> str:
        """
        Realiza una llamada a la API REST de Llama.
        
        Args:
            prompt (str): El prompt completo para enviar al modelo
            
        Returns:
            str: La respuesta del modelo Llama
        """
        try:
            # Preparar el payload
            payload = {
                "model": self.model,
                "prompt": prompt
            }
            
            # Headers para la petición
            headers = {
                "Content-Type": "application/json"
            }
            
            logger.info(f"Enviando petición a API Llama: {self.api_url}")
            
            # Realizar la petición POST
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30  # 30 segundos de timeout
            )
            
            # Verificar status code
            response.raise_for_status()
            
            # Parsear la respuesta JSON
            response_data = response.json()
            
            # Extraer la respuesta del modelo
            if 'response' in response_data:
                return response_data['response']
            else:
                logger.warning(f"Respuesta de API inesperada: {response_data}")
                return "Lo siento, recibí una respuesta inesperada del modelo."
                
        except requests.exceptions.Timeout:
            logger.error("Timeout al conectar con la API de Llama")
            return "Lo siento, la consulta tardó demasiado tiempo. Intenta nuevamente."
            
        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión con la API de Llama")
            return "Lo siento, no pude conectar con el servicio. Verifica la conexión."
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP en API de Llama: {e}")
            return "Lo siento, ocurrió un error en el servicio. Intenta más tarde."
            
        except json.JSONDecodeError:
            logger.error("Error al decodificar la respuesta JSON de la API")
            return "Lo siento, recibí una respuesta malformada del servicio."
            
        except Exception as e:
            logger.error(f"Error inesperado en llamada a API Llama: {e}", exc_info=True)
            return "Lo siento, ocurrió un error inesperado al procesar tu consulta."

    def get_answer(self, query: str) -> str:
        """
        Generates an answer for the given query using the Llama model with web search context.

        Args:
            query (str): The user's query or question.

        Returns:
            str: The response generated by the Llama model.
        """
        try:
            # Verificar patrones predefinidos
            if any(re.match(pattern, query.lower()) for pattern in greetings):
                return random.choice(greeting_messages)
            elif any(re.match(pattern, query.lower()) for pattern in farewell):
                return random.choice(farewell_messages)
            elif any(re.match(pattern, query.lower()) for pattern in gratefulness):
                return random.choice(gratefulness_messages)
            
            # Búsqueda web optimizada
            logger.info(f"Realizando búsqueda web para: '{query}'")
            web_results = search_web(query)
            
            if not web_results:
                logger.warning(f"No se encontraron resultados web para: '{query}'")
                return "Lo siento, no pude encontrar información relevante en la web para responder tu consulta."
            
            # Obtener contexto optimizado
            context = self.get_web_context(web_results)
            
            # Generar prompt completo
            formatted_prompt = self.prompt.format(context=context, question=query)
            
            logger.info(f"Generando respuesta con contexto de {len(web_results)} fuente(s)")
            
            # Llamar a la API de Llama
            response = self.call_llama_api(formatted_prompt)
            
            return response
            
        except Exception as e:
            logger.error('Ha ocurrido un error en la ejecución del Query.', exc_info=True)
            return "Lo siento, ha ocurrido un error al procesar tu consulta." 