from django.shortcuts import render

def main(request):
    return render(request, 'page/main.html')

def chat(request):
    return render(request, 'page/chat.html')