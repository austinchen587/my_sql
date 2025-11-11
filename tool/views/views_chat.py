from django.shortcuts import render
from django.views import View

def chat(request):
    return render(request, 'tool/chat.html')