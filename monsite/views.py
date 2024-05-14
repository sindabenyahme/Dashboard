
from django.shortcuts import render, redirect
from .forms import FileForm
from .models import File
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth.decorators import login_required
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.contrib.auth import logout as auth_logout
import plotly.graph_objs as go
import plotly.io as pio



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





def graphe3(data):
    colors = ['#87CEEB', '#00BFFF', '#6495ED', '#B0C4DE', '#B0E0E6']

    # Créer une trace de type "pie" avec les couleurs définies
    trace = go.Pie(labels=data.index, values=data.values, marker=dict(colors=colors))

    # Créer une figure avec la trace
    fig = go.Figure(trace)

    fig.update_layout(
        title = {
    'text': 'Pourcentage de chaque motif',
    'font': {
        'size': 24,
        # 'color': '#0000FF',
        'family': 'Arial',
    },
    'x': 0.5,
    'xanchor': 'center',
 },
        legend={'orientation': 'h'}  # Placer la légende en bas (horizontal)
    )

    # Convertir le graphe en format HTML
    graph_html3 = pio.to_html(fig, full_html=False)

    return graph_html3


def creer_tableau_dynamique(df):
    # Supprimer les codes numériques de la colonne 'Point d'appel'
    df_copy = df.copy()
    df_copy['Point d\'appel'] = df_copy['Point d\'appel'].str.replace('\d+', '')

    # Créer un tableau dynamique avec le nombre d'appels par résident
    tableau_dynamique = df_copy['Point d\'appel'].value_counts().reset_index()
    tableau_dynamique.columns = ['Resident', 'NB']
    print(tableau_dynamique[['Resident']])

    return tableau_dynamique

def dash(request):
    files = File.objects.all()  
    excel_data = []
    graph_html = ''
    graph_html3 = ''
    graph_calls_period_html = ''
    tableau_dynamique = None

    file_name = request.GET.get('file')  

    if file_name:  # Check if file_name is not empty
        df1 = pd.read_excel("media/files/" + str(file_name), skiprows=1)
        excel_data.append(df1)

        for file in files:
            file.file = str(file.file).split('/')[-1] if '/' in str(file.file) else str(file.file).split('\\')[-1]

        if excel_data:
            combined_df = pd.concat(excel_data, ignore_index=True)

            graph_html = graphe1(combined_df)
            graph_calls_period_html = graphe2(combined_df)

            calls_per_point_of_call = combined_df['Motif'].value_counts()
            graph_html3 = graphe3(calls_per_point_of_call)

            tableau_dynamique = creer_tableau_dynamique(combined_df)
            print(tableau_dynamique)

        else:
            table_data = []

        combined_df['Date'] = pd.to_datetime(combined_df['Date'], format='mixed', errors='coerce')
        combined_df['Period'] = combined_df['Date'].apply(lambda x: 'Nuit' if is_night(x.hour) else 'Jour')
        calls_per_period = combined_df.groupby('Period').size()
        graph_calls_period_html = graphe2(calls_per_period)

        return render(request, 'stats.html', {'files': files, 'table_data': combined_df.to_dict(orient='records'), 
                                               'graph_html': graph_html, 'graph_calls_period_html': graph_calls_period_html, 
                                               'graph_html3': graph_html3,'tableau_dynamique':tableau_dynamique})

    else:
        return render(request, 'stats.html', {'files': files, 'table_data': [], 'graph_html': '', 
                                               'graph_calls_period_html': '','tableau_dynamique':''})