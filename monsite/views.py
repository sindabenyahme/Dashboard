
from django.shortcuts import render, redirect
from .forms import FileForm
from .models import File
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth.decorators import login_required

from django.contrib.auth import logout as auth_logout

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
        return redirect('login')

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
            return redirect('dash')
    else:

        return render(request, 'upload.html', { 'files': files })





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



import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def ghraphe1(data):
    plt.figure(figsize=(12, 6))
    data.plot(kind='bar', color='skyblue', fontsize=12)
    plt.title('Nombre d\'appels par point d\'appel', fontsize=16)
    plt.xlabel('Point d\'appel', fontsize=14)
    plt.ylabel('Nombre d\'appels', fontsize=14)
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graph = base64.b64encode(image_png).decode()
    graph_html = f'<img src="data:image/png;base64,{graph}" style="width:100%">'

    return graph_html

def graphe2(data):
    plt.figure(figsize=(8, 6))
    data.plot(kind='bar', color=['skyblue', 'salmon'], alpha=0.7)
    plt.title('Nombre d\'appels par période')
    plt.xlabel('Période')
    plt.ylabel('Nombre d\'appels')
    plt.xticks(rotation=0)
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graph = base64.b64encode(image_png).decode()
    graph_html = f'<img src="data:image/png;base64,{graph}" style="width:100%">'

    return graph_html

def is_night(hour):
        return hour < 6 or hour >= 20

def dash(request):
    files = File.objects.all()  
    excel_data = []
    graph_html = ''
    graph_calls_period_html = ''

    for file in files:
        df = pd.read_excel(file.file, skiprows=1)
        excel_data.append(df)
        file.file = str(file.file).split('/')[-1] if '/' in str(file.file) else str(file.file).split('\\')[-1]
        print(file.file)
        
    if excel_data:
        combined_df = pd.concat(excel_data, ignore_index=True)
        calls_per_point_of_call = combined_df['Point d\'appel'].value_counts()

        graph_html = ghraphe1(calls_per_point_of_call)

        table_data = combined_df.to_dict(orient='records')
    else:
        table_data = []

    combined_df['Date'] = pd.to_datetime(combined_df['Date'], format='mixed', errors='coerce')
    combined_df['Period'] = combined_df['Date'].apply(lambda x: 'Nuit' if is_night(x.hour) else 'Jour')
    calls_per_period = combined_df.groupby('Period').size()

    graph_calls_period_html = graphe2(calls_per_period)

    return render(request, 'stats.html', {'files': files, 'table_data': table_data, 'graph_html': graph_html, 'graph_calls_period_html': graph_calls_period_html})



def logout(request):
    auth_logout(request)
    return redirect('login')
