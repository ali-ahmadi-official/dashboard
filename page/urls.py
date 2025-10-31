from django.urls import path
from .views import main, chat

urlpatterns = [
    path('', main, name='main'),
    path('chat/', chat, name='chat'),
]