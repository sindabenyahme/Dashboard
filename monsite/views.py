
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

def dash(request):
    files = File.objects.all()  
    excel_data = []
    graph_html = ''  # Définir une valeur par défaut pour éviter l'erreur UnboundLocalError

    for file in files:
        # Load Excel data into a pandas DataFrame, skipping the first row
        df = pd.read_excel(file.file, skiprows=1)
        excel_data.append(df)
        # Assuming each Excel file contains only one sheet
        file.file = str(file.file).split('/')[-1] if '/' in str(file.file) else str(file.file).split('\\')[-1]
        print(file.file)
        
    # Concatenate all dataframes into one
    if excel_data:
        combined_df = pd.concat(excel_data, ignore_index=True)
        # Calculate the number of calls for each point of call
        calls_per_point_of_call = combined_df['Point d\'appel'].value_counts()

        plt.figure(figsize=(12, 6))  # Ajuster la taille de la figure
        calls_per_point_of_call.plot(kind='bar', color='skyblue', fontsize=12)  # Ajuster la taille de la police
        plt.title('Nombre d\'appels par point d\'appel', fontsize=16)  # Ajuster la taille du titre
        plt.xlabel('Point d\'appel', fontsize=14)  # Ajuster la taille de l'étiquette x
        plt.ylabel('Nombre d\'appels', fontsize=14)  # Ajuster la taille de l'étiquette y
        plt.xticks(rotation=45, fontsize=12)  # Ajuster la taille de l'étiquette x et la rotation
        plt.yticks(fontsize=12)  # Ajuster la taille de l'étiquette y
        plt.tight_layout()

        # Convert the plot to an image
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()

        # Convert image to base64 format
        graph = base64.b64encode(image_png).decode()

        # Embed the image in HTML
        graph_html = f'<img src="data:image/png;base64,{graph}" style="width:100%">'

        # Convert the combined dataframe to a list of dictionaries
        table_data = combined_df.to_dict(orient='records')
    else:
        table_data = []
        
    # Create a graph for calls per day and night
    def is_night(hour):
        return hour < 6 or hour >= 20

    combined_df['Date'] = pd.to_datetime(combined_df['Date'], format='mixed', errors='coerce')

    combined_df['Period'] = combined_df['Date'].apply(lambda x: 'Nuit' if is_night(x.hour) else 'Jour')
    calls_per_period = combined_df.groupby('Period').size()

    plt.figure(figsize=(8, 6))
    calls_per_period.plot(kind='bar', color=['skyblue', 'salmon'], alpha=0.7)
    plt.title('Nombre d\'appels par période')
    plt.xlabel('Période')
    plt.ylabel('Nombre d\'appels')
    plt.xticks(rotation=0)
    plt.tight_layout()
    
    # Save the plot as image
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    # Convert image to base64 format
    graph_calls_period = base64.b64encode(image_png).decode()

    # Embed the image in HTML
    graph_calls_period_html = f'<img src="data:image/png;base64,{graph_calls_period}" style="width:100%">'

    return render(request, 'stats.html', {'files': files, 'table_data': table_data, 'graph_html': graph_html, 'graph_calls_period_html': graph_calls_period_html})



def logout(request):
    auth_logout(request)
    return redirect('login')
