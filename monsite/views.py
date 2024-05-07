
from django.shortcuts import render, redirect
from .forms import FileForm
from .models import File
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


@api_view(['POST'])
@permission_classes([AllowAny])
def log(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user:
        # Check if a token already exists for the user
        token, created = Token.objects.get_or_create(user=user)
        login(request, user)
        return redirect('upload')
    else:
        return Response({'error': 'Invalid credentials'}, status=400)

@login_required
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

@login_required
def success(request):
    return HttpResponse('Le fichier Excel a été téléchargé avec succès !')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('upload')  # Redirect logged-in users to the upload page
    else:
        return render(request, 'login.html')


from django.shortcuts import render
from .models import File


@login_required
def dash(request):
    files = File.objects.all()  
    for file in files:
        file.file = str(file.file).split('/')[-1] if '/' in str(file.file) else str(file.file).split('\\')[-1]
        print(file.file)


    return render(request, 'stats.html', {'files': files})