import os
import json
import logging
import time
import re
from datetime import datetime, timezone
from tavily import TavilyClient, MissingAPIKeyError, InvalidAPIKeyError, UsageLimitExceededError
from httpx import TimeoutException, HTTPError

logger = logging.getLogger(__name__)
_tavily_client = None
_SEARCH_CONFIG = None

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chatbot', 'rag', 'config', 'config.json')

# Utilidad para limpiar la consulta
def clean_query(query: str) -> str:
    """
    Limpia y valida la consulta según las mejores prácticas de Tavily.
    """
    cleaned = query.strip().replace('\n', ' ')
    
    # Validar longitud según mejores prácticas de Tavily (máximo 400 caracteres)
    if len(cleaned) > 400:
        logger.warning(f"Consulta muy larga ({len(cleaned)} caracteres), truncando a 400")
        cleaned = cleaned[:400]
    
    return cleaned

def _implies_recency(query: str) -> bool:
    """
    Detecta si la consulta implica necesidad de información reciente.
    """
    q = (query or "").lower()
    recency_terms = [
        'hoy', 'últimas', 'ultimas', 'recientes', 'actual', 'actuales', 'ahora',
        'noticias', 'news', 'hace', 'último', 'ultimo', 'tendencias', 'trend',
        '2025', '2024', '2023'
    ]
    return any(term in q for term in recency_terms)

def _resolve_topic_and_time(search_config: dict, query: str) -> dict:
    """
    Resuelve `topic`  y filtros de tiempo (time_range/days/start_date/end_date)
    usando la configuración y heurísticas basadas en la consulta.
    """
    topic = search_config.get('topic')
    time_range = search_config.get('time_range')
    days = search_config.get('days')
    start_date = search_config.get('start_date')
    end_date = search_config.get('end_date')

    if _implies_recency(query):
        topic = topic or 'news'
        if not any([time_range, days, start_date, end_date]):
            time_range = 'week'  # day|week|month|year
    else:
        topic = topic or 'general'

    return {
        'topic': topic,
        'time_range': time_range,
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
    }

def get_tavily_client():
    global _tavily_client
    if _tavily_client is None:
        try:
            _tavily_client = TavilyClient()
            logger.info("Cliente Tavily inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar cliente Tavily: {e}")
            raise
    return _tavily_client

def get_search_config():
    global _SEARCH_CONFIG
    if _SEARCH_CONFIG is None:
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                websearch_config = config.get('websearch', {})
                _SEARCH_CONFIG = {
                    'include_domains': websearch_config.get('include_domains', []),
                    'country': websearch_config.get('country', 'colombia'),
                    'max_results': websearch_config.get('max_results', 3),
                    'chunks_per_source': websearch_config.get('chunks_per_source', 3),
                    'search_depth': websearch_config.get('search_depth', 'advanced'),
                    # parámetros opcionales de recencia
                    'topic': websearch_config.get('topic'),
                    'time_range': websearch_config.get('time_range'),
                    'days': websearch_config.get('days'),
                    'start_date': websearch_config.get('start_date'),
                    'end_date': websearch_config.get('end_date'),
                }
                logger.info(f"Configuración de búsqueda cargada: {_SEARCH_CONFIG}")
        except Exception as e:
            logger.warning(f"No se pudo leer la configuración de búsqueda web: {e}")
            _SEARCH_CONFIG = {
                'include_domains': [],
                'country': 'colombia',
                'max_results': 3,
                'chunks_per_source': 3,
                'search_depth': 'advanced',
                'topic': None,
                'time_range': None,
                'days': None,
                'start_date': None,
                'end_date': None,
            }
    return _SEARCH_CONFIG

def search_web(query: str) -> list:
    """
    Realiza búsqueda web usando las mejores prácticas de Tavily.
    """
    query = clean_query(query)
    
    if not query:
        logger.error("Consulta vacía después de limpieza")
        return []
    
    try:
        client = get_tavily_client()
        search_config = get_search_config()
    except Exception as e:
        logger.error(f"Error en inicialización: {e}")
        return []
    
    max_retries = 3
    base_wait_time = 1
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Intento {attempt + 1} de búsqueda para: '{query[:50]}...'")
            resolved = _resolve_topic_and_time(search_config, query)
            topic = resolved.get('topic')
            time_range = resolved.get('time_range')
            days = resolved.get('days')
            start_date = resolved.get('start_date')
            end_date = resolved.get('end_date')

            search_kwargs = {
                'query': query,
                'search_depth': search_config['search_depth'],
                'max_results': search_config['max_results'],
                'chunks_per_source': search_config['chunks_per_source'],
                'include_raw_content': True,
                'include_domains': search_config['include_domains'],
            }
            if topic:
                search_kwargs['topic'] = topic
            if time_range:
                search_kwargs['time_range'] = time_range
            if topic == 'news' and days:
                search_kwargs['days'] = days
            if (not topic or topic == 'general') and search_config.get('country'):
                search_kwargs['country'] = search_config['country']
            if start_date:
                search_kwargs['start_date'] = start_date
            if end_date:
                search_kwargs['end_date'] = end_date

            logger.debug(f"Parámetros Tavily resueltos: {search_kwargs}")
            response = client.search(**search_kwargs)
            
            results = response.get('results', [])
            response_time = response.get('response_time', 'N/A')
            
            logger.info(f"Búsqueda exitosa: {len(results)} resultados en {response_time}s para '{query[:30]}' (topic={topic}, time_range={time_range}, days={days})")
            
            # Validar calidad de resultados
            valid_results = []
            for result in results:
                if result.get('content') or result.get('raw_content'):
                    valid_results.append(result)
                else:
                    logger.debug(f"Resultado sin contenido ignorado: {result.get('url', 'URL desconocida')}")
            
            logger.info(f"Resultados válidos: {len(valid_results)}/{len(results)}")
            
            # Reordenamiento por recencia y boletines
            def _score_result(r: dict) -> int:
                s = 0
                title = (r.get('title') or '').lower()
                url = (r.get('url') or '').lower()

                # Recencia basada en published_date/date si viene en ISO
                now = datetime.now(timezone.utc)
                published = r.get('published_date') or r.get('date')
                if isinstance(published, str):
                    try:
                        dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        days_old = (now - dt).days
                        if days_old <= 7:
                            s += 12
                        elif days_old <= 30:
                            s += 9
                        elif days_old <= 180:
                            s += 5
                        elif days_old <= 365:
                            s += 2
                    except Exception:
                        pass

                # Señal por número de boletín en URL
                m = re.search(r"boletin(\d+)", url)
                if m:
                    try:
                        s += min(10, int(m.group(1)))
                    except Exception:
                        pass

                # Señales en el título
                if any(t in title for t in ['nuevo', 'nueva', 'actualizado', 'actualizacion', 'actualización', 'designado', 'nombrado']):
                    s += 4
                if any(t in title for t in ['coordinador', 'director', 'planestic']):
                    s += 2
                return s

            valid_results = sorted(valid_results, key=_score_result, reverse=True)
            return valid_results
        
        except (MissingAPIKeyError, InvalidAPIKeyError) as e:
            logger.error(f"Error de autenticación con Tavily API: {e}")
            logger.error("Verifique que TAVILY_API_KEY esté configurada correctamente")
            return []  # No reintentar errores de API key
        
        except UsageLimitExceededError as e:
            logger.error(f"Límite de uso de Tavily API excedido: {e}")
            logger.error("Verifique su plan y límites de API en https://app.tavily.com")
            return []  # No reintentar límites excedidos
        
        except (TimeoutException, HTTPError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Error de red persistente después de {max_retries} intentos: {e}")
                return []
            else:
                # Backoff exponencial con jitter
                wait_time = base_wait_time * (2 ** attempt) + (attempt * 0.1)
                logger.warning(f"Error de red en intento {attempt + 1}, reintentando en {wait_time:.1f}s: {e}")
                time.sleep(wait_time)
                
        except ValueError as e:
            if "Query is too long" in str(e):
                logger.error(f"Consulta demasiado larga: {e}")
                return []
            else:
                logger.error(f"Error de valor en búsqueda: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error inesperado en búsqueda web (intento {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                logger.error("Se agotaron todos los reintentos")
                return []
            else:
                wait_time = base_wait_time * (attempt + 1)
                logger.warning(f"Reintentando en {wait_time}s...")
                time.sleep(wait_time)