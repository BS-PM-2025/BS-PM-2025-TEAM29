from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('reports.urls')),      # All report-related views
    path('user/', include('user.urls')),    # Firebase login/register/logout
]
#path('admin-backend/', include('admin_backend.urls')),  # Optional: if admin backend has separate routes