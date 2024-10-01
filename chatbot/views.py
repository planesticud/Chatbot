# ./chatbot/views.py

import json
import os

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from chatbot.RAG.handlers.factory import get_qa_handler

# Load the configuration file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'RAG/config/config.json')

with open(CONFIG_PATH, 'r') as config_file:
    config = json.load(config_file)

# Determine the bot type based on the configuration
BOT_TYPE = config.get('bot_type', 'cohere')  # Default value: "cohere"
BOT_CONFIG = config.get('bot_config', {}).get(BOT_TYPE, {})

# Inicializar el handler correcto basado en el tipo de bot y sus configuraciones
qa_handler = get_qa_handler(BOT_TYPE, BOT_CONFIG)
print(f'INFO: Ejecución tipo {BOT_TYPE}')

def index(request):
    """
    Renders the main page of the application.

    :param request: HTTP request object.
    :return: HTTP response rendering 'index.html'.
    """
    return render(request, 'index.html')

@csrf_exempt
def send_message(request):
    """
    Handles a POST request to send a message to the chatbot and receive a response.

    :param request: HTTP request containing the user's message in JSON format.
    :return: JSON response with the chatbot's answer or an error if the method is not allowed.
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message')
        response = qa_handler.get_answer(user_message)
        return JsonResponse({'response': response})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)