
from django.shortcuts import render, redirect
from .forms import FileForm
from .models import File
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth.decorators import login_required
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.contrib.auth import logout as auth_logout


#Authentication

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

def logout(request):
    auth_logout(request)
    return redirect('login')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('upload')  # Redirect logged-in users to the upload page
    else:
        return render(request, 'login.html')

import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def graphe1(data):
    # Extract date without the time part
    data['Date'] = data['Date'].str.split(' à ').str[0].str.strip()

    # Count calls per day
    calls_per_day = data['Date'].value_counts().sort_index()

    # Plotting
    plt.figure(figsize=(10, 6))
    calls_per_day.plot(kind='bar', color='skyblue', alpha=0.7)
    plt.title('Nombre d\'appels par jour')
    plt.xlabel('Jour')
    plt.ylabel('Nombre d\'appels')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Saving plot to HTML
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

#Statistique

def dash(request):
    files = File.objects.all()  
    excel_data = []
    graph_html = ''
    graph_calls_period_html = ''

    file_name = request.GET.get('file')  

    if file_name:  # Check if file_name is not empty
        df1 = pd.read_excel("media/files/"+str(file_name), skiprows=1)
        excel_data.append(df1)

        for file in files:
            file.file = str(file.file).split('/')[-1] if '/' in str(file.file) else str(file.file).split('\\')[-1]
            print(file.file)

        if excel_data:
            combined_df = pd.concat(excel_data, ignore_index=True)
            calls_per_point_of_call = combined_df['Point d\'appel'].value_counts()

            graph_html = graphe1(combined_df)

            table_data = combined_df.to_dict(orient='records')
        else:
            table_data = []

        combined_df['Date'] = pd.to_datetime(combined_df['Date'], format='mixed', errors='coerce')
        combined_df['Period'] = combined_df['Date'].apply(lambda x: 'Nuit' if is_night(x.hour) else 'Jour')
        calls_per_period = combined_df.groupby('Period').size()

        graph_calls_period_html = graphe2(calls_per_period)

        return render(request, 'stats.html', {'files': files, 'table_data': table_data, 'graph_html': graph_html, 'graph_calls_period_html': graph_calls_period_html})
    else:
        return render(request, 'stats.html', {'files': files, 'table_data': [], 'graph_html': '', 'graph_calls_period_html': ''})





