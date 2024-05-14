
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
import re
import seaborn as sns
import plotly.graph_objs as go


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
    
    #Data preprossecing

def extract_sex(point):
    if 'Mle' in point or 'Mme' in point:
        return 'F'
    elif 'Mr' in point:
        return 'M'
    else:
        return None


def categorize_time(time):
    hour = int(time.split(':')[0])
    if 7 <= hour < 20:
        return 'Jour'
    else:
        return 'Nuit'

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

def plot_time_vs_duration_scatter(df):
    df['Time'] = pd.to_datetime(df['Time'])

    # Sort the DataFrame by the 'Durée' column in ascending order
    df_sorted = df.sort_values(by='Durée')

    # Create a scatter plot
    scatter_plot = go.Scatter(
        x=df_sorted['Time'],
        y=df_sorted['Durée'],
        mode='markers',
        marker=dict(color='blue', opacity=0.7)  # Set marker color and opacity
    )

    # Create layout
    layout = go.Layout(
        title="Durée d'appel en fonction du temps",
        xaxis=dict(title='Temps'),
        yaxis=dict(title='Durée')
    )

    # Create figure
    fig = go.Figure(data=[scatter_plot], layout=layout)

    # Convert the figure to HTML
    graph_html = fig.to_html(full_html=False)

    return graph_html

def plot_calls_per_day_and_time(df):
    # Group the data by day and time category and count the number of calls
    calls_per_day_time = df.groupby(['Day', 'Time_Category']).size().unstack(fill_value=0)

    # Create traces for Jour and Nuit
    trace_jour = go.Bar(
        x=calls_per_day_time.index,
        y=calls_per_day_time['Jour'],
        name='Jour',
        hoverinfo='text',
        text=[f'Jour<br>{jour}' for jour in calls_per_day_time['Jour']],
        marker=dict(color='#B0E0E6')
    )
    trace_nuit = go.Bar(
        x=calls_per_day_time.index,
        y=calls_per_day_time['Nuit'],
        name='Nuit',
        hoverinfo='text',
        text=[f'Nuit<br>{nuit}' for nuit in calls_per_day_time['Nuit']],
        marker=dict(color='#6495ED')
    )

    # Create layout
    layout = go.Layout(
        title='Nombre des appels par Jour et Nuit',
        xaxis=dict(title='Jour'),
        yaxis=dict(title='Nombre des appels')
    )

    # Create figure
    fig = go.Figure(data=[trace_jour, trace_nuit], layout=layout)

    # Convert the figure to an image and encode it to base64
    graph_html = fig.to_html(full_html=False)

    return graph_html

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

       
        combined_df = pd.concat(excel_data, ignore_index=True)
        combined_df['Day'] = combined_df['Date'].apply(lambda x: re.search(r'(\d+\s\w+)', x).group(0))
        combined_df['Time'] = combined_df['Date'].apply(lambda x: re.search(r'à\s(\d+:\d+)', x).group(1))
        combined_df['Sex'] = combined_df['Point d\'appel'].apply(extract_sex)
        combined_df['Time_Category'] = combined_df['Time'].apply(categorize_time)

        graph_html = plot_calls_per_day_and_time(combined_df)
        graph2_html=plot_time_vs_duration_scatter(combined_df)
        
        #graph_calls_period_html = graphe2(excel_data)

        return render(request, 'stats.html', {'files': files,'table_data': '', 'graph_html': graph_html, 'graph2_html': graph2_html})
    else:
        return render(request, 'stats.html', {'files': files, 'table_data': [], 'graph_html': '', 'graph_calls_period_html': ''})





