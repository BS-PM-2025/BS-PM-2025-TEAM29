# reports/urls.py
from django.urls import path
from . import views
from admin_backend import views as admin_views

urlpatterns = [
    path('', views.report_list, name='report_list'), #Malik
    path('add/', views.add_report, name='add_report'), #Firas BSPM25T29-16
    path('confirmation/<str:report_id>/', views.report_confirmation, name='report_confirmation'), #Ibrahim BSPM25T29-3
    path('map/', views.map_view, name='map_view'), #Malik
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'), #Abed BSPM25T29-17
    path('worker-dashboard/', views.worker_dashboard, name='worker_dashboard'), #Ibrahim BSPM25T29-151
    path("admin/dashboard/", admin_views.admin_dashboard, name="admin-firebase-reports")
    path('contact/', views.contact_us, name='contact_us'),

]

