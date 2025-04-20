# reports/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_list, name='report_list'),# Root URL for reports
    path('add/', views.add_report, name='add_report'),
    path('confirmation/<str:report_id>/', views.report_confirmation, name='report_confirmation'), #Ibrahim BSPM25T29-3
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register_view, name='register'),
    path('map/', views.map_view, name='map_view'),

]
