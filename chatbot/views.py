from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views import View
from chatbot.RAG.QAHandler import QAHandler
from django.views.decorators.csrf import csrf_exempt
import json

qa_handler = QAHandler()

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message')
        return JsonResponse({'response': qa_handler.get_answer(user_message)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)