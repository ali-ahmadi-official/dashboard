from django.urls import path
from .views import login_or_signup, all_chats, chat, chat_api

urlpatterns = [
    path("", login_or_signup, name="login"),
    path('chat-bot/', all_chats, name='all_chats'),
    path('chat-bot/<int:pk>/', chat, name='chat'),
    path('chat-api/', chat_api, name='chat_api'),
]