from django.shortcuts import render

def index(request):
    return render(request,'index.html')

def cover(request):
    return render(request,'cover.html')
