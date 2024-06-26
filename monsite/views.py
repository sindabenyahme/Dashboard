
from django.shortcuts import render, redirect
from .forms import FileForm
from .models import File
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.contrib.auth import logout as auth_logout
import re
import seaborn as sns
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

def logout(request):
    auth_logout(request)
    return redirect('login')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('upload')  # Redirect logged-in users to the upload page
    else:
        return render(request, 'login.html')
    


@login_required
def upload_file(request):
    files = File.objects.all()
    for file in files:
        file.file = str(file.file).split('/')[-1] if '/' in str(file.file) else str(file.file).split('\\')[-1]
    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('upload')
    else:

        return render(request, 'upload.html', { 'files': files })
    
def delete_file(request, file_id):
    # Assuming YourFileModel is your model name
    file_to_delete = File.objects.get(pk=file_id)
    file_to_delete.delete()
    return redirect('upload')
    
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



import pandas as pd
import plotly.graph_objs as go

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
        title=dict(
            text="Durée des appels en fonction du temps",
            x=0.5  # Set the title's x position to the middle
        ),
        xaxis=dict(
            title='Temps',
            tickformat='%H:%M'  # Show only hours and minutes
        ),
        yaxis=dict(title='Durée')
    )

    # Create figure
    fig = go.Figure(data=[scatter_plot], layout=layout)

    # Convert the figure to HTML
    graph_html = fig.to_html(full_html=False)

    return graph_html






import plotly.graph_objs as go

def plot_calls_per_day_and_time(df):
    # Group the data by day and time category and count the number of calls
    calls_per_day_time = df.groupby(['Day', 'Time_Category']).size().unstack(fill_value=0)

    # Calculate total calls for Jour, Nuit, and overall
    total_jour = calls_per_day_time['Jour'].sum()
    total_nuit = calls_per_day_time['Nuit'].sum()
    total_calls = total_jour + total_nuit

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
        yaxis=dict(title='Nombre des appels'),
        title_x=0.5,  # Positionne le titre au centre du graphe
        annotations=[
            dict(
                xref='paper', yref='paper',
                x=0.25, y=1.08,
                xanchor='right', yanchor='top',
                text=f'Total Appels Jour: <b>{total_jour}</b>',
                showarrow=False,
                font=dict(size=12, color='black')
            ),
            dict(
                xref='paper', yref='paper',
                x=0.5, y=1.08,
                xanchor='center', yanchor='top',
                text=f'Total Appels Nuit: <b>{total_nuit}</b>',
                showarrow=False,
                font=dict(size=12)
            ),
            dict(
                xref='paper', yref='paper',
                x=0.95, y=1.08,
                xanchor='left', yanchor='top',
                text=f'Total Général: <b>{total_calls}</b>',
                showarrow=False,
                font=dict(size=12)
            )
        ]
    )

    # Create figure
    fig = go.Figure(data=[trace_jour, trace_nuit], layout=layout)

    # Update layout for legend and graph title
    fig.update_layout(
        legend=dict(orientation='v', yanchor='bottom', y=0.3, xanchor='center', x=1.2),
        title_font=dict(size=20, family='Arial')
    )

    # Convert the figure to an image and encode it to base64
    graph_html = fig.to_html(full_html=False)

    return graph_html










def plot_calls_duration_ranges(df):
    # Assuming df has 'Durée' column

    # Convert Durée to timedelta format
    df['Durée'] = pd.to_timedelta(df['Durée'])

    # Calculate the total duration in seconds
    df['Duration_seconds'] = df['Durée'].dt.total_seconds()

    # Categorize Durée into different bins representing duration ranges
    bins = [0, 300, 600, 3600, float('inf')]  # Duration ranges: <5m, 5-10m, 10m-1h, >=1h
    labels = ['<5m', '5-10m', '10m-1h', '>=1h']
    df['Duration_Range'] = pd.cut(df['Duration_seconds'], bins=bins, labels=labels, right=False)

    # Count the number of calls in each duration range
    duration_counts = df['Duration_Range'].value_counts().sort_index()

    # Create a bar plot with custom colors
    bar_plot = go.Bar(
        x=duration_counts.index,
        y=duration_counts.values,
        marker=dict(color=['#6495ED', '#4682B4','#87CEEB', '#00BFFF', '#B0C4DE',])
    )

    # Create layout with centered title
    layout = go.Layout(
        title=dict(
            text='Nombre des appels par la durée',
            font=dict(
                family='Arial',
                size=20,
                
            )
        ),
        xaxis=dict(title="Durée d'appel"),
        yaxis=dict(title='Nombre des appels'),
        title_x=0.5
    )

    # Create figure
    fig = go.Figure(data=[bar_plot], layout=layout)

    # Convert the figure to HTML
    graph_html = fig.to_html(full_html=False)

    return graph_html






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
        'size': 20,
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

    return tableau_dynamique





def plot_calls_per_sex(df):
    # Assuming df has 'Sex' column

    # Count the number of calls per sex
    sex_counts = df['Sex'].value_counts()

    # Create a bar plot
    bar_plot = go.Bar(
        x=sex_counts.index,
        y=sex_counts.values,
        marker=dict(color=['#FFC0CB', 'lightblue'])
    )

    # Create layout with modified title style
    layout = go.Layout(
        title=dict(
            text='Nombre des appels par sexe',
            font=dict(
                family='Arial',
                size=20,
                
            )
        ),
        xaxis=dict(title='Sexe'),
        yaxis=dict(title='Nombre des appels'),
        title_x=0.5
    )

    # Create figure
    fig = go.Figure(data=[bar_plot], layout=layout)

    # Convert the figure to HTML
    graph_html = fig.to_html(full_html=False)

    return graph_html







def dash(request):
    files = File.objects.all()  
    excel_data = []
    graph_html = ''
    graph_html3 = ''
    graph_calls_period_html = ''
    tableau_dynamique = None

    file_name = request.GET.get('file')  
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    print(start_date)
    print(end_date)

    if file_name:  # Check if file_name is not empty
        df1 = pd.read_excel("media/files/" + str(file_name), skiprows=1)
        excel_data.append(df1)

        for file in files:
            file.file = str(file.file).split('/')[-1] if '/' in str(file.file) else str(file.file).split('\\')[-1]

        combined_df = pd.concat(excel_data, ignore_index=True)
        combined_df['Day'] = combined_df['Date'].apply(lambda x: re.search(r'(\d+\s\w+)', x).group(0))
        combined_df['Time'] = combined_df['Date'].apply(lambda x: re.search(r'à\s(\d+:\d+)', x).group(1))
        combined_df['Sex'] = combined_df['Point d\'appel'].apply(extract_sex)
        combined_df['Time_Category'] = combined_df['Time'].apply(categorize_time)
        combined_df['Date'] = pd.to_datetime(combined_df['Date'], format='mixed', errors='coerce')

        calls_per_point_of_call = combined_df['Motif'].value_counts()
        graph_html3 = graphe3(calls_per_point_of_call)

        tableau_dynamique = creer_tableau_dynamique(combined_df)

        graph_html = plot_calls_per_day_and_time(combined_df)
        graph2_html = plot_time_vs_duration_scatter(combined_df)
        graph_html5 = plot_calls_duration_ranges(combined_df)
        graph_html6 = plot_calls_per_sex(combined_df)
        

        return render(request, 'stats.html', {
            'start_date': start_date,
            'end_date': end_date,
            'files': files,
            'table_data': '', 
            'graph_html': graph_html,
            'graph2_html': graph2_html,
            'graph_calls_period_html': graph_calls_period_html,
            'graph_html3': graph_html3,
            'tableau_dynamique': tableau_dynamique,
            'graph_html5': graph_html5,
            'graph_html6': graph_html6,
            
        })
    else:
        return render(request, 'stats.html', {
            'files': files,
            'table_data': [],
            'graph_html': '', 
            'graph_calls_period_html': '',
            'tableau_dynamique': '',
            
        })



from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def download_view(request):
    if request.method == 'POST':
        try:
            content = request.POST.get('content', '')
            response = HttpResponse(content, content_type='text/html')
            response['Content-Disposition'] = 'attachment; filename="div_content.html"'
            return response
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
