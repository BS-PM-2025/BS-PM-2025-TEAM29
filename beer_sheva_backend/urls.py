from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

from beer_sheva_backend.firebase import initialize_firebase
from reports import views

initialize_firebase()


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.report_list, name='report_list'),  # List of reports

    path('reports/', include('reports.urls')),  # Include the reports app's URLs

    path('', lambda request: redirect('add_report')),  # Redirect root URL to 'add_report'
]
