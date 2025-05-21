# BS-PM-2025-TEAM29/user/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
