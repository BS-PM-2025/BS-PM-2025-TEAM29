# reports/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('add_report/', views.add_report, name='add_report'),  # URL for the add_report view
]