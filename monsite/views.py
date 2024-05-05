
from django.shortcuts import render, redirect
from .forms import FileForm

def upload_file(request):
    files = File.objects.all()  
    for file in files:
        file.file = str(file.file).split('/')[-1] if '/' in str(file.file) else str(file.file).split('\\')[-1]
        print(file.file)
    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = FileForm()
    return render(request, 'upload.html', {'form': form,'files': files })

def success(request):
    return HttpResponse('Le fichier Excel a été téléchargé avec succès !')


