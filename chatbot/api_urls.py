# ./chatbot/api_urls.py

from django.urls import path
from . import api_views

urlpatterns = [
    path('send_message/', api_views.send_message_api, name='api_send_message'),
    path('system_info/', api_views.system_info, name='api_system_info'),
    path('health/', api_views.health_check, name='api_health_check'),
]
