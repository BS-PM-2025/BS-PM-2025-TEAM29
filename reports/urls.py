# reports/urls.py
from django.urls import path
from . import views

urlpatterns = [
      path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register_view, name='register'),
          path('map/', views.map_view, name='map_view'),

]
