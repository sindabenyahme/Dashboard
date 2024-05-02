from django.shortcuts import render, redirect
from .models import File
from django.http import HttpResponse 
from .forms import FileForm

def upload_file(request):
    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = FileForm()
    return render(request, 'upload.html', {'form': form})

def success(request):
    return HttpResponse('Le fichier Excel a été téléchargé avec succès !')
