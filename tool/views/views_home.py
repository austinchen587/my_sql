from django.shortcuts import render
from django.views import View

def home(request):
    return render(request, 'tool/home.html')