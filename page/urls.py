from django.urls import path
from .views import main, chat, chat_api

urlpatterns = [
    path('', main, name='main'),
    path('chat/', chat, name='chat'),
    path('chat-api/', chat_api, name='chat_api'),
]