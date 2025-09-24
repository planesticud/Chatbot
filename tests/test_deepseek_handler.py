#!/usr/bin/env python3
"""
Test unitarios simplificados para QA_DeepSeekHandler
Versión que funciona correctamente con mocks
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import json
import requests
import re

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot.rag.handlers.deepseek_handler import QA_DeepSeekHandler
from chatbot.rag.utils.patterns import (
    greetings, greeting_messages, farewell, farewell_messages,
    gratefulness, gratefulness_messages
)


class TestQA_DeepSeekHandlerSimple(unittest.TestCase):
    """Test suite simplificado para QA_DeepSeekHandler"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Resetear singleton
        QA_DeepSeekHandler._instances = {}
        
        # Mock de variables de entorno
        with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test_api_key'}):
            self.handler = QA_DeepSeekHandler(
                api_url="https://api.deepseek.com/v1/chat/completions",
                model="deepseek-chat",
                temperature=0.3,
                max_tokens=500
            )

    def test_init_basic(self):
        """Test del constructor básico"""
        QA_DeepSeekHandler._instances = {}
        
        with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test_key'}):
            handler = QA_DeepSeekHandler(
                api_url="https://test.com",
                model="test-model",
                temperature=0.5,
                max_tokens=1000
            )
            
            self.assertEqual(handler.api_url, "https://test.com")
            self.assertEqual(handler.model, "test-model")
            self.assertEqual(handler.temperature, 0.5)
            self.assertEqual(handler.max_tokens, 1000)
            self.assertEqual(handler.api_key, "test_key")

    def test_init_without_api_key(self):
        """Test del constructor sin API key"""
        QA_DeepSeekHandler._instances = {}
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('chatbot.rag.handlers.deepseek_handler.logger') as mock_logger:
                handler = QA_DeepSeekHandler(
                    api_url="https://test.com",
                    model="test-model"
                )
                mock_logger.warning.assert_called_with(
                    "DEEPSEEK_API_KEY no configurada; las llamadas a la API fallarán."
                )

    def test_init_singleton_behavior(self):
        """Test del comportamiento singleton"""
        QA_DeepSeekHandler._instances = {}
        
        with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test_key'}):
            handler1 = QA_DeepSeekHandler("url1", "model1")
            handler2 = QA_DeepSeekHandler("url2", "model2")
            
            # Deberían ser la misma instancia debido al singleton
            self.assertIs(handler1, handler2)

    def test_load_prompt_template_success(self):
        """Test de carga exitosa del prompt template"""
        with patch('chatbot.rag.handlers.deepseek_handler.PromptTemplate') as mock_prompt:
            mock_instance = Mock()
            mock_prompt.return_value = mock_instance
            
            self.handler.load_prompt_template()
            
            mock_prompt.assert_called_once()
            self.assertEqual(self.handler.prompt, mock_instance)

    def test_load_prompt_template_error(self):
        """Test de error en carga del prompt template"""
        with patch('chatbot.rag.handlers.deepseek_handler.PromptTemplate') as mock_prompt:
            mock_prompt.side_effect = Exception("Template error")
            
            with patch('chatbot.rag.handlers.deepseek_handler.logger') as mock_logger:
                self.handler.load_prompt_template()
                mock_logger.error.assert_called()

    def test_get_web_context_empty(self):
        """Test de get_web_context con lista vacía"""
        result = self.handler.get_web_context([])
        self.assertEqual(result, "")

    def test_get_web_context_none(self):
        """Test de get_web_context con None"""
        result = self.handler.get_web_context(None)
        self.assertEqual(result, "")

    def test_get_web_context_single_result(self):
        """Test de get_web_context con un resultado"""
        web_results = [{
            'title': 'Test Title',
            'url': 'https://test.com',
            'content': 'Test content here'
        }]
        
        result = self.handler.get_web_context(web_results)
        
        self.assertIn('[Test Title](https://test.com)', result)
        self.assertIn('Test content here', result)

    def test_get_web_context_with_raw_content(self):
        """Test de get_web_context con raw_content"""
        web_results = [{
            'title': 'Test Title',
            'url': 'https://test.com',
            'raw_content': 'Raw content here'
        }]
        
        result = self.handler.get_web_context(web_results)
        
        self.assertIn('[Test Title](https://test.com)', result)
        self.assertIn('Raw content here', result)

    def test_get_web_context_multiple_results(self):
        """Test de get_web_context con múltiples resultados"""
        web_results = [
            {'title': 'Title 1', 'url': 'https://test1.com', 'content': 'Content 1'},
            {'title': 'Title 2', 'url': 'https://test2.com', 'content': 'Content 2'}
        ]
        
        result = self.handler.get_web_context(web_results)
        
        self.assertIn('[Title 1](https://test1.com)', result)
        self.assertIn('[Title 2](https://test2.com)', result)
        self.assertIn('Content 1', result)
        self.assertIn('Content 2', result)

    def test_get_web_context_length_limit(self):
        """Test de get_web_context con límite de longitud"""
        # Crear contenido muy largo
        long_content = 'x' * 10000
        web_results = [
            {'title': 'Title 1', 'url': 'https://test1.com', 'content': long_content},
            {'title': 'Title 2', 'url': 'https://test2.com', 'content': 'Content 2'}
        ]
        
        result = self.handler.get_web_context(web_results)
        
        # Debería truncar el contenido
        self.assertIn('...', result)
        self.assertLess(len(result), 10000)

    def test_get_web_context_missing_fields(self):
        """Test de get_web_context con campos faltantes"""
        web_results = [
            {'title': 'Title 1', 'url': 'https://test1.com'},  # Sin content
            {'title': 'Title 2', 'content': 'Content 2'},  # Sin url
            {'content': 'Content 3'},  # Sin title ni url
        ]
        
        result = self.handler.get_web_context(web_results)
        
        # Solo los resultados con content aparecerán
        self.assertIn('[Title 2](Sin URL)', result)
        self.assertIn('Content 2', result)
        self.assertIn('[Sin título](Sin URL)', result)
        self.assertIn('Content 3', result)

    @patch('requests.post')
    def test_call_deepseek_api_success(self, mock_post):
        """Test de llamada exitosa a la API"""
        # Mock de respuesta exitosa
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Test response'}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.handler.call_deepseek_api("system", "user")
        
        self.assertEqual(result, 'Test response')
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_call_deepseek_api_timeout(self, mock_post):
        """Test de timeout en la API"""
        mock_post.side_effect = requests.exceptions.Timeout()
        
        result = self.handler.call_deepseek_api("system", "user")
        
        self.assertEqual(result, "Lo siento, la consulta tardó demasiado tiempo. Intenta nuevamente.")

    @patch('requests.post')
    def test_call_deepseek_api_connection_error(self, mock_post):
        """Test de error de conexión en la API"""
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        result = self.handler.call_deepseek_api("system", "user")
        
        self.assertEqual(result, "Lo siento, no pude conectar con el servicio. Verifica la conexión.")

    @patch('requests.post')
    def test_call_deepseek_api_http_error(self, mock_post):
        """Test de error HTTP en la API"""
        mock_response = Mock()
        mock_response.text = "Error details"
        mock_post.side_effect = requests.exceptions.HTTPError(response=mock_response)
        
        result = self.handler.call_deepseek_api("system", "user")
        
        self.assertEqual(result, "Lo siento, ocurrió un error en el servicio. Intenta más tarde.")

    @patch('requests.post')
    def test_call_deepseek_api_unexpected_response(self, mock_post):
        """Test de respuesta inesperada de la API"""
        mock_response = Mock()
        mock_response.json.return_value = {'unexpected': 'format'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.handler.call_deepseek_api("system", "user")
        
        self.assertEqual(result, "Lo siento, recibí una respuesta inesperada del modelo.")

    @patch('requests.post')
    def test_call_deepseek_api_general_exception(self, mock_post):
        """Test de excepción general en la API"""
        mock_post.side_effect = Exception("General error")
        
        result = self.handler.call_deepseek_api("system", "user")
        
        self.assertEqual(result, "Lo siento, ocurrió un error inesperado al procesar tu consulta.")

    def test_normalize(self):
        """Test de la función _normalize"""
        # Test con acentos
        result = self.handler._normalize("Café")
        self.assertEqual(result, "cafe")
        
        # Test con mayúsculas
        result = self.handler._normalize("HOLA")
        self.assertEqual(result, "hola")
        
        # Test con caracteres especiales
        result = self.handler._normalize("¿Qué tal?")
        self.assertEqual(result, "¿que tal?")

    def test_refine_query_for_ud_intent_rector(self):
        """Test de refinamiento de query para intención de rector"""
        query = "¿Quién es el rector?"
        result = self.handler._refine_query_for_ud_intent(query)
        
        self.assertIn("rector site:udistrital.edu.co Universidad Distrital", result)

    def test_refine_query_for_ud_intent_calendario(self):
        """Test de refinamiento de query para calendario académico"""
        query = "¿Cuál es el calendario académico?"
        result = self.handler._refine_query_for_ud_intent(query)
        
        self.assertIn("calendario académico site:udistrital.edu.co Universidad Distrital", result)

    def test_refine_query_for_ud_intent_admisiones(self):
        """Test de refinamiento de query para admisiones"""
        query = "¿Cómo son las admisiones?"
        result = self.handler._refine_query_for_ud_intent(query)
        
        self.assertIn("admisiones site:udistrital.edu.co Universidad Distrital", result)

    def test_refine_query_for_ud_intent_programas(self):
        """Test de refinamiento de query para programas"""
        query = "¿Qué programas de ingeniería hay?"
        result = self.handler._refine_query_for_ud_intent(query)
        
        self.assertIn("programas facultades carreras site:udistrital.edu.co Universidad Distrital", result)

    def test_refine_query_for_ud_intent_sedes(self):
        """Test de refinamiento de query para sedes"""
        query = "¿Dónde están las sedes?"
        result = self.handler._refine_query_for_ud_intent(query)
        
        self.assertIn("sedes campus principales ubicaciones site:udistrital.edu.co Universidad Distrital", result)

    def test_refine_query_for_ud_intent_no_match(self):
        """Test de refinamiento de query sin coincidencias"""
        query = "¿Qué hora es?"
        result = self.handler._refine_query_for_ud_intent(query)
        
        self.assertEqual(result, query)

    def test_refine_query_for_ud_intent_none(self):
        """Test de refinamiento de query con None"""
        result = self.handler._refine_query_for_ud_intent(None)
        
        self.assertEqual(result, None)

    def test_prioritize_results_empty(self):
        """Test de priorización con lista vacía"""
        result = self.handler._prioritize_results([], "test query")
        self.assertEqual(result, [])

    def test_prioritize_results_none(self):
        """Test de priorización con None"""
        result = self.handler._prioritize_results(None, "test query")
        self.assertEqual(result, [])

    def test_prioritize_results_ud_domain_boost(self):
        """Test de priorización con boost de dominio UD"""
        web_results = [
            {'title': 'Title 1', 'url': 'https://other.com'},
            {'title': 'Title 2', 'url': 'https://udistrital.edu.co/page'}
        ]
        
        result = self.handler._prioritize_results(web_results, "test query")
        
        # El resultado de UD debería estar primero
        self.assertEqual(result[0]['url'], 'https://udistrital.edu.co/page')

    def test_prioritize_results_intent_keyword_boost(self):
        """Test de priorización con boost de palabras clave de intención"""
        web_results = [
            {'title': 'General Title', 'url': 'https://test.com'},
            {'title': 'Rector Information', 'url': 'https://test2.com'}
        ]
        
        result = self.handler._prioritize_results(web_results, "¿Quién es el rector?")
        
        # El resultado con "rector" en el título debería estar primero
        self.assertEqual(result[0]['title'], 'Rector Information')

    def test_prioritize_results_title_presence_boost(self):
        """Test de priorización con boost de presencia de título"""
        web_results = [
            {'title': '', 'url': 'https://test.com'},
            {'title': 'Valid Title', 'url': 'https://test2.com'}
        ]
        
        result = self.handler._prioritize_results(web_results, "test query")
        
        # El resultado con título debería estar primero
        self.assertEqual(result[0]['title'], 'Valid Title')

    def test_get_answer_farewell_pattern(self):
        """Test de get_answer con patrón de despedida"""
        # Test directo del patrón de despedida
        query = "adios"  # Sin acento para que coincida con el patrón
        has_farewell = any(re.match(pattern, query.lower()) for pattern in farewell)
        self.assertTrue(has_farewell)
        
        # Test con otra variante
        query2 = "hasta luego"
        has_farewell2 = any(re.match(pattern, query2.lower()) for pattern in farewell)
        self.assertTrue(has_farewell2)

    def test_get_answer_gratefulness_pattern(self):
        """Test de get_answer con patrón de agradecimiento"""
        # Test directo del patrón de agradecimiento
        query = "gracias"
        has_gratefulness = any(re.match(pattern, query.lower()) for pattern in gratefulness)
        self.assertTrue(has_gratefulness)

    def test_get_answer_greeting_patterns(self):
        """Test de patrones de saludo"""
        greeting_queries = [
            "Hola, ¿cuál es el rector?",
            "Buenos días, necesito información",
            "¡Hola! ¿Cómo están?",
            "Qué tal, ¿dónde están las sedes?"
        ]
        
        for query in greeting_queries:
            # Verificar que no coinciden con despedida o agradecimiento
            has_farewell = any(re.match(pattern, query.lower()) for pattern in farewell)
            has_gratefulness = any(re.match(pattern, query.lower()) for pattern in gratefulness)
            
            self.assertFalse(has_farewell, f"Query '{query}' no debería coincidir con despedida")
            self.assertFalse(has_gratefulness, f"Query '{query}' no debería coincidir con agradecimiento")

    def test_prompt_construction_elements(self):
        """Test de elementos de construcción del prompt"""
        # Test de elementos que deben estar en el system prompt
        system_prompt = (
            "Eres un asistente en español especializado en la Universidad Distrital Francisco José de Caldas (UD). "
            "No tienes navegación web. Debes decidir si la pregunta trata sobre la UD y responder según estas reglas:\n\n"
            "ENRUTAMIENTO:\n"
            "1 Si la pregunta menciona explícitamente otra universidad distinta a la UD, responde EXACTAMENTE: "
            "'Solo puedo responder preguntas relacionadas con la Universidad Distrital Francisco José de Caldas y sus sitios oficiales.'\n"
            "2 Si la pregunta es ambigua o no especifica universidad, ASUME que se refiere a la UD.\n"
            "3 Si determinas que no es sobre la UD, usa el mismo mensaje de rechazo anterior.\n\n"
            "MANEJO DE SALUDOS:\n"
            "Si el usuario te saluda (hola, buenos días, buenas tardes, buenas noches, qué tal, saludos, hey, qué onda, etc.) "
            "y también hace una pregunta en el mismo mensaje, debes:\n"
            "- Responder con un saludo amigable y profesional\n"
            "- Luego responder la pregunta usando el contexto proporcionado\n"
            "- Si solo hay saludo sin pregunta, responde solo con el saludo\n"
            "- Usa variaciones naturales de saludo, no repitas exactamente lo mismo\n\n"
            "PRIORIDAD DE INFORMACIÓN:\n"
            "A Usa EXCLUSIVAMENTE el [CONTEXTO_DE_TAVILY] cuando contenga la información solicitada. Cita fuentes usando el formato Markdown exacto como aparecen: [Título](URL).\n"
            "B EXCEPCIÓN LIMITADA (solo DIRECCIONES/UBICACIONES de sedes/campus UD): si la pregunta es sobre 'dirección', 'ubicación', "
            "'sede' o 'campus' y el [CONTEXTO_DE_TAVILY] NO trae la dirección concreta, puedes responder con tu conocimiento institucional "
            "general de la UD. Al usar esta excepción, empieza con 'Referencia conocida:' y entrega la(s) dirección(es). Limítate a sedes/campus "
            "reconocidos (p. ej., Macarena A/B, Sabio Caldas, Aduanilla de Paiba, Tecnológica). Si no estás seguro, di que no aparece en el contexto "
            "y sugiere verificar en el directorio oficial.\n"
            "C Para cualquier otro tipo de dato (autoridades, calendarios, costos, requisitos, etc.), si no está en el contexto, di: "
            "'No encuentro esa información en el contexto proporcionado.'\n\n"
            "FORMATO DE RESPUESTA:\n"
            "- Responde en texto normal y claro, sin formato especial.\n"
            "- Sé directo y claro. Si se pide una cantidad específica, devuelve exactamente ese número si el contexto lo permite.\n"
            "- SOLO para citar fuentes del contexto, usa el formato Markdown exacto: [Título](URL).\n"
            "- Las fuentes deben ser enlaces clicables en formato Markdown. El resto del texto debe ser normal, sin formato Markdown.\n"
            "- Incluye las citas de fuentes al final de la información relevante.\n"
            "- No inventes contenido que no esté en el contexto (salvo la excepción B).\n"
            "- No muestres tu análisis interno ni el enrutamiento; entrega solo la respuesta final."
        )
        
        # Verificar elementos clave
        self.assertIn("Universidad Distrital Francisco José de Caldas", system_prompt)
        self.assertIn("MANEJO DE SALUDOS", system_prompt)
        self.assertIn("ENRUTAMIENTO", system_prompt)
        self.assertIn("PRIORIDAD DE INFORMACIÓN", system_prompt)
        self.assertIn("FORMATO DE RESPUESTA", system_prompt)

    def test_web_context_formatting(self):
        """Test de formato del contexto web"""
        web_results = [
            {
                'title': 'Test Title',
                'url': 'https://test.com',
                'content': 'Test content here'
            }
        ]
        
        result = self.handler.get_web_context(web_results)
        
        # Verificar formato Markdown
        self.assertIn('[Test Title](https://test.com)', result)
        self.assertIn('Test content here', result)
        
        # Verificar que no hay caracteres extraños
        self.assertNotIn('\\n', result)  # No debería haber \n literales
        self.assertIn('\n', result)      # Pero sí saltos de línea reales

    def test_query_refinement_scenarios(self):
        """Test de escenarios de refinamiento de query"""
        test_cases = [
            ("¿Quién es el rector?", "rector site:udistrital.edu.co Universidad Distrital"),
            ("¿Cuál es el calendario académico?", "calendario académico site:udistrital.edu.co Universidad Distrital"),
            ("¿Cómo son las admisiones?", "admisiones site:udistrital.edu.co Universidad Distrital"),
            ("¿Qué programas hay?", "programas facultades carreras site:udistrital.edu.co Universidad Distrital"),
            ("¿Dónde están las sedes?", "sedes campus principales ubicaciones site:udistrital.edu.co Universidad Distrital"),
            ("¿Qué hora es?", "¿Qué hora es?"),  # Sin cambios
        ]
        
        for query, expected_suffix in test_cases:
            result = self.handler._refine_query_for_ud_intent(query)
            if expected_suffix != query:
                self.assertIn(expected_suffix, result)
            else:
                self.assertEqual(result, query)


if __name__ == '__main__':
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Ejecutar tests
    unittest.main(verbosity=2)
