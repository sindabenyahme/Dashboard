from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import login_view, upload_file, log,dash,logout,delete_file,download_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('upload/', upload_file, name='upload'),
    path('delete_url/<int:file_id>/', delete_file, name='delete_file'),
    path('api/log/', log, name='log'),
    path('logout/', logout, name='logout'),
    path ('dashboard/',dash,name='dash'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)