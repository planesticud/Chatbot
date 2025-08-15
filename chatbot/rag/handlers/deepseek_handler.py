# ./chatbot/rag/handlers/deepseek_handler.py

import re
import random
import logging
import os
import requests
from dotenv import load_dotenv
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
import unicodedata

load_dotenv()
logger = logging.getLogger(__name__)

class QA_DeepSeekHandler(BaseQAHandler, metaclass=SingletonMeta):
    """
    Handler to manage interactions with DeepSeek chat API
    for generating responses based on web search results using Tavily.
    """
    
    def __init__(self, api_url: str, model: str, temperature: float = 0.3, max_tokens: int = 500):
        """
        Initializes the handler with API parameters and prompt template.

        Args:
            api_url (str): The DeepSeek chat completions endpoint URL.
            model (str): The DeepSeek model name (e.g., 'deepseek-chat').
            temperature (float): Sampling temperature.
            max_tokens (int): Max tokens for the response.
        """
        # Avoid multiple initializations
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        self.api_url = api_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # API key from environment
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY no configurada; las llamadas a la API fallarán.")

        logger.info(f'DeepSeek API URL: {api_url}')
        logger.info(f'Model: {model}')
        logger.info(f'Temperature: {temperature}')
        logger.info(f'Max Tokens: {max_tokens}')

        # Load prompt template
        self.load_prompt_template()
        
        logger.info('DeepSeek Handler creado correctamente (búsqueda web + API chat).')
        
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
        except Exception:
            logger.error('Ha ocurrido un error al cargar el PromptTemplate.', exc_info=True)

    def get_web_context(self, web_results: list) -> str:
        """
        Formats the web results into a context string for DeepSeek processing.
        """
        if not web_results:
            return ""
        
        context_parts = []
        total_length = 0
        max_context_length = 5000  # Límite algo mayor para mejorar recall
        top_long_budget = 3000      # Presupuesto mayor para el primer resultado
        
        for i, result in enumerate(web_results):
            content = result.get('raw_content', result.get('content', ''))
            if content:
                source_info = f"[Fuente {i+1}] {result.get('title', 'Sin título')} - URL: {result.get('url', 'Sin URL')}"
                content = content.strip()
                if total_length + len(content) + len(source_info) + 2 <= max_context_length:
                    context_parts.append(f"{source_info}\n{content}\n")
                    total_length += len(content) + len(source_info) + 2
                else:
                    # Para el primer resultado, concede un presupuesto mayor de truncado
                    if i == 0 and total_length < top_long_budget:
                        remaining_space = min(top_long_budget - total_length, max_context_length - total_length - len(source_info) - 2)
                    else:
                        remaining_space = max_context_length - total_length - len(source_info) - 2
                    if remaining_space > 0:
                        truncated_content = content[:remaining_space] + "..."
                        context_parts.append(f"{source_info}\n{truncated_content}\n")
                    break
        
        return "\n".join(context_parts)

    def call_deepseek_api(self, system_prompt: str, user_prompt: str) -> str:
        """
        Calls the DeepSeek API (chat completions compatible with OpenAI format).
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
            logger.info("Enviando petición a API DeepSeek")
            resp = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            # Intentar extraer como respuesta estilo OpenAI
            if isinstance(data, dict):
                choices = data.get('choices')
                if choices and isinstance(choices, list):
                    msg = choices[0].get('message') or {}
                    content = msg.get('content')
                    if content:
                        return content
            logger.warning(f"Respuesta de API DeepSeek inesperada: {data}")
            return "Lo siento, recibí una respuesta inesperada del modelo."
        except requests.exceptions.Timeout:
            logger.error("Timeout al conectar con la API de DeepSeek")
            return "Lo siento, la consulta tardó demasiado tiempo. Intenta nuevamente."
        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión con la API de DeepSeek")
            return "Lo siento, no pude conectar con el servicio. Verifica la conexión."
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP en API de DeepSeek: {e}")
            try:
                logger.error(f"Detalle: {resp.text}")
            except Exception:
                pass
            return "Lo siento, ocurrió un error en el servicio. Intenta más tarde."
        except Exception:
            logger.error("Error inesperado en llamada a API DeepSeek", exc_info=True)
            return "Lo siento, ocurrió un error inesperado al procesar tu consulta."

    def _normalize(self, text: str) -> str:
        # Quitar acentos y pasar a minúsculas para comparación robusta
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        return text.lower()   

    def _refine_query_for_ud_intent(self, query: str) -> str:
        """If we detect specific intents, bias the search query toward UD with targeted terms."""
        qn = self._normalize(query or "")
        refined = query
        # Boosters for common intents
        if any(k in qn for k in ["rector", "vicerrector", "directivo", "directivos", "consejo superior"]):
            refined += " rector site:udistrital.edu.co Universidad Distrital"
        elif any(k in qn for k in ["calendario academico", "calendario académico"]):
            refined += " calendario académico site:udistrital.edu.co Universidad Distrital"
        elif any(k in qn for k in ["admisiones", "inscripcion", "inscripciones"]):
            refined += " admisiones site:udistrital.edu.co Universidad Distrital"
        elif any(k in qn for k in ["ingenieria", "ingenierías", "carreras", "programas", "oferta academica", "oferta académica"]):
            refined += " programas facultades carreras site:udistrital.edu.co Universidad Distrital"
        elif any(k in qn for k in ["sedes", "sede", "campus"]):
            refined += " sedes campus principales ubicaciones site:udistrital.edu.co Universidad Distrital"
        return refined

    def _prioritize_results(self, web_results: list, query: str) -> list:
        """Order results to surface the most relevant ones first based on intent keywords and UD domain."""
        qn = self._normalize(query or "")
        intent_keys = [
    "rector","vicerrector","directivo","consejo superior",
    "calendario academico","calendario académico","admisiones",
    "programas","carreras","ingenieria","ingenierías","oferta academica","oferta académica",
    "sedes","sede","campus",
]
        def score(r: dict) -> int:
            title = self._normalize(r.get("title", ""))
            url = self._normalize(r.get("url", ""))
            s = 0
            # UD domain boost
            if "udistrital.edu.co" in url:
                s += 5
            # Intent keyword boosts
            if any(k in title or k in url for k in intent_keys if k in qn):
                s += 5
            # Generic title presence
            if title:
                s += 1
            return s
        return sorted(web_results or [], key=score, reverse=True)

    def get_answer(self, query: str) -> str:
        try:
            # Patrones predefinidos
            if any(re.match(pattern, query.lower()) for pattern in greetings):
                return random.choice(greeting_messages)
            elif any(re.match(pattern, query.lower()) for pattern in farewell):
                return random.choice(farewell_messages)
            elif any(re.match(pattern, query.lower()) for pattern in gratefulness):
                return random.choice(gratefulness_messages)

            # Búsqueda web
            effective_query = self._refine_query_for_ud_intent(query)
            logger.info(f"Realizando búsqueda web para: '{effective_query}'")
            web_results = search_web(effective_query)
            if not web_results:
                logger.warning(f"No se encontraron resultados web para: '{query}'")
                return "Lo siento, no pude encontrar información relevante en la web para responder tu consulta."

            # Priorizar resultados antes de construir el contexto
            web_results = self._prioritize_results(web_results, query)

            # Contexto
            context = self.get_web_context(web_results)
            logger.info(f"Contexto web preparado (len={len(context)} chars, fuentes={len(web_results)})")

            # Construir prompt de usuario con 3 secciones: ANALYSIS, CONTEXT, QUESTION
            formatted_prompt = (
                "INSTRUCCIONES PARA TI (NO MOSTRAR AL USUARIO):\n"
                "Primero, decide internamente si la pregunta es sobre la UD. "
                "No reveles tu análisis; entrega solo la respuesta final.\n\n"
                "[ANALYSIS]\n"
                "Tarea: Decide si la pregunta está relacionada con la UD (sí/no) y si menciona otra universidad explícita.\n"
                "Criterios: Palabras clave, nombres propios, dominio de las fuentes en el contexto, etc.\n\n"
                "[CONTEXTO_DE_TAVILY]\n" + context + "\n\n"
                "[PREGUNTA_DEL_USUARIO]\n" + query
            )

            logger.debug(f"Prompt final (3-partes) construido (len={len(formatted_prompt)} chars)")

            # Construir mensajes: system guía para limpieza y precisión
            system_prompt = (
              "Eres un asistente en español especializado en la Universidad Distrital Francisco José de Caldas (UD). "
              "No tienes navegación web. Debes decidir si la pregunta trata sobre la UD y responder según estas reglas:\n\n"
              "ENRUTAMIENTO:\n"
              "1 Si la pregunta menciona explícitamente otra universidad distinta a la UD, responde EXACTAMENTE: "
              "'Solo puedo responder preguntas relacionadas con la Universidad Distrital Francisco José de Caldas y sus sitios oficiales.'\n"
              "2 Si la pregunta es ambigua o no especifica universidad, ASUME que se refiere a la UD.\n"
              "3 Si determinas que no es sobre la UD, usa el mismo mensaje de rechazo anterior.\n\n"
              "PRIORIDAD DE INFORMACIÓN:\n"
              "A Usa EXCLUSIVAMENTE el [CONTEXTO_DE_TAVILY] cuando contenga la información solicitada. Cita fuentes como [Fuente N] si aparecen.\n"
              "B EXCEPCIÓN LIMITADA (solo DIRECCIONES/UBICACIONES de sedes/campus UD): si la pregunta es sobre 'dirección', 'ubicación', "
              "'sede' o 'campus' y el [CONTEXTO_DE_TAVILY] NO trae la dirección concreta, puedes responder con tu conocimiento institucional "
              "general de la UD. Al usar esta excepción, empieza con 'Referencia conocida:' y entrega la(s) dirección(es). Limítate a sedes/campus "
              "reconocidos (p. ej., Macarena A/B, Sabio Caldas, Aduanilla de Paiba, Tecnológica). Si no estás seguro, di que no aparece en el contexto "
              "y sugiere verificar en el directorio oficial.\n"
              "C Para cualquier otro tipo de dato (autoridades, calendarios, costos, requisitos, etc.), si no está en el contexto, di: "
              "'No encuentro esa información en el contexto proporcionado.'\n\n"
              "FORMATO DE RESPUESTA:\n"
              "- Sé directo y claro. Si se pide una cantidad específica, devuelve exactamente ese número si el contexto lo permite.\n"
              "- Cuando uses el contexto, cita [Fuente N] si corresponde. No inventes contenido que no esté en el contexto (salvo la excepción B).\n"
              "- No muestres tu análisis interno ni el enrutamiento; entrega solo la respuesta final."
          )



            # Llamada a DeepSeek con system rules + prompt de 3 partes (análisis, contexto, pregunta)

            #response = self.call_deepseek_api(system_prompt=context, user_prompt=query)
            response = self.call_deepseek_api(system_prompt=system_prompt, user_prompt=formatted_prompt)
            return response
        except Exception:
            logger.error("Error inesperado en DeepSeekHandler.get_answer", exc_info=True)
            return "Lo siento, ocurrió un error al procesar tu solicitud."
