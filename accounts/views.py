import json
from django.shortcuts import render, redirect
from django.views import View
from django.db.models import Q

def index_en(request):
    return render(request, 'index_en.html')

def index_ru(request):
    return render(request, 'index_ru.html')

def index_uz(request):
    return render(request, 'index_uz.html')
